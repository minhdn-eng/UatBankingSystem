"""Kiểm tra bộ dữ liệu đầu vào có cùng đối tượng trước khi tin vào kết quả."""
from __future__ import annotations

from typing import Optional

import settings
from uat.matcher import Pair, match_ratio
from uat.models import Report


def check_target_match(pairs: list[Pair]) -> list[str]:
    """Phần lớn dòng hệ thống không có công thức -> nghi kết quả của ngành/công ty khác."""
    ratio = match_ratio(pairs)
    if ratio >= settings.MIN_MATCH_RATIO:
        return []
    return [f"NGHI SAI ĐỐI TƯỢNG: chỉ {ratio:.0%} dòng hệ thống có trong file công thức. "
            f"Kiểm tra lại kết quả hệ thống có đúng công ty/ngành không."]


def check_reports(evaluation: Optional[Report], comparison: Optional[Report]) -> list[str]:
    warnings = []
    if evaluation is None:
        warnings.append("Không có BCTC kỳ đánh giá.")
    if comparison is None:
        warnings.append("Không có BCTC kỳ so sánh: các chỉ tiêu lấy nguồn 'comparison' sẽ FALSE.")
    if evaluation is None or comparison is None:
        return warnings

    company_eval, company_comp = evaluation.meta.get("Công ty"), comparison.meta.get("Công ty")
    if company_eval and company_comp and company_eval != company_comp:
        warnings.append(f"Hai BCTC khác công ty: '{company_eval}' và '{company_comp}'.")

    year_eval, year_comp = evaluation.meta.get("Năm"), comparison.meta.get("Năm")
    if isinstance(year_eval, int) and isinstance(year_comp, int) and year_eval - year_comp != 1:
        warnings.append(f"Năm kỳ đánh giá ({year_eval}) và kỳ so sánh ({year_comp}) không liền nhau.")
    return warnings
