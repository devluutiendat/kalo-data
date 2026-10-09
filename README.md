# TikTok Creator Scraper

Công cụ tự động thu thập danh sách Creator và thông tin chi tiết từ **Kalodata OpenAPI**, lọc theo danh mục TikTok Shop.

---

## Tính năng

- 🔍 **Tìm kiếm danh mục** TikTok Shop theo từ khóa (từ file Excel cục bộ)
- 👥 **Thu thập Creator Rank** theo danh mục — tự động phân trang cho đến khi không còn dữ liệu mới
- 📄 **Thu thập Creator Detail** cho từng creator trong danh sách
- 💾 **Dedup thông minh** — chỉ lưu item mới, bỏ qua item đã tồn tại theo `creator_id`
- 🗂️ Lưu kết quả dạng JSON chuẩn hóa

---

## Cấu trúc project

```
tiktok-comment-scraper/
├── main.py                  # Entrypoint chính — chạy toàn bộ pipeline
├── search.py                # Tìm kiếm danh mục TikTok Shop từ file Excel
├── creators.py              # Lấy danh sách Creator theo từng trang
├── creator_detail.py        # Lấy thông tin chi tiết từng Creator
├── kalo.py                  # HTTP client dùng chung cho Kalodata OpenAPI (dedup, lưu file)
├── TikTok Shop Category ... .xlsx  # File Excel danh mục TikTok Shop
├── creators.json            # Output: danh sách Creator thu thập được
└── creator_detail/
    └── <creator_id>.json    # Output: detail từng Creator
```

---

## Yêu cầu

- Python 3.9+
- Tài khoản [Kalodata](https://www.kalodata.com) với `SECRET_KEY`

### Cài đặt thư viện

```bash
pip install requests python-dotenv pandas openpyxl
```

---

## Cấu hình

Tạo file `.env` tại thư mục gốc:

```env
SECRET_KEY=your-kalodata-secret-key-here
```

---

## Cách sử dụng

### Chạy toàn bộ pipeline

```bash
python main.py "từ khóa"
# Ví dụ:
python main.py "váy"
python main.py "gia dụng"
```

Pipeline sẽ thực hiện 3 bước:

```
Bước 1 — Tìm kiếm danh mục
  └─ In danh sách category TikTok Shop khớp với từ khóa

Bước 2 — Thu thập Creator Rank (phân trang tự động)
  └─ Gọi API liên tục trang 1, 2, 3... cho đến khi không có item mới
  └─ Lưu tất cả vào creators.json (dedup theo creator_id)

Bước 3 — Thu thập Creator Detail
  └─ Đọc creators.json, gọi API detail cho từng creator
  └─ Lưu vào creator_detail/<creator_id>.json
```

### Chạy riêng từng module

```bash
# Chỉ tìm danh mục
python search.py "váy"

# Chỉ lấy danh sách creator (1 trang)
python creators.py

# Chỉ lấy detail 1 creator
python creator_detail.py
```

---

## Output

### `creators.json`
Danh sách creator dạng mảng JSON, mỗi item gồm:
```json
[
  {
    "creator_id": "6811418790367527938",
    "creator_nickname": "Chu Nhung oiii",
    "creator_handle": "@chunhungne",
    "revenue": 699892858.12,
    "sales_volumn": 5266,
    "creator_followers": "161500",
    ...
  }
]
```

### `creator_detail/<creator_id>.json`
Chi tiết từng creator, lưu riêng theo `creator_id`:
```json
[
  {
    "creator_id": "6811418790367527938",
    "creator_handle": "@chunhungne",
    "video_revenue": 692795707.26,
    "video_views": 2579153,
    "shop_number": 115,
    "product_number": 202,
    ...
  }
]
```

---

## Ghi chú

- **Dedup:** Mỗi lần chạy lại, tool chỉ thêm item chưa có — an toàn để chạy nhiều lần.
- **Phân trang:** `page_size` mặc định 100 items/trang. Điều chỉnh trong `creators.py`.
- **Danh mục:** `category_ids` trong `creators.py` cần cập nhật thủ công theo ID từ kết quả tìm kiếm.
