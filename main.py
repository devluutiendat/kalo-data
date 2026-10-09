import sys
import json
import os
from search import search_categories
from creators import get_creator_list
from creator_detail import get_creator_detail

CREATORS_FILE = "creators.json"

# Đảm bảo in tiếng Việt chuẩn UTF-8 trên Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def scrape_all_creators():
    """
    Chạy liên tục get_creator_list() qua từng trang cho đến khi
    không thêm được item mới nào (added == 0).
    """
    page = 1
    total_added = 0

    print("\n" + "=" * 50)
    print("Bắt đầu thu thập danh sách Creator...")
    print("=" * 50)

    while True:
        added = get_creator_list(page_number=page)

        if added == 0:
            print(f"\n[main] Trang {page}: Không có item mới → Dừng vòng lặp.")
            break

        total_added += added
        print(f"[main] Trang {page}: +{added} creator mới (tổng đã thêm: {total_added})")
        page += 1

    print("\n" + "=" * 50)
    print(f"Hoàn tất! Tổng số creator mới thêm: {total_added}")
    print("=" * 50)


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


def main():
    # Lấy từ khóa từ tham số dòng lệnh hoặc nhập từ bàn phím
    if len(sys.argv) > 1:
        keyword = " ".join(sys.argv[1:])
    else:
        keyword = input("Nhập từ khóa tìm kiếm danh mục (ví dụ: áo, váy, gia dụng...): ").strip()

    if not keyword:
        print("Chưa nhập từ khóa tìm kiếm.")
        return

    # --- Bước 1: Tìm kiếm danh mục ---
    print(f"\nĐang tìm kiếm danh mục với từ khóa: '{keyword}'...")
    results = search_categories(keyword)

    print(f"=> Tìm thấy {len(results)} kết quả phù hợp:\n")
    for idx, item in enumerate(results, 1):
        cat_id = item.get("TikTok Category ID")
        name = item.get("Tên danh mục")
        parent = item.get("Danh mục cha") or "Gốc"
        is_leaf = "Có" if item.get("Là danh mục lá") else "Không"
        print(f"{idx:>3}. [ID: {cat_id}] {name}")
        print(f"     Danh mục cha: {parent} | Danh mục lá: {is_leaf}")

    if not results:
        print("Không tìm thấy danh mục nào phù hợp, dừng lại.")
        return

    # --- Bước 2: Thu thập danh sách Creator liên tục cho đến khi hết trang ---
    scrape_all_creators()

    # --- Bước 3: Lấy chi tiết từng Creator trong creators.json ---
    scrape_all_creator_details()


if __name__ == "__main__":
    main()
