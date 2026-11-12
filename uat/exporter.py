"""Xuất kết quả ra Excel: Tổng hợp, Kết quả so sánh, Chi tiết tính toán, Kiểm tra nội bộ."""
from __future__ import annotations

from decimal import Decimal

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

import settings
from uat.calculator import round_value
from uat.models import ComparisonResult, PeriodValue, SanityResult
from uat.sanity_check import REASONABLE, SUSPICIOUS

SHEET_SUMMARY = "Tong hop"
SHEET_COMPARE = "Ket qua so sanh"
SHEET_DETAIL = "Chi tiet tinh toan"
SHEET_SANITY = "Kiem tra noi bo HT"

_FONT = Font(name=settings.EXCEL_FONT)
_FONT_BOLD = Font(name=settings.EXCEL_FONT, bold=True)
_FONT_HEADER = Font(name=settings.EXCEL_FONT, bold=True, color="FFFFFF")
_FILL_HEADER = PatternFill("solid", fgColor="1F4E78")
_FILL_GREEN = PatternFill("solid", fgColor="C6EFCE")
_FILL_RED = PatternFill("solid", fgColor="FFC7CE")
_BORDER = Border(*(Side(style="thin", color="BFBFBF"),) * 4)
_CENTER = Alignment(horizontal="center", vertical="center")

COMPARE_HEADERS = [
    ("STT", 5), ("Mã", 7), ("Tên chỉ tiêu (công thức)", 34), ("Tên trên hệ thống", 34), ("Đơn vị", 11),
    ("Kỳ ĐG - Hệ thống", 15), ("Kỳ ĐG - Python", 15), ("Khớp Kỳ ĐG", 10),
    ("Kỳ SS - Hệ thống", 15), ("Kỳ SS - Python", 15), ("Khớp Kỳ SS", 10),
    ("Biến động (%) - Hệ thống", 14), ("Biến động (%) - Python", 14), ("Khớp biến động", 10),
    ("KẾT QUẢ", 10), ("Đầu vào Kỳ ĐG", 38), ("Đầu vào Kỳ SS", 38), ("Ghi chú", 40),
]
DETAIL_HEADERS = [
    ("Mã", 7), ("Tên chỉ tiêu", 34), ("Kỳ", 13), ("Nguồn", 12), ("Cột", 8), ("Công thức", 30),
    ("Công thức đã thay số", 55), ("Giá trị thô", 18), ("Hệ số nhân", 11),
    ("Sau nhân (chưa làm tròn)", 22), ("Sau làm tròn", 16), ("Ghi chú", 30),
]
SANITY_HEADERS = [
    ("STT", 5), ("Tên trên hệ thống", 40), ("Kỳ ĐG - HT", 15), ("Kỳ SS - HT", 15),
    ("Biến động - HT", 15), ("Biến động tính từ số hiển thị", 18),
    ("Khoảng hợp lý - thấp", 16), ("Khoảng hợp lý - cao", 16), ("Đánh giá", 24),
]


def export_excel(path, results: list[ComparisonResult], sanity: list[SanityResult],
                 info: list[tuple[str, str]], warnings: list[str]) -> None:
    workbook = Workbook()
    _write_summary(workbook.active, len(results), info, warnings)
    _write_comparison(workbook.create_sheet(SHEET_COMPARE), results)
    _write_details(workbook.create_sheet(SHEET_DETAIL), results)
    _write_sanity(workbook.create_sheet(SHEET_SANITY), sanity)
    workbook.save(path)


# --------------------------- Các sheet -------------------------------------
def _write_summary(sheet, result_count: int, info, warnings) -> None:
    sheet.title = SHEET_SUMMARY
    sheet["A1"] = "BÁO CÁO UAT - CẢNH BÁO SỚM (CHỈ SỐ PHÁI SINH)"
    sheet["A1"].font = Font(name=settings.EXCEL_FONT, bold=True, size=14)

    last = result_count + 1
    rng = f"'{SHEET_COMPARE}'!O2:O{last}"
    lines = [("THÔNG TIN", None), *info, ("", None),
             ("KẾT QUẢ", None),
             ("Tổng số chỉ tiêu", f"=COUNTA('{SHEET_COMPARE}'!A2:A{last})"),
             ("Số chỉ tiêu KHỚP (TRUE)", f"=COUNTIF({rng},TRUE)"),
             ("Số chỉ tiêu KHÔNG KHỚP (FALSE)", f"=COUNTIF({rng},FALSE)"),
             ("", None), ("CẢNH BÁO", None),
             *[("⚠", w) for w in warnings or ["Không có"]],
             ("", None), ("GIẢ ĐỊNH ĐANG DÙNG (sửa trong settings.py)", None),
             *_assumption_lines()]

    for offset, (label, value) in enumerate(lines, start=3):
        sheet.cell(offset, 1, label).font = _FONT_BOLD if value is None else _FONT
        if value is not None:
            sheet.cell(offset, 2, value).font = _FONT
    sheet.column_dimensions["A"].width = 38
    sheet.column_dimensions["B"].width = 90


