"""
VRChat HTTP/OSC & Key Bridge Server with Exit Cleanups
=====================================================
・ThreadingHTTPServer によるマルチスレッドHTTPサーバー
・Joy-Con (L) の自動再接続・IMUキープアライブ機能
・プロセス終了時 (atexit / signal / sys.excepthook) に VRChat 宛てへ強制移動リセット (0.0) を自動連打送信
"""

import sys
import time
import struct
import socket
import threading
import ctypes
from ctypes import wintypes
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import atexit
import signal
import hid

# Global Shared States (Thread-Safe)
joycon_state = {
    "connected": False,
    "ax": 0.0, "ay": 0.0, "az": 1.0,
    "gx": 0.0, "gy": 0.0,
    "last_update": 0
}
state_lock = threading.Lock()

# ---------------------------------------------------------------------------
# 1. OSC Client (Target: 127.0.0.1:9000) with Safe Emergency Reset
# ---------------------------------------------------------------------------
class OSCClient:
    def __init__(self, ip="127.0.0.1", port=9000):
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def _pad(self, b: bytes) -> bytes:
        return b + b'\x00' * (4 - (len(b) % 4))

    def send_movement(self, speed: float, is_running: bool):
        try:
            addr1 = self._pad(b'/input/Vertical')
            tag1 = self._pad(b',f')
            val1 = struct.pack('>f', float(speed))
            self.sock.sendto(addr1 + tag1 + val1, (self.ip, self.port))

            addr2 = self._pad(b'/input/Run')
            tag2 = self._pad(b',i')
            val2 = struct.pack('>i', 1 if is_running else 0)
            self.sock.sendto(addr2 + tag2 + val2, (self.ip, self.port))
        except Exception as e:
            pass

    def emergency_reset(self):
        """Send stop signals multiple times to ensure VRChat receives it upon application exit"""
        for _ in range(5):
            self.send_movement(0.0, False)
            time.sleep(0.01)

# ---------------------------------------------------------------------------
# 2. Windows Virtual Key Sender
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
            flags_w = KEYEVENTF_KEYUP if not w_down else 0
            ki_w = KEYBDINPUT(VK_W, SCAN_W, flags_w, 0, ctypes.pointer(extra))
            inp_w = INPUT(INPUT_KEYBOARD, _INPUT_UNION(ki=ki_w))
            user32.SendInput(1, ctypes.pointer(inp_w), ctypes.sizeof(inp_w))

            flags_shift = KEYEVENTF_KEYUP if not shift_down else 0
            ki_s = KEYBDINPUT(VK_SHIFT, SCAN_SHIFT, flags_shift, 0, ctypes.pointer(extra))
            inp_s = INPUT(INPUT_KEYBOARD, _INPUT_UNION(ki=ki_s))
            user32.SendInput(1, ctypes.pointer(inp_s), ctypes.sizeof(inp_s))
        except Exception:
            pass
else:
    def set_keys(w_down: bool, shift_down: bool):
        pass

osc_client = OSCClient(port=9000)

# Register automatic exit hooks for clean reset
def _exit_cleanup():
    try:
        set_keys(False, False)
        osc_client.emergency_reset()
        print("[System CleanExit] Sent VRChat reset signal (0.0)")
    except Exception:
        pass

atexit.register(_exit_cleanup)

def _handle_signal(sig, frame):
    _exit_cleanup()
    sys.exit(0)

try:
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)
except Exception:
    pass

def _global_exception_handler(exc_type, exc_value, exc_traceback):
    _exit_cleanup()
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = _global_exception_handler

