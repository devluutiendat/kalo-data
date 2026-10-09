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
        return 0

    added = resp.get("added", 0)
    return added