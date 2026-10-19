"""
sheet.py — Google Sheets utilities (generic + domain-specific)
--------------------------------------------------------------
Usage (standalone):
    python sheet.py <json_file> [sheet_name]

Auth (Service Account) — khai báo trong .env:
    GOOGLE_SPREADSHEET_ID   : ID của Google Spreadsheet
    GOOGLE_SERVICE_ACCOUNT  : đường dẫn tới file JSON service-account credential

Behaviour:
    - Nếu sheet tab chưa tồn tại → tạo mới (ghi header + data).
    - Nếu sheet tab đã tồn tại → chỉ append các bản ghi mới (dedup theo id_name).
    - Hàng đầu tiên là header (lấy từ keys của item đầu tiên).
    - Ghi theo batch để không vượt quota API.
"""

import os
import sys
import json
import math
import time
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# ── Cấu hình ────────────────────────────────────────────────────────────────

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SPREADSHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID", "")
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT", "service_account.json")

BATCH_SIZE = 500  # số hàng ghi mỗi lần gọi API


# ══════════════════════════════════════════════════════════════════════════════
# GENERIC HELPERS — Tái sử dụng cho mọi tác vụ Google Sheets
# ══════════════════════════════════════════════════════════════════════════════

# ── Auth ─────────────────────────────────────────────────────────────────────

_spreadsheet_cache = None


def _get_spreadsheet():
    """Authenticate và trả về spreadsheet object. Cache lại sau lần đầu."""
    global _spreadsheet_cache
    if _spreadsheet_cache is not None:
        return _spreadsheet_cache

    if not SPREADSHEET_ID:
        print("[ERROR] GOOGLE_SPREADSHEET_ID chưa được khai báo trong .env")
        return None
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(f"[ERROR] File service account không tìm thấy: {SERVICE_ACCOUNT_FILE}")
        return None

    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)

    try:
        _spreadsheet_cache = client.open_by_key(SPREADSHEET_ID)
        return _spreadsheet_cache
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"[ERROR] Không tìm thấy Spreadsheet với ID: {SPREADSHEET_ID}")
        return None

# ── Worksheet ────────────────────────────────────────────────────────────────

def get_worksheet(sheet_name: str, create_if_missing: bool = True):
    """
    Lấy worksheet theo tên.

    Returns:
        (worksheet, is_new) — is_new=True nếu vừa tạo mới.
        (None, False) nếu lỗi.
    """
    spreadsheet = _get_spreadsheet()
    if spreadsheet is None:
        return None, False

    try:
        ws = spreadsheet.worksheet(sheet_name)
        return ws, False
    except gspread.exceptions.WorksheetNotFound:
        if create_if_missing:
            print(f"[INFO] Tạo sheet mới: '{sheet_name}'")
            ws = spreadsheet.add_worksheet(title=sheet_name, rows=5000, cols=50)
            return ws, True
        return None, False


# ── Column helpers ───────────────────────────────────────────────────────────

def ensure_columns(ws, columns: list) -> list:
    """
    Đảm bảo các cột tồn tại trong header row (hàng 1).
    Nếu chưa có → thêm vào cuối.

    Returns:
        list headers hiện tại (sau khi đã bổ sung).
    """
    headers = ws.row_values(1)
    if not headers:
        # Sheet rỗng → ghi header mới
        ws.append_row(columns, value_input_option="RAW")
        return list(columns)

    new_cols = [col for col in columns if col not in headers]
    if new_cols:
        start_col = len(headers) + 1
        cells = []
        for i, col in enumerate(new_cols):
            cells.append(gspread.Cell(1, start_col + i, col))
        ws.update_cells(cells, value_input_option="RAW")
        headers.extend(new_cols)
        print(f"[sheet] Đã thêm {len(new_cols)} cột mới: {new_cols}")

    return headers


# ── Find & Update ────────────────────────────────────────────────────────────

def find_row_index(ws, col_name: str, value: str) -> int | None:
    """
    Tìm số thứ tự hàng (1-indexed) chứa `value` trong cột `col_name`.

    Returns:
        row_index (int) nếu tìm thấy, None nếu không.
    """
    headers = ws.row_values(1)
    if col_name not in headers:
        return None

    col_index = headers.index(col_name) + 1  # gspread dùng 1-indexed
    col_values = ws.col_values(col_index)

    for row_idx, cell_value in enumerate(col_values, 1):
        if row_idx == 1:
            continue  # bỏ header
        if str(cell_value).strip() == str(value).strip():
            return row_idx

    return None


def update_cells(ws, row_index: int, updates: dict, headers: list = None):
    """
    Cập nhật các cell tại hàng `row_index` theo dict {col_name: value}.

    Args:
        ws: worksheet object
        row_index: số thứ tự hàng (1-indexed)
        updates: dict mapping column_name → new_value
        headers: danh sách header (nếu đã có sẵn, tránh gọi API thêm)
    """
    if headers is None:
        headers = ws.row_values(1)

    cells = []
    for col_name, value in updates.items():
        if col_name in headers:
            col_idx = headers.index(col_name) + 1
            cells.append(gspread.Cell(row_index, col_idx, flatten_value(value)))

    if cells:
        ws.update_cells(cells, value_input_option="RAW")