def _assumption_lines() -> list[tuple[str, str]]:
    formula = "(ĐG - SS) / |SS| x 100" if settings.VARIATION_ABS_DENOMINATOR else "(ĐG - SS) / SS x 100"
    return [
        ("Làm tròn", f"{settings.ROUNDING_MODE} theo 'decimals' / 'variation_decimals'"),
        ("Sai số cho phép sau làm tròn", str(settings.TOLERANCE)),
        ("Biến động tính trên", "số đã làm tròn" if settings.VARIATION_ON_ROUNDED else "số chưa làm tròn"),
        ("Công thức biến động", formula),
        ("CLOSE(x) / OPEN(x)", f"x.{settings.CLOSE_FIELD} / x.{settings.OPEN_FIELD}"),
    ]


def _write_comparison(sheet, results: list[ComparisonResult]) -> None:
    rows = [_comparison_row(i, r) for i, r in enumerate(results, start=1)]
    _write_table(sheet, COMPARE_HEADERS, rows)

    for excel_row, result in enumerate(results, start=2):
        decimals = result.indicator.decimals if result.indicator else 2
        var_decimals = result.indicator.variation_decimals if result.indicator else 2
        _set_number_format(sheet, excel_row, "FGIJ", decimals)
        _set_number_format(sheet, excel_row, "LM", var_decimals)
        for column in "HKNO":
            sheet[f"{column}{excel_row}"].alignment = _CENTER
        sheet[f"O{excel_row}"].font = _FONT_BOLD

    last = len(results) + 1
    for area in (f"H2:H{last}", f"K2:K{last}", f"N2:O{last}"):
        _add_color_rules(sheet, area, "TRUE", "FALSE")


def _comparison_row(index: int, result: ComparisonResult) -> list:
    ind, row, calc = result.indicator, result.row, result.calc
    decimals = ind.decimals if ind else 2
    var_decimals = ind.variation_decimals if ind else 2
    excel_row = index + 1
    return [
        index, ind.code if ind else "", ind.name if ind else "",
        row.name if row else "(không có trên hệ thống)", ind.unit if ind else "",
        row.evaluation if row else None, round_value(calc.evaluation.value, decimals) if calc else None,
        result.match_evaluation,
        row.comparison if row else None, round_value(calc.comparison.value, decimals) if calc else None,
        result.match_comparison,
        row.variation if row else None, round_value(calc.variation, var_decimals) if calc else None,
        result.match_variation,
        f"=AND(H{excel_row},K{excel_row},N{excel_row})",
        _format_inputs(calc.evaluation if calc else None),
        _format_inputs(calc.comparison if calc else None),
        result.note,
    ]


def _format_inputs(period: PeriodValue | None) -> str:
    """Mỗi số liệu đầu vào một dòng: 'CD400 (value1) = 3,983,151,055,250'."""
    if period is None:
        return ""
    lines = [f"{i.code} ({i.column}) = {i.value:,}" if i.value is not None
             else f"{i.code} ({i.column}) = THIẾU" for i in period.inputs]
    return "\n".join(lines)


def _write_details(sheet, results: list[ComparisonResult]) -> None:
    rows = []
    for result in results:
        if result.calc is None:
            continue
        ind = result.indicator
        for period in (result.calc.evaluation, result.calc.comparison):
            rows.append([ind.code, ind.name, period.period, period.source, period.field, ind.formula,
                         period.filled_formula, period.raw, ind.multiplier, period.value,
                         round_value(period.value, ind.decimals), period.note])
    _write_table(sheet, DETAIL_HEADERS, rows)
    for row in sheet.iter_rows(min_row=2):
        row[7].number_format = row[9].number_format = "#,##0.0000000000"
        row[10].number_format = "#,##0.00"


def _write_sanity(sheet, sanity: list[SanityResult]) -> None:
    rows = [[s.row.stt, s.row.name, s.row.evaluation_text, s.row.comparison_text,
             s.row.variation_text, s.recomputed, s.low, s.high, s.verdict] for s in sanity]
    _write_table(sheet, SANITY_HEADERS, rows)
    _add_color_rules(sheet, f"I2:I{len(rows) + 1}", f'"{REASONABLE}"', f'"{SUSPICIOUS}"')


# --------------------------- Tiện ích định dạng -----------------------------
def _write_table(sheet, headers: list[tuple[str, int]], rows: list[list]) -> None:
    sheet.append([title for title, _ in headers])
    for row in rows:
        sheet.append([float(v) if isinstance(v, Decimal) else v for v in row])

    for cell in sheet[1]:
        cell.font, cell.fill, cell.border = _FONT_HEADER, _FILL_HEADER, _BORDER
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.font, cell.border = _FONT, _BORDER
            cell.alignment = Alignment(vertical="center", wrap_text=isinstance(cell.value, str))

    for column, (_, width) in enumerate(headers, start=1):
        sheet.column_dimensions[get_column_letter(column)].width = width
    sheet.row_dimensions[1].height = 36
    sheet.freeze_panes = "A2"


def _set_number_format(sheet, row: int, columns: str, decimals: int) -> None:
    pattern = "#,##0" if decimals == 0 else "#,##0." + "0" * decimals
    for column in columns:
        sheet[f"{column}{row}"].number_format = pattern


def _add_color_rules(sheet, area: str, good_value: str, bad_value: str) -> None:
    sheet.conditional_formatting.add(area, CellIsRule(operator="equal", formula=[good_value], fill=_FILL_GREEN))
    sheet.conditional_formatting.add(area, CellIsRule(operator="equal", formula=[bad_value], fill=_FILL_RED))
