import json
import os
from kalo import get_kalo_data

CREATORS_FILE = "creators.json"
CREATORS_DETAIL_DIR = "creator_detail"
URL = "https://www.kalodata.com/openapi/v1/tiktok/creator/detail"

def get_creator_detail(creator_id: str) -> dict:

    """
    Lấy thông tin chi tiết của 1 creator theo creator_id.
    Lưu vào creator_detail/<creator_id>.json (dedup theo creator_id).

    Returns:
        dict trả về từ get_kalo_data {"added", "skipped", "result"} hoặc None nếu lỗi.
    """
    os.makedirs(CREATORS_DETAIL_DIR, exist_ok=True)

    payload = {
        "region": "VN",
        "language": "vi-VN",
        "currency": "VND",
        "creator_id": creator_id,
        "date_range": "last7Day",
    }
    output_file = os.path.join(CREATORS_DETAIL_DIR, f"{creator_id}.json")
    result = get_kalo_data(
        payload_data=payload,
        url=URL,
        file=output_file,
        id_name="creator_id",
    )
    return result

def scrape_all_creator_details():
    """
    Đọc danh sách creator từ creators.json,
    lần lượt gọi get_creator_detail() cho từng creator.
    Bỏ qua những creator đã có file detail (dedup xử lý bên trong get_creator_detail).
    """
    if not os.path.exists(CREATORS_FILE):
        print(f"[detail] File '{CREATORS_FILE}' chưa tồn tại, bỏ qua bước lấy detail.")
        return

    with open(CREATORS_FILE, "r", encoding="utf-8") as f:
        creators = json.load(f)

    if not isinstance(creators, list) or len(creators) == 0:
        print("[detail] Danh sách creator rỗng, bỏ qua.")
        return

    print("\n" + "=" * 50)
    print(f"Bắt đầu lấy chi tiết {len(creators)} creator...")
    print("=" * 50)

    success = 0
    failed = 0
    for idx, creator in enumerate(creators, 1):
        creator_id = creator.get("creator_id")
        nickname = creator.get("creator_nickname", "?")

        if not creator_id:
            print(f"[detail] [{idx}/{len(creators)}] Bỏ qua: không có creator_id")
            continue

        print(f"\n[detail] [{idx}/{len(creators)}] {nickname} (ID: {creator_id})")
        resp = get_creator_detail(creator_id)

        if resp is None:
            print(f"[detail] THẤT BẠI: {creator_id}")
            failed += 1
        else:
            success += 1

    print("\n" + "=" * 50)
    print(f"Hoàn tất lấy detail! Thành công: {success} | Thất bại: {failed}")
    print("=" * 50)
