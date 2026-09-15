import os
import time
import threading
import requests
import schedule
from flask import Flask
from playwright.sync_api import sync_playwright

# --- 1. Renderの無料プラン（Web Service）対策の簡易サーバー ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Horipro Monitor is running!"

def run_web_server():
    # Renderから割り当てられるポート（環境変数 PORT）を使用（デフォルトは10000）
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# 別スレッドでWebサーバーを常時起動しつつ、メインの監視処理を動かす
def start_server_in_background():
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()
# -------------------------------------------------------------

# LINE Notify トークン（環境変数から取得）
LINE_NOTIFY_TOKEN = os.getenv("LINE_NOTIFY_TOKEN")
TARGET_URL = "https://horipro-stage.jp/"  # 監視対象のURL

def send_line_notify(message):
    if not LINE_NOTIFY_TOKEN:
        print("LINE_NOTIFY_TOKEN が設定されていません")
        return
    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": f"Bearer {LINE_NOTIFY_TOKEN}"}
    data = {"message": message}
    requests.post(url, headers=headers, data=data)

def check_website():
    print("Webサイトの監視チェックを開始します...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(TARGET_URL, timeout=60000)
            
            # ここでサイトのチェック処理を実行
            title = page.title()
            print(f"取得タイトル: {title}")
            
            browser.close()
            send_line_notify(f"\n【定期チェック】\nサイトの確認が完了しました！\nタイトル: {title}")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        send_line_notify(f"\n【エラー発生】\n監視処理中にエラーが発生しました:\n{e}")

if __name__ == "__main__":
    # Webサーバーをバックグラウンドで起動
    start_server_in_background()

    # 毎時 05 分に実行するスケジュール設定
    schedule.every().hour.at(":05").do(check_website)

    print("監視プログラムを起動しました。毎時05分に実行します...")

    # 起動時に1回確認
    check_website()

    # 定期実行ループ
    while True:
        schedule.run_pending()
        time.sleep(30)
