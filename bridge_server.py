"""
VRChat HTTP/OSC & Key Bridge Server (Python ゼロ依存)
=====================================================
Webブラウザ (test_app.html) からの HTTP 通信を受け取り、
VRChat Native OSC (UDP 127.0.0.1:9000) および Windows SendInput キー入力へ転送します。
"""

import sys
import time
import struct
import socket
import ctypes
from ctypes import wintypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ---------------------------------------------------------------------------
# 1. OSC Client (Target: 127.0.0.1:9000)
# ---------------------------------------------------------------------------
class OSCClient:
    def __init__(self, ip="127.0.0.1", port=9000):
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def _pad(self, b: bytes) -> bytes:
        return b + b'\x00' * (4 - (len(b) % 4))

    def send_movement(self, speed: float, is_running: bool):
        # /input/Vertical float [-1.0 ~ 1.0]
        addr1 = self._pad(b'/input/Vertical')
        tag1 = self._pad(b',f')
        val1 = struct.pack('>f', float(speed))
        self.sock.sendto(addr1 + tag1 + val1, (self.ip, self.port))

        # /input/Run int [0 or 1]
        addr2 = self._pad(b'/input/Run')
        tag2 = self._pad(b',i')
        val2 = struct.pack('>i', 1 if is_running else 0)
        self.sock.sendto(addr2 + tag2 + val2, (self.ip, self.port))

# ---------------------------------------------------------------------------
# 2. Windows Virtual Key Sender (Fixed Ctypes Union initialization)
# ---------------------------------------------------------------------------
if sys.platform == 'win32':
    user32 = ctypes.windll.user32
    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP = 0x0002
    VK_W = 0x57
    SCAN_W = 0x11
    VK_SHIFT = 0x10
    SCAN_SHIFT = 0x2A

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
        ]

    class _INPUT_UNION(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT)]

    class INPUT(ctypes.Structure):
        _fields_ = [
            ("type", wintypes.DWORD),
            ("u", _INPUT_UNION)
        ]

    def set_keys(w_down: bool, shift_down: bool):
        try:
            extra = ctypes.c_ulong(0)
            
            # W Key
            flags_w = KEYEVENTF_KEYUP if not w_down else 0
            ki_w = KEYBDINPUT(VK_W, SCAN_W, flags_w, 0, ctypes.pointer(extra))
            inp_w = INPUT(INPUT_KEYBOARD, _INPUT_UNION(ki=ki_w))
            user32.SendInput(1, ctypes.pointer(inp_w), ctypes.sizeof(inp_w))

            # Shift Key
            flags_shift = KEYEVENTF_KEYUP if not shift_down else 0
            ki_s = KEYBDINPUT(VK_SHIFT, SCAN_SHIFT, flags_shift, 0, ctypes.pointer(extra))
            inp_s = INPUT(INPUT_KEYBOARD, _INPUT_UNION(ki=ki_s))
            user32.SendInput(1, ctypes.pointer(inp_s), ctypes.sizeof(inp_s))
        except Exception as e:
            print(f"[KeySend Error] {e}")
else:
    def set_keys(w_down: bool, shift_down: bool):
        pass

osc_client = OSCClient(port=9000)

# ---------------------------------------------------------------------------
# 3. HTTP Server Handler for Web App Commands
# ---------------------------------------------------------------------------
class BridgeRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if parsed.path == '/send':
            speed = float(params.get('speed', [0.0])[0])
            run = int(params.get('run', [0])[0]) == 1
            use_key = int(params.get('key', [0])[0]) == 1

            # 1. Send VRChat OSC
            osc_client.send_movement(speed, run)

            # 2. Virtual Keyboard Backup
            if use_key:
                set_keys(speed > 0.1, run)

            self.wfile.write(b'{"status":"ok"}')
        elif parsed.path == '/status':
            self.wfile.write(b'{"status":"running"}')
        else:
            self.wfile.write(b'{"error":"not_found"}')

    def log_message(self, format, *args):
        pass

def run_server(port=9011):
    server = HTTPServer(('127.0.0.1', port), BridgeRequestHandler)
    print(f"=======================================================")
    print(f" VRChat Web-OSC Bridge Server (Port: {port}) STARTED")
    print(f" Target VRChat OSC Port: 9000 (UDP)")
    print(f"=======================================================")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