def upsert_row(ws, key_col: str, key_value: str, data: dict, headers: list = None) -> str:
    """
    Tìm hàng theo key_col == key_value:
    - Tìm thấy → update các cột trong `data`.
    - Không tìm thấy → append hàng mới.

    Returns:
        "updated" | "appended" | "error"
    """
    if headers is None:
        headers = ws.row_values(1)

    row_index = find_row_index(ws, key_col, key_value)

    if row_index:
        update_cells(ws, row_index, data, headers=headers)
        return "updated"
    else:
        row = [flatten_value(data.get(h, "")) for h in headers]
        ws.append_row(row, value_input_option="RAW")
        return "appended"


# ── Data helpers ─────────────────────────────────────────────────────────────

def load_json(path: str) -> list:
    """Đọc file JSON và trả về list of dicts."""
    if not os.path.exists(path):
        print(f"[ERROR] File không tồn tại: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        print("[ERROR] File JSON phải là một mảng (list) các object.")
        return []
    if not data:
        print("[WARN] File JSON rỗng, không có dữ liệu để ghi.")
        return []
    return data


def flatten_value(v) -> str:
    """Chuyển giá trị phức tạp (list/dict) thành chuỗi để ghi vào cell."""
    if v is None:
        return ""
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def data_to_rows(data: list, headers: list = None):
    """
    Trả về (headers, rows) từ list of dicts.
    Nếu headers được truyền vào → dùng headers đó (giữ đúng thứ tự cột trên sheet).
    """
    if headers is None:
        headers = list(dict.fromkeys(
            key for item in data if isinstance(item, dict) for key in item.keys()
        ))
    rows = [
        [flatten_value(item.get(h)) for h in headers]
        if isinstance(item, dict)
        else [flatten_value(item)] + [""] * (len(headers) - 1)
        for item in data
    ]
    return headers, rows


def write_in_batches(ws, rows: list, header: list = None):
    """
    Ghi rows vào worksheet theo batch.
    Nếu header được truyền → ghi header trước (dùng cho sheet mới).
    """
    if header:
        ws.append_row(header, value_input_option="RAW")

    total = len(rows)
    if total == 0:
        print("[INFO] Không có dữ liệu mới để ghi.")
        return

    num_batches = math.ceil(total / BATCH_SIZE)
    print(f"[INFO] Tổng {total} hàng dữ liệu → {num_batches} batch (mỗi batch {BATCH_SIZE} hàng)")

    for i in range(num_batches):
        batch = rows[i * BATCH_SIZE : (i + 1) * BATCH_SIZE]
        ws.append_rows(batch, value_input_option="RAW")
        print(f"  Batch {i+1}/{num_batches}: ghi {len(batch)} hàng ✓")
        if i < num_batches - 1:
            time.sleep(1)  # tránh rate-limit


def get_existing_ids(ws, id_col_index: int) -> set:
    """
    Đọc toàn bộ cột id_col_index (0-indexed) từ worksheet,
    trả về set các giá trị ID đã có (bỏ header).
    """
    try:
        all_values = ws.get_all_values()
        if len(all_values) <= 1:
            return set()
        return {row[id_col_index] for row in all_values[1:] if id_col_index < len(row)}
    except Exception:
        return set()


# ══════════════════════════════════════════════════════════════════════════════
# ZALO LOG — Cập nhật trạng thái gửi Zalo vào sheet "creator_detail"
# ══════════════════════════════════════════════════════════════════════════════

_zalo_ws = None
_zalo_headers = None

ZALO_SHEET_NAME = "creator_detail"
ZALO_KEY_COL = "creator_nickname"
ZALO_EXTRA_COLS = ["ngày nhắn zalo", "trạng thái zalo", "đã liên hệ"]


def _get_zalo_ws():
    """
    Lazy-init: lần đầu gọi sẽ auth + lấy sheet 'creator_detail',
    đảm bảo các cột Zalo tồn tại, cache lại cho các lần sau.
    """
    global _zalo_ws, _zalo_headers
    if _zalo_ws is not None:
        return _zalo_ws, _zalo_headers

    ws, _ = get_worksheet(ZALO_SHEET_NAME, create_if_missing=False)
    if ws is None:
        print(f"[ERROR] Sheet '{ZALO_SHEET_NAME}' không tồn tại. Hãy chạy save_to_google_sheet trước.")
        return None, None

    headers = ensure_columns(ws, ZALO_EXTRA_COLS)

    _zalo_ws = ws
    _zalo_headers = headers
    return ws, headers


def log_zalo_status(
    creator_nickname: str,
    status: str,
    contacted: bool,
):
    """
    Tìm hàng theo creator_contact_zalo == phone_number trên sheet 'creator_detail',
    chỉ cập nhật các cột: ngày nhắn zalo, trạng thái zalo, đã liên hệ.

    Args:
        creator_nickname: Tên creator (dùng để log, không ghi đè lên sheet)
        status: Trạng thái (vd: "Số không tồn tại", "Đã liên hệ", "Lỗi gửi tin nhắn")
        contacted: True nếu đã gửi tin nhắn thành công
    """
    ws, headers = _get_zalo_ws()
    if ws is None:
        print("[WARN] Không thể ghi log Zalo vào Google Sheets.")
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    updates = {
        "ngày nhắn zalo": now,
        "trạng thái zalo": status,
        "đã liên hệ": str(contacted),
    }

    try:
        row_index = find_row_index(ws, ZALO_KEY_COL, creator_nickname)
        if row_index:
            update_cells(ws, row_index, updates, headers=headers)
            print(f"[sheet] Đã cập nhật hàng {row_index}: {creator_nickname} | {status}")
        else:
            print(f"[sheet] Không tìm thấy '{creator_nickname}' trên sheet '{ZALO_SHEET_NAME}', bỏ qua.")
    except Exception as e:
        print(f"[sheet] Lỗi ghi log Zalo: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# SAVE TO GOOGLE SHEET — Upload JSON file (dedup & append)
# ══════════════════════════════════════════════════════════════════════════════

def save_to_google_sheet(json_file: str = None, sheet_name: str = None, id_name: str = None):
    """
    Đọc file JSON và ghi lên Google Sheets.
    - Nếu sheet đã tồn tại → chỉ append các bản ghi mới (dedup theo id_name).
    - Nếu sheet chưa tồn tại → tạo mới và ghi toàn bộ.

    Args:
        json_file: Đường dẫn tới file JSON. Nếu None → lấy từ sys.argv[1].
        sheet_name: Tên sheet tab. Nếu None → lấy từ sys.argv[2] hoặc tên file.
        id_name: Tên field dùng làm khóa dedup (vd: "creator_id"). Nếu None → ghi hết, không dedup.
    """
    # Resolve tham số từ sys.argv nếu chưa truyền trực tiếp
    if json_file is None:
        if len(sys.argv) < 2:
            print("Usage: python sheet.py <json_file> [sheet_name]")
            return
        json_file = sys.argv[1]

    if sheet_name is None:
        sheet_name = sys.argv[2] if len(sys.argv) >= 3 else os.path.splitext(os.path.basename(json_file))[0]

    spreadsheet = _get_spreadsheet()
    if spreadsheet is None:
        return

    print(f"[INFO] File JSON  : {json_file}")
    print(f"[INFO] Sheet name : {sheet_name}")
    print(f"[INFO] Spreadsheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")

    # Đọc dữ liệu
    data = load_json(json_file)
    if not data:
        return

    print(f"[INFO] Đọc được {len(data)} bản ghi từ '{json_file}'")

    # Kiểm tra sheet đã tồn tại chưa
    is_new_sheet = False
    try:
        ws = spreadsheet.worksheet(sheet_name)
        print(f"[INFO] Sheet '{sheet_name}' đã tồn tại → chỉ append dữ liệu mới.")
    except gspread.exceptions.WorksheetNotFound:
        print(f"[INFO] Tạo sheet mới: '{sheet_name}'")
        ws = spreadsheet.add_worksheet(title=sheet_name, rows=5000, cols=50)
        is_new_sheet = True

    if is_new_sheet:
        headers, rows = data_to_rows(data)
        print(f"[INFO] Số cột (headers): {len(headers)}")
        write_in_batches(ws, rows, header=headers)
        print(f"\n✅ Xong! Đã ghi {len(rows)} hàng vào sheet mới '{sheet_name}'.")
    else:
        # Sheet đã tồn tại → đọc header hiện có trên sheet
        existing_headers = ws.row_values(1)
        if not existing_headers:
            headers, rows = data_to_rows(data)
            write_in_batches(ws, rows, header=headers)
            print(f"\n✅ Xong! Đã ghi {len(rows)} hàng vào sheet '{sheet_name}'.")
        else:
            # Dedup: lọc ra các bản ghi chưa có trên sheet
            if id_name and id_name in existing_headers:
                id_col_index = existing_headers.index(id_name)
                existing_ids = get_existing_ids(ws, id_col_index)
                new_data = [
                    item for item in data
                    if isinstance(item, dict) and flatten_value(item.get(id_name)) not in existing_ids
                ]
                print(f"[INFO] Đã có {len(existing_ids)} bản ghi trên sheet, {len(new_data)} bản ghi mới cần ghi.")
            else:
                new_data = data
                if id_name:
                    print(f"[WARN] Không tìm thấy cột '{id_name}' trên sheet → ghi toàn bộ (không dedup).")

            if not new_data:
                print("[INFO] Không có bản ghi mới nào cần ghi.")
                return

            _, rows = data_to_rows(new_data, headers=existing_headers)
            write_in_batches(ws, rows)
            print(f"\n✅ Xong! Đã append thêm {len(rows)} hàng mới vào sheet '{sheet_name}'.")

    print(f"   Mở tại: {ws.url}")


if __name__ == "__main__":
    save_to_google_sheet("creator_detail.json", "creator_detail", "creator_id")
