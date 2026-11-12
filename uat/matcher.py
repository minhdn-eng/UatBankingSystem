"""Ghép từng dòng hệ thống trả về với chỉ tiêu tương ứng trong file công thức."""
from __future__ import annotations

from typing import Optional

from uat.models import Indicator, SystemRow
from uat.text_utils import normalize_name

Pair = tuple[Optional[Indicator], Optional[SystemRow]]


def build_name_index(indicators: list[Indicator]) -> dict[str, Indicator]:
    index = {}
    for indicator in indicators:
        for alias in indicator.aliases:
            index.setdefault(normalize_name(alias), indicator)
    return index


def find_indicator(row: SystemRow, index: dict[str, Indicator]) -> Optional[Indicator]:
    return index.get(normalize_name(row.name))


def pair_rows(indicators: list[Indicator], rows: list[SystemRow]) -> list[Pair]:
    """Trả về: các cặp đã khớp, dòng hệ thống lạ (indicator=None),
    chỉ tiêu hệ thống không trả (row=None)."""
    index = build_name_index(indicators)
    pairs, matched_codes = [], set()
    for row in rows:
        indicator = find_indicator(row, index)
        if indicator is not None:
            matched_codes.add(indicator.code)
        pairs.append((indicator, row))
    pairs += [(ind, None) for ind in indicators if ind.code not in matched_codes]
    return pairs


def match_ratio(pairs: list[Pair]) -> float:
    """Tỷ lệ dòng hệ thống tìm được công thức. Thấp -> nghi sai đối tượng/ngành."""
    system_rows = [p for p in pairs if p[1] is not None]
    if not system_rows:
        return 0.0
    return sum(1 for ind, _ in system_rows if ind is not None) / len(system_rows)
