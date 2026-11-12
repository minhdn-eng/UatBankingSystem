"""So sánh giá trị Python tính với giá trị hệ thống trả về."""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

import settings
from uat.calculator import calculate_indicator, round_value
from uat.matcher import Pair
from uat.models import ComparisonResult, Indicator, Report, SystemRow


def values_match(python_value: Optional[Decimal], system_value: Optional[Decimal],
                 decimals: int) -> bool:
    """Làm tròn cả hai theo cùng số lẻ rồi so. Cả hai cùng rỗng -> khớp."""
    if python_value is None and system_value is None:
        return True
    if python_value is None or system_value is None:
        return False
    difference = round_value(python_value, decimals) - round_value(system_value, decimals)
    return abs(difference) <= settings.TOLERANCE


def compare_pair(indicator: Optional[Indicator], row: Optional[SystemRow],
                 reports: dict[str, Optional[Report]]) -> ComparisonResult:
    if indicator is None:
        return ComparisonResult(None, row, None, False, False, False,
                                "Không tìm thấy chỉ tiêu trong file công thức")

    calc = calculate_indicator(indicator, reports)
    if row is None:
        note = "; ".join(x for x in ("Hệ thống không trả chỉ tiêu này", calc.notes) if x)
        return ComparisonResult(indicator, None, calc, False, False, False, note)

    return ComparisonResult(
        indicator=indicator,
        row=row,
        calc=calc,
        match_evaluation=values_match(calc.evaluation.value, row.evaluation, indicator.decimals),
        match_comparison=values_match(calc.comparison.value, row.comparison, indicator.decimals),
        match_variation=values_match(calc.variation, row.variation, indicator.variation_decimals),
        note=calc.notes,
    )


def run_comparison(pairs: list[Pair], reports: dict[str, Optional[Report]]) -> list[ComparisonResult]:
    return [compare_pair(indicator, row, reports) for indicator, row in pairs]
