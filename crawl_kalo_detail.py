"""
kalodata_detail.py

Gửi POST request trực tiếp tới https://www.kalodata.com/creator/detail
với cookie từ kalodata_cookies.json (đăng nhập qua browser),
lưu toàn bộ JSON response vào creators_detail.json.

Usage:
  python kalodata_detail.py <creator_id>   # single creator
  python kalodata_detail.py --all          # all creators from creators.json
"""

import json
import random
import sys
import time
from pathlib import Path
import requests
from gemini import normalize_with_gemini

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR             = Path(__file__).parent
COOKIES_TXT_FILE     = BASE_DIR / "kalodata_cookies.txt"   # cookie string từ toolsngon
CREATORS_FILE        = BASE_DIR / "creators.json"
CREATORS_DETAIL_FILE = BASE_DIR / "creators_detail.json"

# ── API ───────────────────────────────────────────────────────────────────────
DETAIL_URL = "https://www.kalodata.com/creator/detail"

START_DATE = "2026-09-19"
END_DATE   = "2026-10-18"

HEADERS = {
    "accept":       "application/json, text/plain, */*",
    "content-type": "application/json",
    "country":      "VN",
    "currency":     "VND",
    "language":     "en-US",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}


# ── Helpers ───────────────────────────────────────────────────────────────────
def _parse_cookie_string(s: str) -> dict:
    """Parse 'key=val; key2=val2' → dict."""
    cookies = {}
    for part in s.split(";"):
        part = part.strip()
        if "=" in part:
            k, _, v = part.partition("=")
            cookies[k.strip()] = v.strip()
    return cookies


def _load_cookies() -> dict:
    """Đọc cookie string từ kalodata_cookies.txt (lấy từ toolsngon hoặc DevTools)."""
    if not COOKIES_TXT_FILE.exists():
        print(f"[error] Không tìm thấy {COOKIES_TXT_FILE}")
        print("[error] Hãy lấy cookie từ toolsngon và lưu vào kalodata_cookies.txt")
        return {}

    raw = COOKIES_TXT_FILE.read_text(encoding="utf-8-sig").strip()
    if not raw:
        print("[error] kalodata_cookies.txt rỗng!")
        return {}

    cookies = _parse_cookie_string(raw)
    print(f"Cookies loaded: {len(cookies)}")
    return cookies


