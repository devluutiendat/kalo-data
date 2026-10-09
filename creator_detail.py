import os
from kalo import get_kalo_data

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