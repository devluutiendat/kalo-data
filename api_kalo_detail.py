from tiktok_crawl import crawl_tiktok_bio
import asyncio
import json
import os
from kalo import get_kalo_data
from gemini import normalize_with_gemini

CREATORS_FILE = "creators.json"
URL = "https://www.kalodata.com/openapi/v1/tiktok/creator/detail"

def get_creator_detail(creator_id: str) -> dict:
    
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
            if (not zalo or not email):
                creator_handle = raw_data.get("creator_handle", "")
                if not bio and creator_handle:
                    bio = asyncio.run(crawl_tiktok_bio(creator_handle, creator_id))
                    update_creator_contact(
                        file="creator_detail.json",
                        creator_id=creator_id,
                        field_name="creator_bio",
                        value=bio,
                    )
                contact = normalize_with_gemini(bio)
                if contact:
                    update_creator_contact(
                        file="creator_detail.json",
                        creator_id=creator_id,
                        field_name="creator_contact_zalo",
                        value=contact.contact_zalo,
                    )
                    update_creator_contact(
                        file="creator_detail.json",
                        creator_id=creator_id,
                        field_name="creator_contact_email",
                        value=contact.contact_email,
                    )
    return result

def update_creator_contact(
    file: str,
    creator_id: str,
    field_name: str,
    value: str
) -> bool:
    if not os.path.exists(file):
        return False

    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data:
        if item.get("creator_id") == creator_id:
            old_value = item.get(field_name)

            if old_value != value:
                item[field_name] = value
                print(
                    f"[update] {field_name}: "
                    f"{old_value!r} -> {value!r}"
                )

                with open(file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

            return True

    return False


def scrape_all_creator_details():
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

if __name__ == "__main__":
    get_creator_detail("7364801654489285650")