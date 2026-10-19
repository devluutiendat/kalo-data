# TikTok Creator Scraper, AI Contact Extractor & Google Sheets Exporter

Công cụ tự động thu thập danh sách Creator và thông tin chi tiết từ **Kalodata API**, tích hợp **Google Gemini AI** tự động trích xuất thông tin liên hệ (Zalo, Email) từ Signature, hỗ trợ tìm kiếm danh mục và đồng bộ trực tiếp lên **Google Sheets**.

---

## 🚀 Tính năng nổi bật

- 🔍 **Tìm kiếm danh mục TikTok Shop:** Tra cứu mã danh mục TikTok Shop theo từ khóa từ file Excel cục bộ (`search.py`).
- 👥 **Thu thập Creator Rank:** Tự động phân trang (mỗi trang 100 creator), vòng lặp chạy liên tục cho đến khi số lượng data API trả về `< 100` (`creators.py`).
- 📄 **Thu thập Creator Detail (HTTP trực tiếp):** Gửi POST request thẳng tới `/creator/detail` bằng cookies từ DevTools (không cần Playwright), lưu vào `creators_detail.json` với dedup theo `creator_id` (`crawl_kalo_detail.py`).
- 🤖 **AI Trích xuất liên hệ thông minh (Gemini AI):**
  - Sau mỗi lần lấy detail, nếu `zalo` hoặc `email` rỗng → tự động gửi `signature` cho Gemini AI phân tích.
  - Sử dụng mô hình `gemini-2.0-flash` với Structured Output (Pydantic Schema) để nhận diện chính xác số điện thoại/Zalo và email từ văn bản thô (kể cả số bị viết lách).
  - Tích hợp cơ chế bắt lỗi rate limit 429: tự động tắt Gemini sau khi hết quota free tier (20 req/ngày), không gây gián đoạn quá trình scrape.
- 🍪 **Cookie-based Authentication:** Đọc cookie trực tiếp từ `kalodata_cookies.txt` (dán từ DevTools) hoặc `kalodata_cookies.json` (EditThisCookie format).
- ⏱️ **Random delay giữa requests:** Mỗi request nghỉ ngẫu nhiên 1–3 giây để tránh bị block.
- 🏢 **Tích hợp AnB ERP (`erp.py`):** Tra cứu và tìm kiếm thông tin creator trực tiếp từ hệ thống ERP thông qua API Bearer Token.
- 💾 **Dedup thông minh:** Tự động lọc trùng lặp theo `creator_id`, chỉ bổ sung bản ghi mới mà không ghi đè dữ liệu cũ.
- 📊 **Xuất dữ liệu lên Google Sheets:** Đồng bộ các file JSON lên tab tương ứng trên Google Sheets theo batch 500 hàng (`sheet.py`).

---

## 📁 Cấu trúc dự án

```
kalodata/
├── main.py                          # Entrypoint điều phối toàn bộ pipeline
├── search.py                        # Tìm kiếm danh mục TikTok Shop từ file Excel
├── creators.py                      # Lấy danh sách Creator Rank theo phân trang
├── crawl_kalo_detail.py             # ★ Lấy chi tiết Creator qua HTTP POST + Gemini enrichment
├── gemini.py                        # Trích xuất SĐT/Zalo và Email từ Signature bằng Gemini AI
├── erp.py                           # Tìm kiếm Creator trên hệ thống AnB ERP
├── kalo.py                          # Core HTTP client gọi Kalodata OpenAPI
├── sheet.py                         # Đẩy dữ liệu JSON lên Google Spreadsheet theo batch
├── kalodata_cookies.txt             # ⭐ Cookie string lấy từ toolsngon (bắt buộc, trong .gitignore)
├── TikTok Shop Category ....xlsx    # File dữ liệu danh mục TikTok Shop
├── creators.json                    # Dữ liệu danh sách Creator đã thu thập
├── creators_detail.json             # Dữ liệu chi tiết Creator (kèm zalo/email đã được AI bổ sung)
├── service_account.json             # Google Cloud Service Account key (bảo mật, nằm trong .gitignore)
├── .env                             # Khai báo Secret Keys & API Keys (nằm trong .gitignore)
└── README.md                        # Tài liệu hướng dẫn sử dụng dự án
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
pip install requests python-dotenv pandas openpyxl gspread google-auth google-genai pydantic
```

> ⚠️ **Lưu ý:** Các module như `time`, `os`, `sys`, `json`, `random` là thư viện tiêu chuẩn của Python, **không cần cài qua pip**.

---

## ⚙️ Cấu hình môi trường (.env)

Tạo file `.env` tại thư mục gốc của dự án với các thông số:

