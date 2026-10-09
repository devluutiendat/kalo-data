"""
sheet.py — Upload JSON file → Google Sheets
-------------------------------------------
Usage:
    python sheet.py <json_file> [sheet_name]

    json_file  : đường dẫn tới file JSON (list of dicts)
    sheet_name : (tuỳ chọn) tên sheet tab muốn ghi vào
                 Mặc định = tên file không có extension (vd: creators.json → "creators")

Auth (Service Account) — khai báo trong .env:
    GOOGLE_SPREADSHEET_ID   : ID của Google Spreadsheet
    GOOGLE_SERVICE_ACCOUNT  : đường dẫn tới file JSON service-account credential
                              (vd: service_account.json)

Behaviour:
    - Nếu sheet tab chưa tồn tại → tạo mới.
    - Nếu sheet tab đã tồn tại → xoá hết dữ liệu cũ rồi ghi lại.
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

load_dotenv()

# ── Cấu hình ────────────────────────────────────────────────────────────────

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SPREADSHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID", "")
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT", "service_account.json")

BATCH_SIZE = 500  # số hàng ghi mỗi lần gọi API


# ── Helpers ──────────────────────────────────────────────────────────────────

def load_json(path: str) -> list:
    """Đọc file JSON và trả về list of dicts."""
    if not os.path.exists(path):
        print(f"[ERROR] File không tồn tại: {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        print("[ERROR] File JSON phải là một mảng (list) các object.")
        sys.exit(1)
    if not data:
        print("[WARN] File JSON rỗng, không có dữ liệu để ghi.")
        sys.exit(0)
    return data


def get_or_create_sheet(spreadsheet, sheet_name: str):
    """Lấy sheet theo tên; nếu chưa có thì tạo mới."""
    try:
        ws = spreadsheet.worksheet(sheet_name)
        print(f"[INFO] Sheet '{sheet_name}' đã tồn tại → xoá dữ liệu cũ.")
        ws.clear()
        return ws
    except gspread.exceptions.WorksheetNotFound:
        print(f"[INFO] Tạo sheet mới: '{sheet_name}'")
        return spreadsheet.add_worksheet(title=sheet_name, rows=5000, cols=50)


def flatten_value(v) -> str:
    """Chuyển giá trị phức tạp (list/dict) thành chuỗi để ghi vào cell."""
    if v is None:
        return ""
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def data_to_rows(data: list):
    """Trả về (headers, rows) từ list of dicts."""
    # Thu thập tất cả keys theo thứ tự xuất hiện
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


def write_in_batches(ws, header: list, rows: list):
    """Ghi header + rows vào worksheet theo batch."""
    # Ghi header
    ws.append_row(header, value_input_option="RAW")

    total = len(rows)
    num_batches = math.ceil(total / BATCH_SIZE) if total > 0 else 0
    print(f"[INFO] Tổng {total} hàng dữ liệu → {num_batches} batch (mỗi batch {BATCH_SIZE} hàng)")

    for i in range(num_batches):
        batch = rows[i * BATCH_SIZE : (i + 1) * BATCH_SIZE]
        ws.append_rows(batch, value_input_option="RAW")
        print(f"  Batch {i+1}/{num_batches}: ghi {len(batch)} hàng ✓")
        if i < num_batches - 1:
            time.sleep(1)  # tránh rate-limit


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python sheet.py <json_file> [sheet_name]")
        sys.exit(1)

    json_file = sys.argv[1]
    # Tên sheet: dùng tham số thứ 2 nếu có, không thì lấy tên file
    sheet_name = sys.argv[2] if len(sys.argv) >= 3 else os.path.splitext(os.path.basename(json_file))[0]

    # Kiểm tra config
    if not SPREADSHEET_ID:
        print("[ERROR] GOOGLE_SPREADSHEET_ID chưa được khai báo trong .env")
        sys.exit(1)
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(f"[ERROR] File service account không tìm thấy: {SERVICE_ACCOUNT_FILE}")
        print("        Khai báo GOOGLE_SERVICE_ACCOUNT trong .env hoặc đặt file service_account.json vào thư mục dự án.")
        sys.exit(1)

    print(f"[INFO] File JSON  : {json_file}")
    print(f"[INFO] Sheet name : {sheet_name}")
    print(f"[INFO] Spreadsheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")

    # Xác thực
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)

    # Mở spreadsheet
    try:
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"[ERROR] Không tìm thấy Spreadsheet với ID: {SPREADSHEET_ID}")
        print("        Kiểm tra lại GOOGLE_SPREADSHEET_ID và quyền truy cập của service account.")
        sys.exit(1)

    # Đọc dữ liệu
    data = load_json(json_file)
    print(f"[INFO] Đọc được {len(data)} bản ghi từ '{json_file}'")

    # Chuẩn bị headers + rows
    headers, rows = data_to_rows(data)
    print(f"[INFO] Số cột (headers): {len(headers)}")

    # Lấy / tạo worksheet
    ws = get_or_create_sheet(spreadsheet, sheet_name)

    # Ghi dữ liệu
    write_in_batches(ws, headers, rows)

    print(f"\n✅ Xong! Đã ghi {len(rows)} hàng vào sheet '{sheet_name}'.")
    print(f"   Mở tại: {ws.url}")


if __name__ == "__main__":
    main()
