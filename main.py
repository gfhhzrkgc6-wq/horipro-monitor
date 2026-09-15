import hashlib
import os
import time
from datetime import datetime
import requests
from playwright.sync_api import sync_playwright

# --- 設定情報 ---
TARGET_URL = "https://www.s2.e-get.jp/web5ap04b/pt2/s2smethodseat.act?s.nonce=96508F2DCDC4B3ACBD1EA40A9EA981E9&p=c86b35ff294bed1ceee8cda02b57630479fce5c3c93557efd786105e43245d3c_16a36e86f6fed5d465ff332511a0ce1a863b55d364b25a7cdaa25db19abf9648&l=c86b35ff294bed1ceee8cda02b57630479fce5c3c93557efd786105e43245d3c"

# ★ ホリプロのログイン情報 ★
USER_ID = "Test1111"
USER_PASS = "1111test"

CACHE_FILE = "previous_horipro_status.txt"
CHECK_INTERVAL_SECONDS = 3600  # 1時間間隔（バン防止）

# LINE設定
LINE_USER_ID = "Uf42850e037063f6fd4344d172856affd"
LINE_CHANNEL_ACCESS_TOKEN = "XkfQ3KCOeDip6oXPo2OAp1+u8HIF98ZACofmt8RN3sz2PnQ11TFwgwvMFMlUC23f1QMfMCClCnZ79dsWyIp0ajWrw4+MhKWTvurDqkmueVmQGTs8RP3REMOGvkkl0BjMLDibkqp9Y/I0HrIRhfto6AdB04t89/1O/w1cDnyilFU="


def send_line_notification(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
    }
    payload = {"to": LINE_USER_ID, "messages": [{"type": "text", "text": message}]}
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print("-> LINE通知送信完了")
    except Exception as e:
        print(f"LINE通知エラー: {e}")


def is_active_hours():
    """現在時刻が 7:00 〜 21:00 の間かどうか判定"""
    current_hour = datetime.now().hour
    return 7 <= current_hour < 21


def get_login_ticket_inventory():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()

        try:
            page.goto(TARGET_URL, wait_until="networkidle", timeout=30000)

            # ログイン画面が表示されている場合は自動ログイン
            if page.locator("input[type='password']").is_visible():
                page.fill("input[type='text']", USER_ID)
                page.fill("input[type='password']", USER_PASS)
                page.click("input[type='submit'], button[type='submit']")
                page.wait_for_load_state("networkidle")

            content = page.locator("body").text_content()
            browser.close()
            return content.strip() if content else None

        except Exception as e:
            print(f"取得エラー: {e}")
            browser.close()
            return None


def check_for_updates():
    if not is_active_hours():
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 稼働時間外（7:00〜21:00のみ稼働）のためスキップします。")
        return

    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ホリプロページを確認中...")
    current_text = get_login_ticket_inventory()

    if not current_text:
        print("データ取得失敗のためスキップ")
        return

    current_hash = hashlib.md5(current_text.encode("utf-8")).hexdigest()

    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            previous_hash = f.read()

        if current_hash != previous_hash:
            msg = f"【ホリプロチケット更新検知】\n座席・在庫状況が更新されました！\n\n{TARGET_URL}"
            print(msg)
            send_line_notification(msg)

            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                f.write(current_hash)
        else:
            print("更新なし")
    else:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(current_hash)
        print("初回チェック完了")


if __name__ == "__main__":
    print("=== ホリプロ 監視プログラム開始 ===")
    send_line_notification("【ホリプロ】安全モード（7:00〜21:00・1時間間隔）で監視を開始しました！")

    while True:
        check_for_updates()
        time.sleep(CHECK_INTERVAL_SECONDS)
