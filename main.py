"""
JoyCon2VRC - Standalone Desktop Application (pywebview + PyInstaller)
=====================================================================
・単一 exe ファイルとして全機能（Web UI, Bluetooth全自動検出, OSC/キー送信）を完結
・アプリクローズ時 (Xボタン操作) に VRChat 宛てへ強制移動リセット (0.0) を連打送信する安全フック搭載
"""

import os
import sys
import time
import threading
import webview

from bridge_server import run_server, osc_client, set_keys

# ---------------------------------------------------------------------------
# 1. Resource Path Helper for PyInstaller
# ---------------------------------------------------------------------------
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# ---------------------------------------------------------------------------
# 2. Window Closing Hook for Immediate Emergency Reset
# ---------------------------------------------------------------------------
def on_closing():
    """Triggered instantly when the user clicks the window X button"""
    try:
        set_keys(False, False)
        osc_client.emergency_reset()
        print("[Window Closing] Emergency VRChat Movement Reset Sent")
    except Exception:
        pass

# ---------------------------------------------------------------------------
# 3. Main Entry Point
# ---------------------------------------------------------------------------
def main():
    # Start Bridge Server & Joy-Con Auto Reader Thread
    server_thread = threading.Thread(target=run_server, args=(9011,), daemon=True)
    server_thread.start()
    time.sleep(0.3)

    html_path = get_resource_path("test_app.html")

    window = webview.create_window(
        title="JoyCon2VRC",
        url=html_path,
        width=980,
        height=820,
        resizable=True
    )

    # Attach window closing event handler
    window.events.closing += on_closing

    webview.start(debug=False)

if __name__ == "__main__":
    main()