def _load_existing() -> list:
    if not CREATORS_DETAIL_FILE.exists():
        return []
    try:
        with open(CREATORS_DETAIL_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def _save(records: list):
    with open(CREATORS_DETAIL_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def _load_creators() -> list:
    if not CREATORS_FILE.exists():
        print(f"[error] {CREATORS_FILE} not found.")
        return []
    with open(CREATORS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data if isinstance(data, list) else []


# ── Core: gửi POST request ────────────────────────────────────────────────────
def _fetch(creator_id: str, cookies: dict) -> dict | None:
    payload = {
        "id":        creator_id,
        "cateIds":   [],
        "startDate": START_DATE,
        "endDate":   END_DATE,
        "sellerId":  "",
        "authority": True,
    }

    try:
        resp = requests.post(
            DETAIL_URL,
            headers=HEADERS,
            cookies=cookies,
            json=payload,
            timeout=30,
        )
        print(f"  [http] {resp.status_code} {resp.url}")

        if resp.status_code != 200:
            print(f"  [error] HTTP {resp.status_code}: {resp.text[:200]}")
            return None

        body = resp.json()
        success = body.get("success") if isinstance(body, dict) else None
        print(f"  [api]  success={success}")

        if not success:
            msg = body.get("message") or body.get("msg") or ""
            print(f"  [api]  message={msg}")
            return None

        return body

    except requests.exceptions.RequestException as e:
        print(f"  [error] Request failed: {e}")
        return None


# ── Gemini contact enrichment ─────────────────────────────────────────────────
_gemini_exhausted = False  # True khi đã bị rate limit 429


def _enrich_contact(record: dict) -> dict:
    """Gọi Gemini để trích xuất zalo/email từ signature nếu các trường còn rỗng."""
    global _gemini_exhausted

    if _gemini_exhausted:
        return record  # Đã hết quota, bỏ qua

    zalo  = record.get("zalo", "") or ""
    email = record.get("email", "") or ""

    # Chỉ gọi Gemini khi ít nhất 1 trong 2 trường rỗng
    if zalo and email:
        return record

    signature = record.get("signature", "") or ""
    if not signature.strip():
        return record

    print(f"  [gemini] Trích xuất contact từ signature...")
    try:
        contact = normalize_with_gemini(signature)
    except Exception as e:
        err = str(e)
        if "429" in err or "RESOURCE_EXHAUSTED" in err:
            print("  [gemini] ⚠️  Rate limit 429 — tắt Gemini cho session này.")
            _gemini_exhausted = True
        else:
            print(f"  [gemini] Lỗi: {e}")
        return record

    if contact is None:
        return record

    updated = False
    if not zalo and contact.contact_zalo:
        record["zalo"] = contact.contact_zalo
        print(f"  [gemini] zalo ← {contact.contact_zalo}")
        updated = True
    if not email and contact.contact_email:
        record["email"] = contact.contact_email
        print(f"  [gemini] email ← {contact.contact_email}")
        updated = True

    if not updated:
        print("  [gemini] Không tìm thấy thông tin liên hệ trong signature.")

    return record



# ── Save ──────────────────────────────────────────────────────────────────────
def _save_one(creator_id: str, body: dict, records: list, existing_ids: set) -> bool:
    data = body.get("data", body)

    if creator_id in existing_ids:
        print(f"  [skip] {creator_id} already exists.")
        return False

    record = data if isinstance(data, dict) else {"raw": data}
    if isinstance(record, dict) and "creator_id" not in record:
        record = {"creator_id": creator_id, **record}

    # Enrich contact via Gemini nếu thiếu zalo/email
    record = _enrich_contact(record)

    records.append(record)
    existing_ids.add(creator_id)
    _save(records)
    print(f"  [saved] {creator_id}  (total: {len(records)})")
    return True



# ── Public API ────────────────────────────────────────────────────────────────
def get_detail(creator_id: str) -> dict | None:
    print(f"\n{'='*50}")
    print(f"Fetching: {creator_id}")
    print(f"POST → {DETAIL_URL}")
    print(f"{'='*50}")

    cookies = _load_cookies()
    print(f"Cookies loaded: {len(cookies)}")

    body = _fetch(creator_id, cookies)
    if body is None:
        return None

    records      = _load_existing()
    existing_ids = {r.get("creator_id") for r in records if isinstance(r, dict)}
    _save_one(creator_id, body, records, existing_ids)
    return body


# ── Delays ────────────────────────────────────────────────────────────────
DELAY_MIN = 1.0   # giây tối thiểu giữa mỗi request
DELAY_MAX = 3.0   # giây tối đa giữa mỗi request


def _random_sleep():
    delay = random.uniform(DELAY_MIN, DELAY_MAX)
    print(f"  [sleep] {delay:.1f}s...")
    time.sleep(delay)


def scrape_all():
    creators     = _load_creators()
    records      = _load_existing()
    existing_ids = {r.get("creator_id") for r in records if isinstance(r, dict)}
    cookies      = _load_cookies()

    todo = [c for c in creators if c.get("creator_id") not in existing_ids]

    print(f"\nTotal  : {len(creators)}")
    print(f"Saved  : {len(existing_ids)}")
    print(f"Todo   : {len(todo)}")
    print(f"Cookies: {len(cookies)}")
    print(f"Delay  : {DELAY_MIN}–{DELAY_MAX}s between requests")

    success = failed = 0
    for idx, creator in enumerate(todo, 1):
        cid  = creator.get("creator_id")
        nick = creator.get("creator_nickname", "?")
        print(f"\n[{idx}/{len(todo)}] {nick} ({cid})")

        body = _fetch(cid, cookies)
        if body:
            ok = _save_one(cid, body, records, existing_ids)
            if ok:
                success += 1
        else:
            print("  [failed] No data.")
            failed += 1

        # Random delay sau mỗi request (kể cả request cuối)
        if idx < len(todo):
            _random_sleep()

    print(f"\n{'='*50}")
    print(f"Done — success: {success}  failed: {failed}")
    print(f"{'='*50}")


# ── Google Sheets upload ──────────────────────────────────────────────────────
def save_to_sheet(sheet_name: str = "creators_detail"):
    """Đẩy toàn bộ creators_detail.json lên Google Sheets (dedup theo creator_id)."""
    from sheet import save_to_google_sheet
    print(f"\n[sheet] Đang upload lên sheet '{sheet_name}'...")
    save_to_google_sheet(
        json_file=str(CREATORS_DETAIL_FILE),
        sheet_name=sheet_name,
        id_name="creator_id",
    )


# ── Main: chạy thử N KOC đầu tiên ───────────────────────────────────────────
def main(limit: int = 50, sheet_name: str = "creators_detail"):
    """
    Scrape `limit` KOC đầu tiên chưa có trong creators_detail.json,
    sau đó đẩy toàn bộ dữ liệu lên Google Sheets.
    """
    creators     = _load_creators()
    records      = _load_existing()
    existing_ids = {r.get("creator_id") for r in records if isinstance(r, dict)}
    cookies      = _load_cookies()

    todo = [c for c in creators if c.get("creator_id") not in existing_ids]
    todo = todo[:limit]  # Chỉ lấy limit KOC đầu tiên chưa có

    print(f"\n{'='*50}")
    print(f"Main — chạy thử {limit} KOC đầu tiên")
    print(f"{'='*50}")
    print(f"Total creators : {len(creators)}")
    print(f"Already saved  : {len(existing_ids)}")
    print(f"To fetch       : {len(todo)}")
    print(f"Cookies loaded : {len(cookies)}")
    print(f"Delay          : {DELAY_MIN}–{DELAY_MAX}s between requests")

    success = failed = 0
    for idx, creator in enumerate(todo, 1):
        cid  = creator.get("creator_id")
        nick = creator.get("creator_nickname", "?")
        print(f"\n[{idx}/{len(todo)}] {nick} ({cid})")

        body = _fetch(cid, cookies)
        if body:
            ok = _save_one(cid, body, records, existing_ids)
            if ok:
                success += 1
        else:
            print("  [failed] No data.")
            failed += 1

        if idx < len(todo):
            _random_sleep()

    print(f"\n{'='*50}")
    print(f"Scrape xong — success: {success}  failed: {failed}")
    print(f"{'='*50}")

    # Đẩy lên Google Sheets
    save_to_sheet(sheet_name=sheet_name)


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Không có arg → chạy main mặc định 50 KOC
        main(limit=50)
    elif sys.argv[1] == "--all":
        scrape_all()
    elif sys.argv[1] == "--main":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        main(limit=limit)
    elif sys.argv[1] == "--sheet":
        save_to_sheet()
    else:
        get_detail(sys.argv[1])