import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Union
import pandas as pd

# Đảm bảo in tiếng Việt trên console Windows không bị lỗi font / mã hóa charmap
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Đường dẫn mặc định đến file Excel danh mục TikTok Shop
DEFAULT_EXCEL_PATH = Path(__file__).resolve().parent / "TikTok Shop Category (cache-on-demand) (tiktok.category).xlsx"

# Biến cache dữ liệu để không phải đọc lại file Excel nhiều lần
_CACHED_DF: Union[pd.DataFrame, None] = None


def load_category_data(file_path: Union[str, Path] = DEFAULT_EXCEL_PATH, reload: bool = False) -> pd.DataFrame:
    """
    Đọc dữ liệu từ file Excel danh mục TikTok Shop.
    Sử dụng cache để tối ưu tốc độ cho các lần tìm kiếm tiếp theo.
    """
    global _CACHED_DF
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy file Excel tại: {path}")

    if _CACHED_DF is None or reload:
        _CACHED_DF = pd.read_excel(path)

    return _CACHED_DF


def search_categories(
    x: str,
    file_path: Union[str, Path] = DEFAULT_EXCEL_PATH,
    case_sensitive: bool = False,
    as_dict: bool = True
) -> Union[List[Dict[str, Any]], pd.DataFrame]:
    """
    Tìm kiếm chuỗi `x` trong 2 cột:
    - 'Tên danh mục'
    - 'Danh mục cha'

    Args:
        x (str): Chuỗi từ khóa cần tìm kiếm.
        file_path (Union[str, Path]): Đường dẫn tới file Excel.
        case_sensitive (bool): Phân biệt chữ hoa/thường (mặc định False).
        as_dict (bool): Nếu True trả về danh sách các dict (list of rows), 
                        nếu False trả về DataFrame.

    Returns:
        List[Dict[str, Any]] hoặc pd.DataFrame: Danh sách các dòng phù hợp.
    """
    if not x or not str(x).strip():
        return [] if as_dict else pd.DataFrame()

    query = str(x).strip()
    df = load_category_data(file_path)

    # Chuẩn hóa chuỗi và xử lý NaN để tránh tìm nhầm chữ 'nan'
    category_name_series = df["Tên danh mục"].fillna("").astype(str)
    parent_category_series = df["Danh mục cha"].fillna("").astype(str)

    # Lọc các dòng có chứa `x` trong 'Tên danh mục' HOẶC 'Danh mục cha'
    # regex=False để các ký tự đặc biệt như (), [], +, * không gây lỗi regex
    mask = (
        category_name_series.str.contains(query, case=case_sensitive, regex=False)
        | parent_category_series.str.contains(query, case=case_sensitive, regex=False)
    )

    result_df = df[mask].copy()

    # Sắp xếp: Đưa các dòng có 'Là danh mục lá' = False lên đầu danh sách
    leaf_col = "Là danh mục lá"
    if leaf_col in result_df.columns and not result_df.empty:
        # 0 cho False (lên đầu danh sách), 1 cho True (ở phía sau)
        # Sử dụng stable sort để giữ nguyên thứ tự tương đối ban đầu giữa các dòng cùng nhóm
        sort_key = result_df[leaf_col].apply(
            lambda v: 0 if (v is False or str(v).strip().lower() in ("false", "0")) else 1
        )
        result_df = result_df.iloc[sort_key.argsort(kind="stable")].copy()

    if as_dict:
        # Chuyển đổi Timestamp / NaT sang dạng string hoặc None dễ dùng
        records = result_df.to_dict(orient="records")
        for row in records:
            for k, v in row.items():
                if pd.isna(v):
                    row[k] = None
                elif isinstance(v, pd.Timestamp):
                    row[k] = str(v)
        return records

    return result_df


# Tạo alias ngắn gọn `search` cho hàm `search_categories`
search = search_categories



def main():
    print("=" * 60)
    print(" CÔNG CỤ TÌM KIẾM DANH MỤC TIKTOK SHOP")
    print("=" * 60)
    print(f"File nguồn: {DEFAULT_EXCEL_PATH.name}\n")

    # Tải trước dữ liệu
    print("Đang đọc dữ liệu Excel...")
    df = load_category_data()
    print(f"Đã tải thành công {len(df)} danh mục.\n")

    # Nếu truyền từ khóa qua tham số dòng lệnh (vd: python search.py "váy")
    if len(sys.argv) > 1:
        keyword = " ".join(sys.argv[1:])
        results = search_categories(keyword, as_dict=True)
        print(f"Tìm thấy {len(results)} kết quả phù hợp với từ khóa '{keyword}':\n")
        for i, row in enumerate(results, 1):
            print(f"{i}. [ID: {row.get('TikTok Category ID')}]")
            print(f"   - Tên danh mục: {row.get('Tên danh mục')}")
            print(f"   - Danh mục cha: {row.get('Danh mục cha')}")
            print(f"   - Là danh mục lá: {row.get('Là danh mục lá')}")
            print("-" * 50)
        return

    # Chế độ tương tác nhập từ bàn phím
    while True:
        try:
            x = input("\nNhập từ khóa cần tìm (hoặc gõ 'q' để thoát): ").strip()
            if not x:
                continue
            if x.lower() in ("q", "quit", "exit"):
                print("Đã thoát chương trình.")
                break

            results = search_categories(x, as_dict=True)
            print(f"\n=> Tìm thấy {len(results)} dòng phù hợp với '{x}':")
            if results:
                for i, row in enumerate(results, 1):
                    parent = row.get("Danh mục cha") or "Không có"
                    is_leaf = row.get("Là danh mục lá")
                    tag = "[DANH MỤC GỐC/CHA]" if (is_leaf is False or str(is_leaf).lower() == "false") else "[LÁ]"
                    print(f"{i:>3}. {tag} [ID: {row.get('TikTok Category ID')}] {row.get('Tên danh mục')} | Cha: {parent}")
            else:
                print("Không có danh mục nào khớp với từ khóa tìm kiếm.")
        except (KeyboardInterrupt, EOFError):
            print("\nĐã dừng chương trình.")
            break


if __name__ == "__main__":
    main()
