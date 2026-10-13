import json
import os
from kalo import get_kalo_data
from gemini import normalize_with_gemini

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
    
    payload = {
        "region": "VN",
        "language": "vi-VN",
        "currency": "VND",
        "creator_id": creator_id,
        "date_range": "last7Day",
    }
    result = get_kalo_data(
        payload_data=payload,
        url=URL,
        file="creator_detail.json",
        id_name="creator_id",
    )

    if result and result.get("added", 0) > 0:
        raw_data = result.get("result", {}).get("data", {})
        if isinstance(raw_data, dict):
            zalo = raw_data.get("creator_contact_zalo", "")
            email = raw_data.get("creator_contact_email", "")
            bio = raw_data.get("creator_bio", "")

            if (not zalo or not email) and bio:
                print(f"[gemini] Thiếu contact (zalo='{zalo}', email='{email}'), trích xuất từ bio...")
                contact = normalize_with_gemini(bio)
                if contact:
                    # Cập nhật lại file JSON với thông tin Gemini trích xuất được
                    _update_creator_contact(
                        file="creator_detail.json",
                        creator_id=creator_id,
                        gemini_zalo=contact.contact_zalo,
                        gemini_email=contact.contact_email,
                    )

    return result

def _update_creator_contact(file: str, creator_id: str, gemini_zalo: str | None, gemini_email: str | None):
    """
    Đọc file JSON, tìm creator theo creator_id,
    ghi bổ sung giá trị Gemini vào creator_contact_zalo và creator_contact_email
    nếu field đó đang rỗng.
    """
    if not os.path.exists(file):
        return
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
    for item in data:
        if item.get("creator_id") == creator_id:
            if gemini_zalo and not item.get("creator_contact_zalo"):
                item["creator_contact_zalo"] = gemini_zalo
                print(f"[gemini] Đã cập nhật creator_contact_zalo: {gemini_zalo}")
            if gemini_email and not item.get("creator_contact_email"):
                item["creator_contact_email"] = gemini_email
                print(f"[gemini] Đã cập nhật creator_contact_email: {gemini_email}")
            break
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


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

get_creator_detail("6705337685530117121")