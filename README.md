# UAT - Cảnh báo sớm (chỉ số phái sinh)

So sánh kết quả hệ thống với kết quả Python tự tính từ BCTC + file công thức,
xuất Excel có cột TRUE/FALSE.

## Cấu trúc

```
settings.py            Biến dùng chung: ngành, đường dẫn, quy tắc làm tròn, tên trường JSON
main.py                Điểm chạy: nối các bước lại
uat/
  models.py            Cấu trúc dữ liệu (Indicator, Report, SystemRow, ...)
  loader.py            Đọc file công thức, BCTC, kết quả hệ thống
  text_utils.py        Đọc số "3,260,961" / "8.53%", chuẩn hóa tên chỉ tiêu
  formula.py           Tính 1 công thức trên 1 báo cáo (an toàn, không dùng eval)
  calculator.py        Tính chỉ số 2 kỳ, % biến động, làm tròn
  matcher.py           Ghép dòng hệ thống với chỉ tiêu trong file công thức
  comparator.py        So sánh Python vs hệ thống -> TRUE/FALSE
  sanity_check.py      Kiểm tra nội bộ kết quả hệ thống (không cần BCTC)
  validators.py        Cảnh báo sai đối tượng, khác công ty, năm không liền nhau
  exporter.py          Xuất Excel
tests/test_core.py     Unit test
data/<ngành>/          congthuc.json, bctc_2026.json, bctc_2025.json, ket_qua_he_thong.json
output/                File Excel kết quả
```

## Chạy

```
pip install openpyxl
python main.py                      # ngành mặc định trong settings.ACTIVE_INDUSTRY
python main.py --nganh bao_hiem     # đổi ngành
python -m unittest discover tests   # chạy unit test
```

Chỉ định file riêng: `--cong-thuc`, `--bctc-dg`, `--bctc-ss`, `--he-thong`, `--output`.

## Đổi / thêm ngành

1. Tạo thư mục `data/<ten_nganh>/` và đặt 4 file vào (cùng tên như chung_khoan).
2. Thêm một mục vào `INDUSTRIES` trong `settings.py` (copy mục chung_khoan, đổi đường dẫn).
3. Chạy `python main.py --nganh <ten_nganh>`.

## Giả định cần xác nhận (sửa trong settings.py)

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `TOLERANCE` | 0 | Sai số cho phép sau làm tròn |
| `VARIATION_ON_ROUNDED` | False | Biến động tính trên số chưa làm tròn |
| `VARIATION_ABS_DENOMINATOR` | False | Mẫu số biến động có lấy trị tuyệt đối không |
| `CLOSE_FIELD` / `OPEN_FIELD` | value1 / value2 | Cột dùng cho CLOSE() / OPEN() |

## Lưu ý bảo mật

Dữ liệu thật của khách hàng chỉ chạy trên máy/môi trường công ty cho phép.
