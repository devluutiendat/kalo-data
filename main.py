from creators import scrape_all_creators
from creator_detail import scrape_all_creator_details
import sys
from search import search_categories

CREATORS_FILE = "creators.json"

# Đảm bảo in tiếng Việt chuẩn UTF-8 trên Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

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
    # Cho user chọn category ID muốn cào
    print("\nNhập STT danh mục muốn cào (cách nhau bằng dấu phẩy, ví dụ: 1,3).")
    print("Để trống và nhấn Enter → lấy tất cả danh mục lá (Là danh mục lá = True):")
    raw_input = input("Chọn: ").strip()

    if raw_input:
        try:
            chosen_indices = [int(x.strip()) - 1 for x in raw_input.split(",")]
            selected = [results[i] for i in chosen_indices if 0 <= i < len(results)]
        except (ValueError, IndexError):
            print("[WARN] Lựa chọn không hợp lệ, lấy tất cả danh mục lá.")
            selected = [r for r in results if r.get("Là danh mục lá")]
    else:
        selected = [r for r in results if r.get("Là danh mục lá")]
        if not selected:
            selected = results  # fallback nếu không có danh mục lá nào

    category_ids = [item.get("TikTok Category ID") for item in selected if item.get("TikTok Category ID")]

    print(f"\nĐang cào {len(category_ids)} danh mục: {[item.get('Tên danh mục') for item in selected]}")
    scrape_all_creators(category_ids)

    # --- Bước 3: Lấy chi tiết từng Creator trong creators.json ---
    scrape_all_creator_details()

if __name__ == "__main__":
    main()
