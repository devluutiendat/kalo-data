# TikTok Creator Scraper & Google Sheets Exporter

Công cụ tự động thu thập danh sách Creator và thông tin chi tiết từ **Kalodata OpenAPI**, hỗ trợ lọc theo danh mục TikTok Shop và đồng bộ trực tiếp lên **Google Sheets**.

---

## 🚀 Tính năng nổi bật

- 🔍 **Tìm kiếm danh mục:** Tra cứu mã danh mục TikTok Shop theo từ khóa từ file Excel cục bộ (`search.py`).
- 👥 **Thu thập Creator Rank:** Tự động phân trang (mỗi trang 100 creator), vòng lặp chạy liên tục cho đến khi số lượng data API trả về `< 100` (đã đến trang cuối cùng) (`creators.py`).
- 📄 **Thu thập Creator Detail:** Đọc danh sách từ `creators.json` và tải chi tiết từng creator vào thư mục `creator_detail/<creator_id>.json` (`creator_detail.py`).
- 💾 **Dedup thông minh:** Tự động lọc trùng lặp theo `creator_id`, chỉ bổ sung bản ghi mới mà không ghi đè dữ liệu cũ (`kalo.py`).
- 📊 **Xuất dữ liệu lên Google Sheets:** Đồng bộ các file JSON (creators, creator_detail) lên tab tương ứng trên Google Sheets theo batch 500 hàng, chống vượt hạn mức Google API Quota (`sheet.py`).

---

## 📁 Cấu trúc dự án

```
kalodata/
├── main.py                          # Entrypoint điều phối toàn bộ pipeline
├── search.py                        # Tìm kiếm danh mục TikTok Shop từ file Excel
├── creators.py                      # Lấy danh sách Creator Rank theo phân trang
├── creator_detail.py                # Lấy thông tin chi tiết từng Creator
├── kalo.py                          # Core HTTP client gọi Kalodata OpenAPI (dedup & lưu file)
├── sheet.py                         # Đẩy dữ liệu JSON lên Google Spreadsheet
├── TikTok Shop Category ....xlsx      # File dữ liệu danh mục TikTok Shop
├── creators.json                    # Dữ liệu danh sách Creator đã thu thập
├── creator_detail/                  # Thư mục chứa chi tiết từng Creator
│   └── <creator_id>.json
├── service_account.json             # Google Cloud Service Account key (bảo mật, nằm trong .gitignore)
├── .env                             # Khai báo Secret Key & Spreadsheet ID (nằm trong .gitignore)
└── README.md                        # Hướng dẫn sử dụng dự án
```

---

## 🛠️ Yêu cầu & Cài đặt

- **Python 3.9+**
- Môi trường ảo (khuyến nghị):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Cài đặt thư viện phụ thuộc

```powershell
pip install requests python-dotenv pandas openpyxl gspread google-auth
```

---

## ⚙️ Cấu hình môi trường (.env)

Tạo file `.env` tại thư mục gốc với các thông số:

```env
# Kalodata OpenAPI Key
SECRET_KEY=your_kalodata_secret_key

# Google Sheets Configuration
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id
GOOGLE_SERVICE_ACCOUNT=service_account.json
```

> **Lưu ý cấu hình Google Sheets:**
> 1. Tạo Service Account trên Google Cloud Console (bật Google Sheets API và Google Drive API), tải file JSON chứng thực về và đặt tên là `service_account.json`.
> 2. Mở file Google Sheet trên trình duyệt, bấm nút **Chia sẻ (Share)** và thêm email của Service Account với quyền **Người chỉnh sửa (Editor)**.

---

## 📖 Hướng dẫn sử dụng

### 1. Chạy toàn bộ Pipeline (`main.py`)

Chạy pipeline tuần tự từ tìm danh mục $\rightarrow$ cào danh sách Creator $\rightarrow$ cào chi tiết Creator:

```powershell
python main.py "từ khóa"
# Ví dụ:
python main.py "váy"
python main.py "gia dụng"
```

### 2. Chạy riêng từng module

#### A. Tìm danh mục TikTok Shop (`search.py`)
Tìm mã `TikTok Category ID` để cấu hình trong `creators.py`:
```powershell
python search.py "váy"
```

#### B. Cào danh sách Creator (`creators.py`)
Tự động lặp qua trang 1, 2, 3... cho đến khi số lượng data trả về ở trang trước đó `< 100`:
```powershell
python creators.py
```
> *Mẹo:* Bạn có thể cập nhật `category_ids` trong file `creators.py` theo mã Category ID vừa tìm được.

#### C. Cào chi tiết Creator (`creator_detail.py`)
Đọc tất cả `creator_id` từ `creators.json` và lưu chi tiết vào `creator_detail/<creator_id>.json`:
```powershell
python creator_detail.py
```

#### D. Đẩy dữ liệu lên Google Sheets (`sheet.py`)
Cú pháp: `python sheet.py <file_json> [tên_sheet]`
```powershell
# Ghi danh sách creators vào tab 'creators'
python sheet.py creators.json

# Hoặc chỉ định tên tab tùy ý
python sheet.py creators.json "Creators_Tuan1"
```

Sau khi hoàn tất, terminal sẽ in trực tiếp đường link mở tab tương ứng (kèm `#gid=...`).

---

## 🔄 Cơ chế hoạt động & Quy tắc xử lý

- **Quy tắc dừng phân trang:**
  API Kalodata trả về tối đa 100 creator/trang (`page_size: 100`). Vòng lặp `scrape_all_creators()` kiểm tra số lượng dữ liệu API trả về (`fetched_count = added + skipped`):
  - Nếu `fetched_count == 100`: Tiếp tục trang tiếp theo (`page += 1`).
  - Nếu `fetched_count < 100`: Dừng vòng lặp vì đã đến trang cuối cùng hoặc không còn dữ liệu.
- **Dedup thông minh:**
  Dù file JSON đã có sẵn dữ liệu, cơ chế dedup trong `kalo.py` sẽ đối soát `creator_id`. Bản ghi đã tồn tại sẽ được bỏ qua, chỉ lưu bổ sung bản ghi mới.
- **Batch Update Google Sheets:**
  `sheet.py` chia nhỏ dữ liệu thành từng đợt `BATCH_SIZE = 500` dòng/lần gọi API, kèm giãn cách thời gian để tránh bị lỗi `QuotaExceeded (429)`.

---

## 📊 Định dạng dữ liệu đầu ra (Output)

### `creators.json`
Chứa mảng các Creator được sắp xếp theo doanh thu:
```json
[
  {
    "creator_id": "6767877953680770050",
    "creator_nickname": "Milo On Diet",
    "creator_handle": "@miloondiet",
    "revenue": 44246662.65,
    "revenue_growth_rate": -65.35,
    "content_views": "10213758",
    "creator_followers": "1400000",
    "sales_volumn": 338,
    "video_revenue": 44246662.65,
    "live_revenue": 0.0,
    "category_list": null,
    "category_id_list": null,
    "ter_category_list": null,
    "ter_category_id_list": null
  }
]
```

### `creator_detail/<creator_id>.json`
Chứa thông tin chi tiết của từng Creator tương ứng:
```json
[
  {
    "creator_id": "6767877953680770050",
    "creator_handle": "@miloondiet",
    "video_revenue": 44246662.65,
    "video_views": 10213758,
    "shop_number": 12,
    "product_number": 45
  }
]
```
