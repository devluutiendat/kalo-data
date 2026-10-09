from kalo import get_kalo_data

URL = "https://www.kalodata.com/openapi/v1/tiktok/creator/rank"
OUTPUT_FILE = "creators.json"

def get_creator_list(page_number: int = 1) -> int:

    """
    Lấy danh sách creator từ Kalodata theo từng trang.

    Args:
        page_number: Số trang cần lấy (bắt đầu từ 1).

    Returns:
        int: Số item mới được thêm vào file trong lần gọi này.
             Trả về 0 nếu không có item mới hoặc xảy ra lỗi.
    """
    payload = {
        "region": "VN",
        "language": "vi-VN",
        "currency": "VND",
        "date_range": "last7Day",
        "sort_field": {
            "field": "revenue",
            "type": "DESC",
        },
        "category_ids": [700785],
        "category_id_list": "700785",
        "page_size": 100,
        "page_number": page_number,
    }

    print(f"\n[creators] Đang lấy trang {page_number}...")
    resp = get_kalo_data(
        payload_data=payload,
        url=URL,
        file=OUTPUT_FILE,
        id_name="creator_id",
    )

    if resp is None:
        print("[creators] Lỗi khi gọi API, dừng lại.")
        return 0, 0

    added = resp.get("added", 0)
    skipped = resp.get("skipped", 0)
    fetched_count = added + skipped
    return added, fetched_count

def scrape_all_creators():
    """
    Chạy liên tục get_creator_list() qua từng trang.
    Điều kiện dừng vòng lặp: lần lấy dữ liệu trước đó có data < 100
    (nghĩa là đã tới trang cuối hoặc không còn dữ liệu trả về từ API).
    """
    page = 1
    total_added = 0

    print("\n" + "=" * 50)
    print("Bắt đầu thu thập danh sách Creator...")
    print("=" * 50)

    while True:
        added, fetched_count = get_creator_list(page_number=page)
        total_added += added
        print(f"[main] Trang {page}: nhận {fetched_count} creator (thêm mới: {added}, tổng mới: {total_added})")

        if fetched_count < 100:
            print(f"\n[main] Trang {page}: Số lượng data nhận về ({fetched_count}) < 100 → Dừng vòng lặp.")
            break

        page += 1

    print("\n" + "=" * 50)
    print(f"Hoàn tất! Tổng số creator mới thêm: {total_added}")
    print("=" * 50)

if __name__ == "__main__":
    scrape_all_creators()