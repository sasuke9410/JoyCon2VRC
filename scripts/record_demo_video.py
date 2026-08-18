import os
import sys
import time
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = 8085
BASE_DIR = Path(__file__).parent.parent.resolve()
OUTPUT_DIR = BASE_DIR / "dist" / "videos"

class QuietHTTPRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # ログ出力を抑制

def start_server():
    os.chdir(BASE_DIR)
    server = HTTPServer(("127.0.0.1", PORT), QuietHTTPRequestHandler)
    server.serve_forever()

def record_demo():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # バックグラウンドでローカルWEBサーバー起動
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(1)

    print(f"Local server started at http://127.0.0.1:{PORT}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=str(OUTPUT_DIR),
            record_video_size={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        page.goto(f"http://127.0.0.1:{PORT}/index.html")
        page.wait_for_load_state("networkidle")

        # アプリUIをそのまま表示（追加のDOM注入やスタイル変更は一切行いません）

        def hover_and_click(selector, delay=2.0):
            page.hover(selector)
            time.sleep(0.3)
            page.click(selector)
            time.sleep(delay)

        # --- 純粋なアプリ操作シナリオ ---

        # 1. 初期状態の提示 (2秒)
        time.sleep(2.0)

        # 2. テストシミュレーター起動
        hover_and_click("#btnSimulate", delay=3.0)

        # 3. 通常足踏み（歩行テスト）
        hover_and_click("#btnSimWalk", delay=4.0)

        # 4. 通常足踏み（走行テスト）
        hover_and_click("#btnSimRun", delay=4.0)

        # 5. サイレントモード切り替え＆テスト
        hover_and_click("#modeSilent", delay=1.0)
        hover_and_click("#btnSimSilent", delay=4.0)

        # 6. スライダー操作（感度・速度パラメータの調整）
        page.hover("#sliderSens")
        page.evaluate("""() => {
            const slider = document.getElementById('sliderSens');
            slider.value = 0.60;
            slider.dispatchEvent(new Event('input', { bubbles: true }));
        }""")
        time.sleep(2.0)

        page.hover("#sliderRunSpm")
        page.evaluate("""() => {
            const slider = document.getElementById('sliderRunSpm');
            slider.value = 120;
            slider.dispatchEvent(new Event('input', { bubbles: true }));
        }""")
        time.sleep(2.0)

        # 7. OSC連携手順タブ切り替え
        hover_and_click("button[data-tab='osc-guide']", delay=4.0)

        # 8. アルゴリズム解説タブ切り替え
        hover_and_click("button[data-tab='algorithm']", delay=3.0)

        # 9. メインダッシュボードに戻る
        hover_and_click("button[data-tab='dashboard']", delay=3.0)

        # 終了処理
        video_path = page.video.path()
        context.close()
        browser.close()

        # 動画ファイル名のリネーム保存
        if video_path and os.path.exists(video_path):
            target_name = OUTPUT_DIR / "joycon2vrc_app_recording.webm"
            if target_name.exists():
                target_name.unlink()
            os.rename(video_path, target_name)
            print(f"Clean app video saved to: {target_name}")

    print("Pure app recording completed successfully.")

if __name__ == "__main__":
    record_demo()