# ---------------------------------------------------------------------------
# 3. Joy-Con HID Reader Thread with Auto Re-Init & Keep-Alive
# ---------------------------------------------------------------------------
def joycon_reader_worker():
    global joycon_state
    dev = None
    packet_count = 0
    last_imu_enable_time = 0

    def send_subcmd(d, subcmd, args):
        nonlocal packet_count
        rumble = [0x00, 0x01, 0x40, 0x40, 0x00, 0x01, 0x40, 0x40]
        buf = [0x01, packet_count & 0x0F] + rumble + [subcmd] + args
        packet_count = (packet_count + 1) & 0x0F
        try:
            d.write(buf)
            time.sleep(0.03)
            return True
        except Exception:
            return False

    def enable_imu(d):
        if send_subcmd(d, 0x03, [0x30]):
            send_subcmd(d, 0x40, [0x01])
            return True
        return False

    while True:
        with state_lock:
            connected = joycon_state["connected"]

        if not connected or dev is None:
            devices = hid.enumerate(0x057e, 0x2006)
            if not devices:
                devices = hid.enumerate(0x057e, 0)
            
            if devices:
                target = devices[0]
                try:
                    if dev:
                        try: dev.close()
                        except: pass
                    dev = hid.device()
                    dev.open_path(target['path'])
                    
                    if enable_imu(dev):
                        last_imu_enable_time = time.time()
                        with state_lock:
                            joycon_state["connected"] = True
                        print(f"[JoyCon HID] Connected and Enabled 60Hz IMU")
                    else:
                        raise Exception("Failed to send IMU enable subcommand")
                except Exception as e:
                    dev = None
                    with state_lock:
                        joycon_state["connected"] = False
                    time.sleep(1.0)
            else:
                dev = None
                time.sleep(1.0)
                continue

        # Active Read Loop
        try:
            now = time.time()
            if now - last_imu_enable_time > 10.0:
                enable_imu(dev)
                last_imu_enable_time = now

            data = dev.read(49, timeout_ms=50)
            if data and len(data) >= 25 and data[0] in (0x21, 0x30):
                raw_ax = struct.unpack('<h', bytes(data[13:15]))[0] * 0.000244
                raw_ay = struct.unpack('<h', bytes(data[15:17]))[0] * 0.000244
                raw_az = struct.unpack('<h', bytes(data[17:19]))[0] * 0.000244
                raw_gx = struct.unpack('<h', bytes(data[19:21]))[0] * 0.061
                raw_gy = struct.unpack('<h', bytes(data[21:23]))[0] * 0.061

                with state_lock:
                    joycon_state["ax"] = raw_ax
                    joycon_state["ay"] = raw_ay
                    joycon_state["az"] = raw_az
                    joycon_state["gx"] = raw_gx
                    joycon_state["gy"] = raw_gy
                    joycon_state["last_update"] = now

            elif data and len(data) > 0 and data[0] not in (0x21, 0x30):
                enable_imu(dev)
                last_imu_enable_time = now

        except Exception as e:
            with state_lock:
                joycon_state["connected"] = False
            if dev:
                try: dev.close()
                except: pass
                dev = None
            time.sleep(1.0)

# Start background thread
t = threading.Thread(target=joycon_reader_worker, daemon=True)
t.start()

# ---------------------------------------------------------------------------
# 4. Multi-threaded HTTP Server Handler
# ---------------------------------------------------------------------------
class BridgeRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
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

                osc_client.send_movement(speed, run)
                if use_key:
                    set_keys(speed > 0.1, run)

                self.wfile.write(b'{"status":"ok"}')

            elif parsed.path == '/get_sensor':
                with state_lock:
                    snapshot = json.dumps(joycon_state)
                self.wfile.write(snapshot.encode('utf-8'))

            elif parsed.path == '/status':
                self.wfile.write(b'{"status":"running"}')
            else:
                self.wfile.write(b'{"error":"not_found"}')
        except Exception:
            pass

    def log_message(self, format, *args):
        pass

def run_server(port=9011):
    server = ThreadingHTTPServer(('127.0.0.1', port), BridgeRequestHandler)
    print(f"=======================================================")
    print(f" VRChat Web-OSC Bridge Server (Port: {port}) [Multi-Threaded]")
    print(f" Target VRChat OSC Port: 9000 (UDP)")
    print(f"=======================================================")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
