"""Tính chỉ số phái sinh cho 2 kỳ và % biến động giữa 2 kỳ."""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

import settings
from uat.formula import evaluate_formula
from uat.models import Indicator, IndicatorCalc, PeriodValue, Report


def round_value(value: Optional[Decimal], decimals: int) -> Optional[Decimal]:
    if value is None:
        return None
    return value.quantize(Decimal(1).scaleb(-decimals), rounding=settings.ROUNDING_MODE)


def compute_variation(current: Optional[Decimal], previous: Optional[Decimal],
                      method: str = "relative") -> tuple[Optional[Decimal], str]:
    """relative: (A - B) / B x 100 | absolute: A - B"""
    if current is None or previous is None:
        return None, "Thiếu giá trị để tính biến động"
    if method == "absolute":
        return current - previous, ""
    if previous == 0:
        return None, "Kỳ so sánh = 0, không tính được biến động"
    denominator = abs(previous) if settings.VARIATION_ABS_DENOMINATOR else previous
    return (current - previous) / denominator * 100, ""


def compute_period(indicator: Indicator, reports: dict[str, Optional[Report]],
                   period: str) -> PeriodValue:
    """Tính giá trị chỉ tiêu cho 1 kỳ (evaluation / comparison)."""
    if period == settings.SOURCE_EVALUATION:
        source, field = indicator.evaluation_source, indicator.evaluation_field
    else:
        source, field = indicator.comparison_source, indicator.comparison_field

    result = evaluate_formula(indicator.formula, reports.get(source), field)
    value = result.value * indicator.multiplier if result.value is not None else None
    return PeriodValue(period=settings.PERIOD_LABELS[period], source=source, field=field,
                       filled_formula=result.filled_formula, raw=result.value,
                       value=value, note=result.note, inputs=result.inputs)


def calculate_indicator(indicator: Indicator, reports: dict[str, Optional[Report]]) -> IndicatorCalc:
    evaluation = compute_period(indicator, reports, settings.SOURCE_EVALUATION)
    comparison = compute_period(indicator, reports, settings.SOURCE_COMPARISON)

    current, previous = evaluation.value, comparison.value
    if settings.VARIATION_ON_ROUNDED:
        current = round_value(current, indicator.decimals)
        previous = round_value(previous, indicator.decimals)

    variation, note = compute_variation(current, previous, indicator.variation_method)
    return IndicatorCalc(indicator, evaluation, comparison, variation, note)
