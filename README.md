# TikTok Creator Scraper, AI Contact Extractor & Google Sheets Exporter

Công cụ tự động thu thập danh sách Creator và thông tin chi tiết từ **Kalodata OpenAPI**, tích hợp **Google Gemini AI** tự động trích xuất thông tin liên hệ (Zalo, Email) từ Bio, hỗ trợ tìm kiếm trên **ERP** và đồng bộ trực tiếp lên **Google Sheets**.

---

## 🚀 Tính năng nổi bật

- 🔍 **Tìm kiếm danh mục TikTok Shop:** Tra cứu mã danh mục TikTok Shop theo từ khóa từ file Excel cục bộ (`search.py`).
- 👥 **Thu thập Creator Rank:** Tự động phân trang (mỗi trang 100 creator), vòng lặp chạy liên tục cho đến khi số lượng data API trả về `< 100` (`creators.py`).
- 📄 **Thu thập Creator Detail:** Tự động gọi API lấy chi tiết từng creator và lưu tập trung vào `creator_detail.json` với cơ chế dedup theo `creator_id` (`creator_detail.py`).
- 🤖 **AI Trích xuất liên hệ thông minh (Gemini & Regex):** 
  - Nếu API Kalodata không trả về Zalo (`creator_contact_zalo`) hoặc Email (`creator_contact_email`), hệ thống tự động đọc `creator_bio`.
  - **Làm sạch văn bản (`normalize_text.py`):** Ánh xạ các emoji số đặc biệt (`0️⃣`–`9️⃣`, `🔟`), giải mã các ký tự lách luật (thay `o`/`O` thành `0`), loại bỏ emoji trang trí và chuẩn hóa Unicode NFKC.
  - **Trích xuất bằng Gemini AI (`gemini.py`):** Sử dụng mô hình `gemini-3.8-flash` với Structured Output (Pydantic Schema) để nhận diện chính xác số điện thoại/Zalo và email, sau đó tự động cập nhật bù vào `creator_detail.json`.
- 🏢 **Tích hợp AnB ERP (`erp.py`):** Tra cứu và tìm kiếm thông tin creator trực tiếp từ hệ thống ERP thông qua API Bearer Token.
- 💾 **Dedup thông minh:** Tự động lọc trùng lặp theo `creator_id`, chỉ bổ sung bản ghi mới mà không ghi đè dữ liệu cũ (`kalo.py`).
- 📊 **Xuất dữ liệu lên Google Sheets:** Đồng bộ các file JSON (`creators.json`, `creator_detail.json`) lên tab tương ứng trên Google Sheets theo batch 500 hàng, chống vượt hạn mức Google API Quota (`sheet.py`).

---

## 📁 Cấu trúc dự án

```
kalodata/
├── main.py                          # Entrypoint điều phối toàn bộ pipeline
├── search.py                        # Tìm kiếm danh mục TikTok Shop từ file Excel
├── creators.py                      # Lấy danh sách Creator Rank theo phân trang
├── creator_detail.py                # Lấy thông tin chi tiết từng Creator & kích hoạt Gemini fallback
├── normalize_text.py                # Chuẩn hóa văn bản, xử lý emoji số và lách luật số điện thoại
├── gemini.py                        # Trích xuất số điện thoại/Zalo và Email từ text bằng Gemini AI
├── erp.py                           # Tìm kiếm Creator trên hệ thống AnB ERP
├── kalo.py                          # Core HTTP client gọi Kalodata OpenAPI (dedup & lưu file JSON)
├── sheet.py                         # Đẩy dữ liệu JSON lên Google Spreadsheet
├── TikTok Shop Category ....xlsx    # File dữ liệu danh mục TikTok Shop
├── creators.json                    # Dữ liệu danh sách Creator đã thu thập
├── creator_detail.json              # Dữ liệu chi tiết Creator (kèm contact đã được AI bù đắp)
├── service_account.json             # Google Cloud Service Account key (bảo mật, nằm trong .gitignore)
├── .env                             # Khai báo Secret Keys & API Keys (nằm trong .gitignore)
└── README.md                        # Hướng dẫn sử dụng dự án
```

