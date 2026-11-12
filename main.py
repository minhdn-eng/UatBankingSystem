"""
UAT - Chức năng Cảnh báo sớm.

Chạy mặc định (ngành trong settings.ACTIVE_INDUSTRY):
    python main.py
Đổi ngành:
    python main.py --nganh bao_hiem
Chỉ định file riêng (ghi đè settings):
    python main.py --cong-thuc a.json --bctc-dg b.json --bctc-ss c.json --he-thong d.json
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from decimal import getcontext
from pathlib import Path

import settings
from uat.comparator import run_comparison
from uat.exporter import export_excel
from uat.loader import load_indicators, load_report, load_system_rows
from uat.matcher import pair_rows
from uat.sanity_check import SUSPICIOUS, run_sanity_checks
from uat.validators import check_reports, check_target_match


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="UAT Cảnh báo sớm - so sánh chỉ số phái sinh")
    parser.add_argument("--nganh", default=settings.ACTIVE_INDUSTRY, choices=settings.INDUSTRIES)
    parser.add_argument("--cong-thuc", help="File công thức (ghi đè settings)")
    parser.add_argument("--bctc-dg", help="BCTC kỳ đánh giá (ghi đè settings)")
    parser.add_argument("--bctc-ss", help="BCTC kỳ so sánh (ghi đè settings)")
    parser.add_argument("--he-thong", help="Kết quả hệ thống (ghi đè settings)")
    parser.add_argument("--output", help="File Excel đầu ra")
    return parser.parse_args()


def resolve_paths(args: argparse.Namespace) -> dict:
    industry = settings.INDUSTRIES[args.nganh]
    paths = {
        "formula_file": args.cong_thuc or industry["formula_file"],
        "evaluation_report": args.bctc_dg or industry["evaluation_report"],
        "comparison_report": args.bctc_ss or industry["comparison_report"],
        "system_result": args.he_thong or industry["system_result"],
    }
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    paths["output"] = args.output or settings.OUTPUT_DIR / f"ket_qua_UAT_{args.nganh}_{stamp}.xlsx"
    return {key: Path(value) for key, value in paths.items()}


def ensure_required_files(paths: dict) -> None:
    missing = [str(paths[k]) for k in ("formula_file", "system_result") if not paths[k].exists()]
    if missing:
        sys.exit("Thiếu file bắt buộc:\n  " + "\n  ".join(missing))


def build_info(industry_key: str, paths: dict, reports: dict) -> list[tuple[str, str]]:
    def describe(report):
        if report is None:
            return "(không có)"
        meta = " | ".join(f"{k}: {v}" for k, v in report.meta.items() if v is not None)
        return f"{Path(report.path).name}  [{meta}]"

    return [
        ("Ngành", settings.INDUSTRIES[industry_key]["label"]),
        ("File công thức", paths["formula_file"].name),
        ("BCTC kỳ đánh giá", describe(reports[settings.SOURCE_EVALUATION])),
        ("BCTC kỳ so sánh", describe(reports[settings.SOURCE_COMPARISON])),
        ("Kết quả hệ thống", paths["system_result"].name),
        ("Thời điểm chạy", datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
    ]


def print_console_summary(results, sanity, warnings, output) -> None:
    passed = sum(r.passed for r in results)
    print(f"\nĐã xuất: {output}")
    print(f"So sánh: {passed}/{len(results)} chỉ tiêu KHỚP")
    for result in results:
        mark = "TRUE " if result.passed else "FALSE"
        code = result.indicator.code if result.indicator else "-"
        name = result.row.name if result.row else result.indicator.name
        print(f"  {mark} {code:4} {name}" + (f"  ({result.note})" if result.note else ""))
    suspicious = [s for s in sanity if s.verdict == SUSPICIOUS]
    print(f"Kiểm tra nội bộ hệ thống: {len(sanity) - len(suspicious)}/{len(sanity)} hợp lý")
    for warning in warnings:
        print(f"⚠  {warning}")


def main() -> None:
    getcontext().prec = settings.DECIMAL_PRECISION
    args = parse_args()
    paths = resolve_paths(args)
    ensure_required_files(paths)

    indicators = load_indicators(paths["formula_file"])
    reports = {settings.SOURCE_EVALUATION: load_report(paths["evaluation_report"]),
               settings.SOURCE_COMPARISON: load_report(paths["comparison_report"])}
    rows = load_system_rows(paths["system_result"])

    pairs = pair_rows(indicators, rows)
    results = run_comparison(pairs, reports)
    sanity = run_sanity_checks(pairs)
    warnings = check_target_match(pairs) + check_reports(*reports.values())

    paths["output"].parent.mkdir(parents=True, exist_ok=True)
    export_excel(paths["output"], results, sanity, build_info(args.nganh, paths, reports), warnings)
    print_console_summary(results, sanity, warnings, paths["output"])


if __name__ == "__main__":
    main()
