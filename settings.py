"""
CẤU HÌNH DÙNG CHUNG CHO TOÀN BỘ SCRIPT UAT.
Đổi ngành (chứng khoán -> bảo hiểm): sửa ACTIVE_INDUSTRY, hoặc chạy python main.py --nganh bao_hiem
Thêm ngành mới: thêm một mục vào INDUSTRIES.
"""

from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. ĐƯỜNG DẪN & NGÀNH
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

ACTIVE_INDUSTRY = "chung_khoan"

# Sau em them ma nganh nao moi thi them vao day 
INDUSTRIES = {
    "chung_khoan": {
        "label": "Công ty chứng khoán",
        "formula_file": DATA_DIR / "chung_khoan" / "congthuc.json",
        "evaluation_report": DATA_DIR / "chung_khoan" / "bctc_2026.json",
        "comparison_report": DATA_DIR / "chung_khoan" / "bctc_2025.json",
        "system_result": DATA_DIR / "chung_khoan" / "ket_qua_he_thong.json",
    },
    "bao_hiem": {
        "label": "Công ty bảo hiểm",
        "formula_file": DATA_DIR / "bao_hiem" / "congthuc.json",
        "evaluation_report": DATA_DIR / "bao_hiem" / "bctc_2026.json",
        "comparison_report": DATA_DIR / "bao_hiem" / "bctc_2025.json",
        "system_result": DATA_DIR / "bao_hiem" / "ket_qua_he_thong.json",
    },
}

# ---------------------------------------------------------------------------
# 2. QUY TẮC TÍNH TOÁN & SO SÁNH (giả định nghiệp vụ, cần xác nhận)
# ---------------------------------------------------------------------------
DECIMAL_PRECISION = 34
ROUNDING_MODE = ROUND_HALF_UP           # làm tròn kiểu thông thường: 0.125 -> 0.13
TOLERANCE = Decimal("0")                # sai số cho phép sau làm tròn
VARIATION_ON_ROUNDED = False            # False: tính biến động trên số chưa làm tròn
VARIATION_ABS_DENOMINATOR = False       # True: (A - B) / |B|
CLOSE_FIELD = "value1"                  # CLOSE(x) = số cuối kỳ
OPEN_FIELD = "value2"                   # OPEN(x)  = số đầu kỳ
MIN_MATCH_RATIO = 0.5                   # dưới ngưỡng này -> cảnh báo sai đối tượng

# ---------------------------------------------------------------------------
# 3. TÊN TRƯỜNG JSON (sửa tại đây nếu API đổi tên)
# ---------------------------------------------------------------------------
SOURCE_EVALUATION = "evaluation"
SOURCE_COMPARISON = "comparison"

REPORT_ITEM_CODE_KEY = "itemCode"
REPORT_VALUE_KEY_PATTERN = r"value\d+"
REPORT_META_KEYS = {                    # nhãn hiển thị -> các tên trường có thể gặp
    "Công ty": ("companyName", "customerName"),
    "Năm": ("year", "reportYear"),
    "Mã báo cáo": ("reportId", "id"),
}

SYSTEM_ROWS_PATH = ("data", "rows")
SYSTEM_STT_KEY = "stt"
SYSTEM_NAME_KEY = "indicatorName"
SYSTEM_EVALUATION_KEY = "evaluationValue"
SYSTEM_COMPARISON_KEY = "comparisonValue"
SYSTEM_VARIATION_KEY = "variationRate"
EMPTY_MARKERS = {"", "-", "--", "N/A", "NA", "null", "None"}

# ---------------------------------------------------------------------------
# 4. NHÃN HIỂN THỊ
# ---------------------------------------------------------------------------
PERIOD_LABELS = {SOURCE_EVALUATION: "Kỳ đánh giá", SOURCE_COMPARISON: "Kỳ so sánh"}
EXCEL_FONT = "Arial"
