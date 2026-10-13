import os
import sys
import json
import requests
from dotenv import load_dotenv

# Đảm bảo in tiếng Việt UTF-8 chuẩn trên Windows Console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()

ERP_BASE_URL = os.getenv("ERP_BASE_URL", "https://anb-erp.site").rstrip("/")
API_KEY_ERP = os.getenv("API_KEY_ERP", "").strip().strip('"').strip("'")

ENDPOINT = "/api/v1/booking/creators/search"
SEARCH_URL = f"{ERP_BASE_URL}{ENDPOINT}"


def search_creators(
    keyword: str = "",
    page: int = 1,
    page_size: int = 20,
    extra_payload: dict = None,
) -> dict:
    """
    Tìm kiếm creator từ ERP qua API:
        POST https://anb-erp.site/api/v1/booking/creators/search
        Header: Authorization: Bearer <API_KEY_ERP>

    Args:
        keyword: Từ khóa tìm kiếm (tên creator, handle...).
        page: Số thứ tự trang (mặc định: 1).
        page_size: Số lượng kết quả mỗi trang (mặc định: 20).
        extra_payload: Dữ liệu payload bổ sung nếu có.

    Returns:
        dict: Dữ liệu JSON trả về từ ERP hoặc None nếu có lỗi.
    """
    if not API_KEY_ERP:
        print("[ERROR] Chưa cấu hình API_KEY_ERP trong file .env")
        return None

    headers = {
        "Authorization": f"Bearer {API_KEY_ERP}",
        "Content-Type": "application/json",
    }

    payload = {
        "keyword": keyword,
        "page": page,
        "page_size": page_size,
    }

    if extra_payload:
        payload.update(extra_payload)

    print(f"\n[ERP] Gửi POST: {SEARCH_URL}")
    print(f"[ERP] Payload : {json.dumps(payload, ensure_ascii=False)}")

    try:
        resp = requests.post(SEARCH_URL, headers=headers, json=payload, timeout=30)
        print(f"[ERP] Mã phản hồi HTTP: {resp.status_code}")

        try:
            data = resp.json()
        except ValueError:
            print(f"[ERP] Response không phải JSON: {resp.text}")
            return None

        if resp.status_code == 200:
            return data
        else:
            err_msg = data.get("message", resp.text)
            err_code = data.get("error", "unknown_error")
            print(f"[ERP] Thất bại [{resp.status_code}] ({err_code}): {err_msg}")
            return data

    except requests.exceptions.RequestException as e:
        print(f"[ERP] Lỗi kết nối tới ERP: {e}")
        return None


def main():
    keyword = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    print("=" * 60)
    print(" ERP - TÌM KIẾM CREATORS (/api/v1/booking/creators/search)")
    print(f" URL     : {SEARCH_URL}")
    print(f" Từ khóa : '{keyword}'" if keyword else " Từ khóa : (tất cả / rỗng)")
    print("=" * 60)

    result = search_creators(keyword=keyword)

    if result:
        print("\n[ERP] Kết quả:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("\n[ERP] Không nhận được phản hồi.")


if __name__ == "__main__":
    main()