```env
# Google Gemini API Key (dùng trích xuất SĐT/Zalo/Email từ Signature)
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

## 🍪 Cấu hình Cookie (Bắt buộc)

> ⭐ **Cách duy nhất và được khuyến nghị**

### Lấy Cookie bằng toolsngon

1. **Tải và cài đặt [toolsngon](https://toolsngon.com)**, sau đó đăng nhập tài khoản Kalodata trong app.

2. **Tìm file Cookies trong thư mục profile:**
   ```
   C:\Users\<tên người dùng>\AppData\Roaming\toolsngon\browser-profiles\<id>\<id>\<id>\browser-data\Network\Cookies
   ```
   > *Thay `<id>` bằng ID thư mục thực tế trên máy bạn (thường là chuỗi số/chữ dài).*

3. **Gửi file `Cookies` đó cho AI phân tích** (ví dụ: ChatGPT, Gemini) với prompt:
   ```
   Đây là file SQLite Cookies của Chrome. Hãy đọc bảng cookies, lọc các cookie 
   có host chứa "kalodata.com", và xuất ra một chuỗi Cookie String theo định dạng:
   tên1=giá_trị1; tên2=giá_trị2; ...
   ```

4. **Ghi đè chuỗi Cookie nhận được vào file `kalodata_cookies.txt`** (toàn bộ nội dung file chỉ là 1 dòng cookie string).

---

## 📖 Hướng dẫn sử dụng

### 1. Chạy toàn bộ Pipeline (`main.py`)

Pipeline tuần tự: tìm danh mục → cào danh sách Creator → cào chi tiết + Gemini AI → đẩy lên Google Sheets:

```powershell
python main.py "từ khóa"
# Ví dụ:
python main.py "váy"
python main.py "gia dụng"
```

### 2. Chạy riêng từng module

#### A. Tìm danh mục TikTok Shop (`search.py`)
```powershell
python search.py "váy"
```

#### B. Cào danh sách Creator (`creators.py`)
```powershell
python creators.py
```
> *Mẹo:* Cập nhật `category_ids` trong file `creators.py` theo mã Category ID vừa tìm được.

#### C. Cào chi tiết Creator & Trích xuất Contact (`crawl_kalo_detail.py`) ★ Mới

```powershell
# Scrape tất cả creators chưa có trong creators_detail.json (có delay + Gemini)
python crawl_kalo_detail.py --all

# Chạy thử N creator đầu tiên rồi tự push lên Google Sheets
python crawl_kalo_detail.py --main 50
python crawl_kalo_detail.py --main 100

# Chỉ push dữ liệu đã có lên Google Sheets (không scrape thêm)
python crawl_kalo_detail.py --sheet

# Lấy detail 1 creator cụ thể theo ID
python crawl_kalo_detail.py 6767877953680770050
```

**Flow xử lý mỗi creator:**
```
POST /creator/detail
    ↓
Kiểm tra zalo & email
    ├─ Cả hai đã có → Lưu ngay
    └─ Thiếu ít nhất 1 → Gemini AI phân tích signature
           ↓
       Trích xuất zalo/email → Ghi đè vào record
           ↓
       Lưu vào creators_detail.json
    ↓
Random sleep 1–3s
```

> ⚠️ **Gemini Free Tier:** Giới hạn **20 requests/ngày**. Khi hết quota, Gemini tự tắt trong session đó, scrape vẫn tiếp tục bình thường (chỉ bỏ phần enrichment).

#### D. Kiểm tra trích xuất Contact độc lập bằng Gemini (`gemini.py`)
```powershell
python gemini.py
```

#### E. Tìm kiếm Creator trên hệ thống ERP (`erp.py`)
```powershell
python erp.py "tên_creator_hoặc_handle"
```

#### F. Đẩy dữ liệu lên Google Sheets (`sheet.py`)
```powershell
# Ghi danh sách creators vào tab 'creators'
python sheet.py creators.json creators

# Ghi chi tiết creators vào tab 'creators_detail'
python sheet.py creators_detail.json creators_detail
```

---

## 🔄 Cơ chế hoạt động & Quy tắc xử lý

- **Quy tắc dừng phân trang:**
  API Kalodata trả về tối đa 100 creator/trang. Vòng lặp dừng khi `fetched_count < 100`.

- **Dedup thông minh:**
  `creator_id` đã tồn tại trong file JSON sẽ bị bỏ qua, chỉ append bản ghi mới.

- **Xử lý thiếu thông tin liên hệ (Gemini Fallback):**

  ```mermaid
  flowchart TD
      A[Fetch /creator/detail] --> B{zalo & email đủ?}
      B -->|Có| Z[Lưu vào JSON]
      B -->|Thiếu| C{signature rỗng?}
      C -->|Rỗng| Z
      C -->|Có nội dung| D[Gemini AI phân tích signature]
      D --> E{Tìm thấy contact?}
      E -->|Có| F[Ghi đè zalo / email]
      E -->|Không| Z
      F --> Z
  ```

- **Xử lý Rate Limit Gemini 429:**
  Sau khi gặp lỗi `RESOURCE_EXHAUSTED`, flag `_gemini_exhausted = True` được bật → các creator tiếp theo **bỏ qua bước Gemini** để không làm chậm pipeline. Data vẫn được lưu đầy đủ.

- **Batch Update Google Sheets:**
  `sheet.py` chia nhỏ dữ liệu thành từng đợt `BATCH_SIZE = 500` dòng/lần gọi API.

---

## 📊 Định dạng dữ liệu đầu ra (Output)

### `creators.json`
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

### `creators_detail.json`
```json
[
  {
    "creator_id": "6767877953680770050",
    "nickname": "Milo On Diet",
    "handle": "miloondiet",
    "follower_count": "1,4tr",
    "signature": "Cô Gái Bản Uông, Quảng Ninh 🥰\nFor Work viber: 033.442.5233",
    "zalo": "033.442.5233",
    "email": "",
    "product_count": "187",
    "region": "Việt Nam",
    "creator_type": "INDEPENDENT",
    "has_mcn": -1,
    "collect_day": "2024-01-04"
  }
]
```

---

## ⚠️ Lưu ý quan trọng

- **Cookie hết hạn:** Nếu API trả về `success=False`, cần lấy lại cookie mới từ DevTools và cập nhật `kalodata_cookies.txt`.
- **Gemini Free Tier:** Giới hạn 20 requests/ngày. Để scrape không giới hạn, cần nâng cấp lên [Google AI Studio Paid](https://ai.google.dev/pricing).
- **Thời gian scrape toàn bộ:** Với ~5750 creators và delay 1–3s/request, ước tính **3–5 tiếng** để hoàn thành `--all`.
