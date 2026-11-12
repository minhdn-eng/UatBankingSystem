"""Đọc dữ liệu đầu vào: file công thức, BCTC, kết quả hệ thống."""
from __future__ import annotations

import json
import re
from decimal import Decimal
from pathlib import Path
from typing import Optional

import settings
from uat.models import Indicator, Report, SystemRow
from uat.text_utils import parse_number


def read_json(path):
    with open(path, encoding="utf-8-sig") as file:
        return json.load(file)


# --------------------------- File công thức --------------------------------
def load_indicators(path) -> list[Indicator]:
    return [_to_indicator(item) for item in read_json(path)]


def _to_indicator(item: dict) -> Indicator:
    aliases = [item.get("name")] + list(item.get("system_names") or []) \
        + list(item.get("indicator_names") or [])
    return Indicator(
        code=item["code"],
        name=item["name"],
        formula=item["formula"],
        multiplier=Decimal(str(item.get("multiplier", "1"))),
        unit=item.get("unit", ""),
        decimals=int(item.get("decimals", 2)),
        variation_decimals=int(item.get("variation_decimals", 2)),
        variation_method=item.get("variation", "relative"),
        evaluation_source=item.get("evaluation_source", settings.SOURCE_EVALUATION),
        evaluation_field=item.get("evaluation_field", "value1"),
        comparison_source=item.get("comparison_source", settings.SOURCE_COMPARISON),
        comparison_field=item.get("comparison_field", "value1"),
        aliases=tuple(a for a in aliases if a),
    )


# --------------------------- File BCTC -------------------------------------
def load_report(path) -> Optional[Report]:
    if path is None or not Path(path).exists():
        return None
    content = read_json(path)
    rows = _find_item_rows(content)
    if rows is None:
        raise ValueError(f"Không tìm thấy danh sách dòng có '{settings.REPORT_ITEM_CODE_KEY}' trong {path}")
    return Report(path=str(path), meta=_extract_meta(content), items=_build_items(rows))


def _find_item_rows(node):
    """Tự dò mảng chứa các dòng BCTC, không phụ thuộc tên key (bctcList, items...)."""
    key = settings.REPORT_ITEM_CODE_KEY
    if isinstance(node, list):
        if node and all(isinstance(x, dict) for x in node) and any(key in x for x in node):
            return node
        children = node
    elif isinstance(node, dict):
        children = node.values()
    else:
        return None
    for child in children:
        found = _find_item_rows(child)
        if found is not None:
            return found
    return None


def _build_items(rows: list[dict]) -> dict:
    items = {}
    for row in rows:
        code = row.get(settings.REPORT_ITEM_CODE_KEY)
        if code:
            items[str(code).strip().upper()] = {
                key: _to_decimal(value) for key, value in row.items()
                if re.fullmatch(settings.REPORT_VALUE_KEY_PATTERN, key)
            }
    return items


def _to_decimal(value) -> Optional[Decimal]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return Decimal(str(value))


def _extract_meta(content) -> dict:
    data = content.get("data", content) if isinstance(content, dict) else {}
    meta = {}
    for label, keys in settings.REPORT_META_KEYS.items():
        meta[label] = next((data[k] for k in keys if isinstance(data, dict) and data.get(k) is not None), None)
    return meta


# --------------------------- Kết quả hệ thống ------------------------------
def load_system_rows(path) -> list[SystemRow]:
    node = read_json(path)
    for key in settings.SYSTEM_ROWS_PATH:
        node = node.get(key, []) if isinstance(node, dict) else []
    return [_to_system_row(row) for row in node]


def _to_system_row(row: dict) -> SystemRow:
    evaluation = row.get(settings.SYSTEM_EVALUATION_KEY)
    comparison = row.get(settings.SYSTEM_COMPARISON_KEY)
    variation = row.get(settings.SYSTEM_VARIATION_KEY)
    return SystemRow(
        stt=row.get(settings.SYSTEM_STT_KEY),
        name=row.get(settings.SYSTEM_NAME_KEY, ""),
        evaluation_text=evaluation,
        comparison_text=comparison,
        variation_text=variation,
        evaluation=parse_number(evaluation),
        comparison=parse_number(comparison),
        variation=parse_number(variation),
    )
