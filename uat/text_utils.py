"""Xử lý chuỗi: đọc số hệ thống hiển thị, chuẩn hóa tên chỉ tiêu."""
from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation
from typing import Optional

import settings


def parse_number(text) -> Optional[Decimal]:
    """'3,260,961' -> 3260961 | '8.53%' -> 8.53 | '(1.2%)' -> -1.2 | 'N/A' -> None"""
    if text is None or isinstance(text, bool):
        return None
    if isinstance(text, (int, float)):
        return Decimal(str(text))

    cleaned = str(text).strip()
    if cleaned in settings.EMPTY_MARKERS:
        return None

    is_negative = cleaned.startswith("(") and cleaned.endswith(")")
    cleaned = cleaned.strip("()").replace("%", "").replace(",", "").replace(" ", "")
    try:
        number = Decimal(cleaned)
    except InvalidOperation:
        return None
    return -number if is_negative else number


def normalize_name(name) -> str:
    """Chuẩn hóa tên để so khớp: bỏ '(%)', '%' cuối, khoảng trắng thừa, chữ hoa."""
    text = unicodedata.normalize("NFC", str(name or "")).lower().strip()
    text = re.sub(r"\(\s*%\s*\)", "", text)
    text = re.sub(r"%\s*$", "", text)
    text = re.sub(r"\s*/\s*", " / ", text)
    return re.sub(r"\s+", " ", text).strip()


def guess_decimals(text) -> int:
    """Đoán số lẻ khi không có config: số % thường 2 số lẻ, số tiền 0."""
    return 2 if "%" in str(text or "") else 0
