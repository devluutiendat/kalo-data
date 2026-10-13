from normalize_text import clean_and_normalize_text
import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Định nghĩa cấu trúc dữ liệu đầu ra mong muốn
class ContactInfo(BaseModel):
  contact_zalo: str | None = Field(None, description="Số điện thoại")
  contact_email: str | None = Field(None, description="Địa chỉ email")


def extract_contact_info(text: str) -> ContactInfo | None:
  """Nhận vào một đoạn text, sử dụng Gemini để phân tích và trả về thông tin liên hệ cấu trúc chuẩn."""
  prompt = f"""
    Hãy phân tích kỹ đoạn văn bản dưới đây và trích xuất toàn bộ thông tin liên hệ có sẵn.
    Nếu thông tin nào không xuất hiện trong văn bản, hãy để giá trị là null.

    Văn bản cần phân tích:
    {text}
    """

  try:
    # Gọi Gemini model với cấu hình Structured Output (JSON Schema từ Pydantic)
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ContactInfo,
            temperature=0.1,  # Nhiệt độ thấp giúp mô hình trích xuất chính xác, ít sáng tạo thừa
        ),
    )

    # response.parsed sẽ trả về trực tiếp đối tượng Pydantic (ContactInfo)
    return response.parsed

  except Exception as e:
    print(f"Lỗi khi gọi API Gemini: {e}")
    return None

def normalize_with_gemini(text: str):
    text = clean_and_normalize_text(text)
    print(f"Đang phân tích văn bản...")
    result = extract_contact_info(text)
    if result:
        print(f"Số điện thoại/Zalo: {result.contact_zalo}")
        print(f"Email: {result.contact_email}")
    return result

#sample 1
text = "Cả nhà giúp em 1 fl với🩴💼: o9o51️⃣8️⃣2️⃣20️⃣2"
normalize_with_gemini(text)

