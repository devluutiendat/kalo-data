import sys
from playwright.async_api import async_playwright
import json
import os

CREATORS_FILE = "creators.json"

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

async def crawl_tiktok_bio(creator_handle, id):
    async with async_playwright() as p:
        # Khởi động trình duyệt (headless=False nếu bạn muốn nhìn thấy trình duyệt chạy)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        if not os.path.exists(CREATORS_FILE):
            print(f"[detail] File '{CREATORS_FILE}' chưa tồn tại, bỏ qua bước lấy detail.")
            return

        with open(CREATORS_FILE, "r", encoding="utf-8") as f:
            creators = json.load(f)

        if not isinstance(creators, list) or len(creators) == 0:
            print("[detail] Danh sách creator rỗng, bỏ qua.")
            return 
        if not creator_handle:
            print(f"[detail] [{id}] Bỏ qua: không có creator_handle")
            return
            
        try:
            # Truy cập vào trang web
            await page.goto(f"https://www.tiktok.com/{creator_handle}")
            
            bio_locator = page.locator('h2[data-e2e="user-bio"]')
            await bio_locator.wait_for(state="visible", timeout=5000)
            
            # Nếu tìm thấy, lấy text thành công 
            bio_text = await bio_locator.inner_text()
            print("Bio TikTok:", bio_text)
            return bio_text
        except Exception as e:
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            
            # Lấy toàn bộ mã nguồn HTML hiện tại của trang
            html_content = await page.content()
            
            # Đường dẫn file lưu HTML
            file_path = os.path.join(output_dir, f"{creator_handle}_error_screenshot.html")
            
            # Ghi HTML ra file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)
                    
            print(f"Đã lưu toàn bộ HTML vào: {file_path}")
            
            # (Tùy chọn) Chụp ảnh màn hình lúc lỗi để xem TikTok đang hiện cái gì (Captcha/Login)
            await page.screenshot(path=os.path.join(output_dir, f"{creator_handle}_error_screenshot.png"))
            print("Đã lưu ảnh chụp màn hình vào thư mục output.")
            
        await browser.close()

