"""Các cấu trúc dữ liệu dùng chung giữa các module."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class Indicator:
    """Một chỉ tiêu trong file công thức."""
    code: str
    name: str
    formula: str
    multiplier: Decimal
    unit: str
    decimals: int
    variation_decimals: int
    variation_method: str
    evaluation_source: str
    evaluation_field: str
    comparison_source: str
    comparison_field: str
    aliases: tuple  # tất cả tên có thể dùng để khớp với hệ thống


@dataclass(frozen=True)
class Report:
    """Một báo cáo tài chính: {mã dòng: {value1: ..., value2: ...}}."""
    path: str
    meta: dict
    items: dict

    def value(self, code: str, field: str) -> Optional[Decimal]:
        return self.items.get(code, {}).get(field)


@dataclass(frozen=True)
class SystemRow:
    """Một dòng kết quả hệ thống trả về (đã đổi chuỗi sang số)."""
    stt: object
    name: str
    evaluation_text: Optional[str]
    comparison_text: Optional[str]
    variation_text: Optional[str]
    evaluation: Optional[Decimal]
    comparison: Optional[Decimal]
    variation: Optional[Decimal]


@dataclass(frozen=True)
class InputValue:
    """Một số liệu đầu vào lấy từ BCTC để tính công thức."""
    code: str
    column: str
    value: Optional[Decimal]    # None = BCTC không có số liệu này


@dataclass(frozen=True)
class PeriodValue:
    """Giá trị chỉ tiêu của một kỳ, kèm vết tính toán."""
    period: str
    source: str
    field: str
    filled_formula: str
    raw: Optional[Decimal]      # trước khi nhân hệ số
    value: Optional[Decimal]    # sau khi nhân hệ số, chưa làm tròn
    note: str = ""
    inputs: tuple = ()          # các InputValue đã dùng


@dataclass(frozen=True)
class IndicatorCalc:
    """Kết quả Python tính cho một chỉ tiêu."""
    indicator: Indicator
    evaluation: PeriodValue
    comparison: PeriodValue
    variation: Optional[Decimal]
    variation_note: str = ""

    @property
    def notes(self) -> str:
        parts = (self.evaluation.note, self.comparison.note, self.variation_note)
        return "; ".join(p for p in parts if p)


@dataclass(frozen=True)
class ComparisonResult:
    """Kết quả đối chiếu Python với hệ thống cho một chỉ tiêu."""
    indicator: Optional[Indicator]
    row: Optional[SystemRow]
    calc: Optional[IndicatorCalc]
    match_evaluation: bool
    match_comparison: bool
    match_variation: bool
    note: str = ""

    @property
    def passed(self) -> bool:
        return self.match_evaluation and self.match_comparison and self.match_variation


@dataclass(frozen=True)
class SanityResult:
    """Kiểm tra biến động hệ thống có khớp với 2 giá trị hệ thống hiển thị."""
    row: SystemRow
    recomputed: Optional[Decimal]
    low: Optional[Decimal]
    high: Optional[Decimal]
    verdict: str