---

## 🛠️ Yêu cầu & Cài đặt

- **Python 3.10+**
- Môi trường ảo (khuyến nghị):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Cài đặt thư viện phụ thuộc

```powershell
pip install requests python-dotenv pandas openpyxl gspread google-auth google-genai pydantic emoji
```

---

## ⚙️ Cấu hình môi trường (.env)

Tạo file `.env` tại thư mục gốc của dự án với các thông số:

```env
# Kalodata OpenAPI Key
SECRET_KEY=your_kalodata_secret_key

# Google Gemini API Key (dùng trích xuất SĐT/Zalo/Email từ Bio)
GEMINI_API_KEY=your_gemini_api_key

# AnB ERP Configuration
ERP_BASE_URL=https://anb-erp.site
API_KEY_ERP=your_erp_api_key

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

Chạy pipeline tuần tự từ tìm danh mục $\rightarrow$ cào danh sách Creator $\rightarrow$ cào chi tiết Creator (kèm kích hoạt Gemini trích xuất contact nếu thiếu):

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

#### C. Cào chi tiết Creator & Trích xuất Bio bằng AI (`creator_detail.py`)
Đọc danh sách `creator_id` từ `creators.json` và lưu chi tiết vào `creator_detail.json`:
- Nếu `creator_contact_zalo` hoặc `creator_contact_email` rỗng, hệ thống sẽ tự động gọi `normalize_with_gemini()` để đọc từ `creator_bio` và điền bù vào bản ghi.

```powershell
python creator_detail.py
```

#### D. Kiểm tra trích xuất Bio độc lập (`gemini.py` / `normalize_text.py`)
Thử nghiệm xử lý emoji, lách luật số điện thoại và gọi Gemini:
```powershell
python normalize_text.py
python gemini.py
```

#### E. Tìm kiếm Creator trên hệ thống ERP (`erp.py`)
Tra cứu creator trên AnB ERP theo từ khóa:
```powershell
python erp.py "tên_creator_hoặc_handle"
```

#### F. Đẩy dữ liệu lên Google Sheets (`sheet.py`)
Cú pháp: `python sheet.py <file_json> [tên_sheet]`
```powershell
# Ghi danh sách creators vào tab 'creators'
python sheet.py creators.json

# Ghi chi tiết creators vào tab 'creator_detail'
python sheet.py creator_detail.json

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
- **Xử lý thiếu thông tin liên hệ (AI Fallback):**
  Khi thêm mới creator vào `creator_detail.json`, nếu thiếu số Zalo hoặc Email và creator có `creator_bio`, luồng xử lý:
  $$\text{Bio} \xrightarrow{\text{normalize\_text}} \text{Văn bản sạch} \xrightarrow{\text{Gemini 3.8 Flash}} \{\text{contact\_zalo, contact\_email}\} \xrightarrow{\text{update}} \text{creator\_detail.json}$$
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
    "live_revenue": 0.0
  }
]
```

### `creator_detail.json`
Chứa thông tin chi tiết của Creator kèm contact (đã được AI bổ sung nếu có trong Bio):
```json
[
  {
    "creator_id": "6705337685530117121",
    "creator_nickname": "Trịnh Mai Hương",
    "creator_handle": "@trinhmaihuongg",
    "creator_bio": "Zalo công việc: 0905182202 - maihuong@gmail.com",
    "creator_contact_zalo": "0905182202",
    "creator_contact_email": "maihuong@gmail.com",
    "creator_contact_tiktok": "trinhmaihuongg",
    "revenue": 699892858.12,
    "sales_volumn": 5266,
    "creator_followers": "161500"
  }
]
```
