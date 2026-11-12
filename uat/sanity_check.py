"""Kiểm tra nội bộ: % biến động hệ thống có hợp lý với 2 giá trị hệ thống hiển thị?

Không cần BCTC. Vì giá trị hiển thị đã làm tròn (8.53% thực ra là 8.525 -> 8.535),
ta tính khoảng biến động có thể xảy ra và xem số hệ thống có nằm trong đó không.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from uat.calculator import compute_variation, round_value
from uat.matcher import Pair
from uat.models import SanityResult, SystemRow
from uat.text_utils import guess_decimals

REASONABLE = "HỢP LÝ"
SUSPICIOUS = "BẤT THƯỜNG"


def check_row(row: SystemRow, decimals: int, variation_decimals: int) -> SanityResult:
    current, previous, variation = row.evaluation, row.comparison, row.variation
    if current is None or previous is None or variation is None:
        return SanityResult(row, None, None, None, "Thiếu giá trị, bỏ qua")

    half_step = Decimal("0.5").scaleb(-decimals)
    if previous - half_step <= 0 <= previous + half_step:
        return SanityResult(row, None, None, None, "Kỳ so sánh ≈ 0, bỏ qua")

    low, high = _variation_range(current, previous, half_step)
    tolerance = Decimal("0.5").scaleb(-variation_decimals)
    verdict = REASONABLE if low - tolerance <= variation <= high + tolerance else SUSPICIOUS
    recomputed = round_value(compute_variation(current, previous)[0], variation_decimals)
    return SanityResult(row, recomputed, round_value(low, variation_decimals + 2),
                        round_value(high, variation_decimals + 2), verdict)


def _variation_range(current: Decimal, previous: Decimal, half_step: Decimal) -> tuple[Decimal, Decimal]:
    """Biến động đơn điệu theo từng biến nên chỉ cần xét 4 góc."""
    corners = [compute_variation(c, p)[0]
               for c in (current - half_step, current + half_step)
               for p in (previous - half_step, previous + half_step)]
    return min(corners), max(corners)


def run_sanity_checks(pairs: list[Pair]) -> list[SanityResult]:
    results = []
    for indicator, row in pairs:
        if row is None:
            continue
        decimals: Optional[int] = indicator.decimals if indicator else guess_decimals(row.evaluation_text)
        variation_decimals = indicator.variation_decimals if indicator else 2
        results.append(check_row(row, decimals, variation_decimals))
    return results
