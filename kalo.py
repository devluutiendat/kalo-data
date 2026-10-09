import os
import sys
import json
import requests
from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

headers = {
    "secret-key": SECRET_KEY,
    "Content-Type": "application/json;charset=utf-8",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}

def _load_existing(file: str) -> list:
    """Đọc danh sách đã lưu từ file JSON. Trả về list rỗng nếu file chưa tồn tại."""
    if not os.path.exists(file):
        return []
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def _save_file(file: str, data: list):
    """Ghi danh sách ra file JSON."""
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_kalo_data(payload_data: object, url: str, file: str, id_name: str) -> dict:
    """
    Gửi request POST tới Kalodata OpenAPI.
    - Lấy danh sách item từ response.
    - So sánh với dữ liệu cũ đã lưu theo id_name.
    - Chỉ append những item mới (chưa có id trùng) vào file.

    Returns:
        dict: {
            "added": int,    # số item mới được thêm
            "skipped": int,  # số item bị bỏ qua (trùng)
            "result": dict   # raw JSON response từ API
        }
        hoặc None nếu có lỗi request.
    """
    req_headers = headers.copy()
    req_headers["secret-key"] = SECRET_KEY

    try:
        response = requests.post(url, headers=req_headers, json=payload_data, timeout=30)
        print(f"Status Code: {response.status_code}")

        try:
            result = response.json()
        except json.JSONDecodeError:
            print("Response không phải định dạng JSON:")
            print(response.text)
            return None

        if not result:
            print("Response rỗng.")
            return result

        raw_data = result.get("data", result)
        print(f"[DEBUG] success={result.get('success')} | raw_data type={type(raw_data).__name__}")

        # --- Lấy danh sách item từ response ---
        if isinstance(raw_data, list):
            # Trường hợp data là list (VD: creator rank)
            new_items = raw_data
            print(f"[DEBUG] data là list, số item nhận về: {len(new_items)}")

        elif isinstance(raw_data, dict):
            if id_name in raw_data:
                # Trường hợp data là 1 object đơn lẻ (VD: creator detail)
                new_items = [raw_data]
                print(f"[DEBUG] data là object đơn, id_name='{id_name}' value='{raw_data.get(id_name)}'")
            else:
                # Dict nhưng không có id_name → thử tìm list con
                new_items = next(
                    (v for v in raw_data.values() if isinstance(v, list)),
                    []
                )
                print(f"[DEBUG] data là dict, tìm list con → {len(new_items)} item")

        else:
            print(f"[DEBUG] raw_data không nhận diện được (type={type(raw_data).__name__}), bỏ qua.")
            return result

        if not new_items:
            print("[WARN] Không có item nào để xử lý.")
            return {"added": 0, "skipped": 0, "result": result}

        # --- Dedup ---
        existing = _load_existing(file)
        existing_ids = {item.get(id_name) for item in existing if isinstance(item, dict)}
        print(f"[DEBUG] File hiện tại có {len(existing)} item | existing_ids={existing_ids}")

        added = []
        skipped = 0
        for item in new_items:
            item_id = item.get(id_name) if isinstance(item, dict) else None
            print(f"[DEBUG] Xử lý item id_name='{id_name}' value='{item_id}'", end=" → ")
            if item_id is not None and item_id in existing_ids:
                skipped += 1
                print("BỎ QUA (đã tồn tại)")
            else:
                existing.append(item)
                if item_id is not None:
                    existing_ids.add(item_id)
                added.append(item)
                print("THÊM MỚI")

        _save_file(file, existing)
        print(f"\nThêm mới: {len(added)} item | Bỏ qua (trùng {id_name}): {skipped} item")
        print(f"Tổng số item trong file: {len(existing)}")
        print(f"Đã lưu dữ liệu vào {file}")

        return {"added": len(added), "skipped": skipped, "result": result}

    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gửi request: {e}")
        return None