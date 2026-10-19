
import time
import json
import requests
from dotenv import load_dotenv
import os
from typing import Literal
from sheet import log_zalo_status

load_dotenv()

CREATORS_DETAIL_FILE = "creator_detail.json"
BASE_URL = os.getenv("ERP_BASE_URL")
API_KEY = os.getenv("API_KEY_ERP")

def check_zalo_by_phone(phone_number: str, zalo_account_id: int = None):
  """Gọi API tra cứu tài khoản Zalo theo số điện thoại[cite: 1]."""
  endpoint = f"{BASE_URL}/api/v1/booking/zalo/lookup"

  headers = {
      "Authorization": f"Bearer {API_KEY}",
      "Content-Type": "application/json",
  }

  # Xây dựng payload theo chuẩn tài liệu API[cite: 1]
  payload = {"phone": phone_number}

  # Thêm zalo_account_id nếu có chỉ định (tùy chọn)[cite: 1]
  if zalo_account_id is not None:
    payload["zalo_account_id"] = zalo_account_id

  try:
    response = requests.post(endpoint, json=payload, headers=headers)

    # Kiểm tra mã phản hồi HTTP
    if response.status_code == 200:
      data = response.json()
      return data
    elif response.status_code == 400:
      print(
          "Lỗi 400: Số điện thoại không hợp lệ hoặc thiếu tài khoản Zalo [cite:"
          " 1]."
      )
    elif response.status_code == 401:
      print("Lỗi 401: Xác thực thất bại hoặc API key không hợp lệ[cite: 1].")
    else:
      print(f"Lỗi không xác định: {response.status_code} - {response.text}")

    return None

  except Exception as e:
    print(f"Lỗi kết nối đến server: {e}")
    return None

def send_zalo_messager(phone_number:str, message: str, action_type: Literal["friend_request", "message"] = "message", zalo_account_id: int = None, creator_id : int =None):
  endpoint = f"{BASE_URL}/api/v1/booking/zalo/send"

  headers = {
      "Authorization": f"Bearer {API_KEY}",
      "Content-Type": "application/json",
  }

  payload = {
      "phone": phone_number,
      "text": message,
      "action_type": action_type,
  }


  if zalo_account_id is not None:
    payload["zalo_account_id"] = zalo_account_id

  if creator_id is not None:
    payload["creator_id"] = creator_id

  try:
    response = requests.post(endpoint, json=payload, headers=headers)
    return response.json()
  except Exception as e:
    print(f"Lỗi kết nối đến server: {e}")
    return None

def multi_send_zalo_messager():

    if not os.path.exists(CREATORS_DETAIL_FILE):
        print(f"[detail] File '{CREATORS_DETAIL_FILE}' chưa tồn tại.")
        return

    with open(CREATORS_DETAIL_FILE, "r", encoding="utf-8") as f:
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
        phone_number = creator.get("creator_contact_zalo") or "0325933782"
        nickname = creator.get("creator_nickname")
        if not phone_number:
          print(f"[detail] [{idx}/{len(creators)}] Bỏ qua: creator {nickname} không có sđt")
          continue
        try:
          is_esxit = check_zalo_by_phone(phone_number)
        except Exception as e:
          log_zalo_status(nickname, "Số không tồn tại trên Zalo", False)
          print(f"[detail] [{idx}/{len(creators)}] creator {nickname} không có zalo")
          continue

        print(f"\n[detail] [{idx}/{len(creators)}] {nickname} : {phone_number}")
        messager = f"chào {nickname}"
        try:  
          resp = send_zalo_messager(phone_number, messager )
          log_zalo_status(nickname, "Đã liên hệ", True)
          time.sleep(1)
        except Exception as e:
          log_zalo_status(nickname,  f"Lỗi gửi tin nhắn: {e}", False)
          print(f"Lỗi gửi tin nhắn: {e}")
          failed += 1

        if resp is None:
            print(f"[detail] THẤT BẠI: {nickname} : {phone_number}")
            failed += 1
        else:
            success += 1

    print("\n" + "=" * 50)
    print(f"Hoàn tất gửi tin nhắn Thành công: {success} | Thất bại: {failed}")
    print("=" * 50)


multi_send_zalo_messager()