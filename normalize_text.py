import re
import unicodedata
import emoji


def clean_and_normalize_text(text: str) -> str:
  # 1. Bảng ánh xạ các emoji số và ký tự lách luật phổ biến
  number_mapping = {
      '0️⃣': '0',
      '1️⃣': '1',
      '2️⃣': '2',
      '3️⃣': '3',
      '4️⃣': '4',
      '5️⃣': '5',
      '6️⃣': '6',
      '7️⃣': '7',
      '8️⃣': '8',
      '9️⃣': '9',
      '🔟': '10',
  }

  # Thay thế emoji số trước
  for keycap, digit in number_mapping.items():
    text = text.replace(keycap, digit)

  # 2. Xóa tất cả các emoji trang trí còn lại (🩴, 💼, ✨, 🔥,...)
  text = emoji.replace_emoji(text, replace='')

  # 3. Chuẩn hóa Unicode
  text = unicodedata.normalize('NFKC', text)

  # 4. Xử lý trường hợp lách luật thay 'o'/'O' thành '0' trong chuỗi số
  # Tìm các cụm có dạng số kết hợp chữ o/O (VD: o9o5 -> 0905)
  def replace_o_in_phone(match):
    return match.group(0).replace('o', '0').replace('O', '0')

  # Regex tìm cụm chứa từ 8-11 ký tự gồm số và chữ o/O đứng cạnh nhau
  text = re.sub(
      r'\b(?=[a-zA-Z0-9]*[0-9])[a-zA-Z0-9]{8,12}\b', replace_o_in_phone, text
  )

  # 5. Làm sạch khoảng trắng thừa
  cleaned_text = ' '.join(text.split())

  return cleaned_text


# --- Thử nghiệm ---
sample_1 = (
    "Cả nhà giúp em 1 fl với 🩴💼✨🔥: o9o51️⃣8️⃣2️⃣20️⃣2 ib em nha ❤️"
)
sample_2 = "Shop bán áo giá 150k 👗👠 liên hệ 0️⃣9️⃣1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣8️⃣ 🎉"

print("Đầu vào 1:", sample_1)
print("Sau xử lý:", clean_and_normalize_text(sample_1))
print("-" * 50)
print("Đầu vào 2:", sample_2)
print("Sau xử lý:", clean_and_normalize_text(sample_2))