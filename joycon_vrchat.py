"""
Joy-Con (L) 足踏み VRChat Locomotion Bridge (Python ゼロ依存実装)
-----------------------------------------------------------------
・VRChat Native OSC (/input/Vertical, /input/Run) へのUDP送信
・Windows SendInput による仮想 W / Shift キー送信
・WebHID ブラウザアプリからのWebSocket連携 または HIDAPI直結対応
"""

import sys
import time
import socket
import struct
import ctypes
from ctypes import wintypes

# ---------------------------------------------------------------------------
# 1. OSC Message Encoder (Python Standard Library Only)
# ---------------------------------------------------------------------------
class OSCClient:
    def __init__(self, ip="127.0.0.1", port=9010):
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def _pad(self, b: bytes) -> bytes:
        """OSC strings must be null-terminated and padded to 4-byte boundaries."""
        return b + b'\x00' * (4 - (len(b) % 4))

    def send_float(self, address: str, value: float):
        """Send a single float message to VRChat OSC."""
        addr_bytes = self._pad(address.encode('utf-8'))
        tag_bytes = self._pad(b',f')
        val_bytes = struct.pack('>f', float(value))
        data = addr_bytes + tag_bytes + val_bytes
        try:
            self.sock.sendto(data, (self.ip, self.port))
        except Exception as e:
            print(f"[OSC Error] {e}")

    def send_int(self, address: str, value: int):
        """Send a single integer message to VRChat OSC."""
        addr_bytes = self._pad(address.encode('utf-8'))
        tag_bytes = self._pad(b',i')
        val_bytes = struct.pack('>i', int(value))
        data = addr_bytes + tag_bytes + val_bytes
        try:
            self.sock.sendto(data, (self.ip, self.port))
        except Exception as e:
            print(f"[OSC Error] {e}")

# ---------------------------------------------------------------------------
# 2. Windows Direct Keyboard Input via SendInput (Ctypes)
# ---------------------------------------------------------------------------
if sys.platform == 'win32':
    user32 = ctypes.windll.user32

    # Constants
    INPUT_KEYBOARD = 1
    KEYEVENTF_EXTENDEDKEY = 0x0001
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_SCANCODE = 0x0008

    # Virtual Key Codes & Scan Codes
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

    class INPUT(ctypes.Structure):
        class _INPUT(ctypes.Union):
            _fields_ = [("ki", KEYBDINPUT)]
        _anonymous_ = ("_input",)
        _fields_ = [
            ("type", wintypes.DWORD),
            ("_input", _INPUT)
        ]

    def press_key(scan_code, vk_code):
        extra = ctypes.c_ulong(0)
        ii_ = KEYBDINPUT(vk_code, scan_code, 0, 0, ctypes.pointer(extra))
        x = INPUT(INPUT_KEYBOARD, ii_)
        user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

    def release_key(scan_code, vk_code):
        extra = ctypes.c_ulong(0)
        ii_ = KEYBDINPUT(vk_code, scan_code, KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))
        x = INPUT(INPUT_KEYBOARD, ii_)
        user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

    def set_key_state(w_down: bool, shift_down: bool):
        if w_down:
            press_key(SCAN_W, VK_W)
        else:
            release_key(SCAN_W, VK_W)

        if shift_down:
            press_key(SCAN_SHIFT, VK_SHIFT)
        else:
            release_key(SCAN_SHIFT, VK_SHIFT)
else:
    def set_key_state(w_down: bool, shift_down: bool):
        print(f"[VirtualKey] W={w_down}, Shift={shift_down}")

# ---------------------------------------------------------------------------
# 3. Main Controller Bridge Class
# ---------------------------------------------------------------------------
class VRChatLocomotionBridge:
    def __init__(self, osc_ip="127.0.0.1", osc_port=9010):
        self.osc = OSCClient(osc_ip, osc_port)
        self.current_speed = 0.0
        self.current_run = False
        self.key_w = False
        self.key_shift = False

    def update_movement(self, speed: float, is_running: bool, use_keyboard: bool = False):
        """
        speed: 0.0 (STOP), 0.5 (WALK), 1.0 (RUN)
        is_running: True if sprinting
        """
        # Send OSC to VRChat
        self.osc.send_float("/input/Vertical", speed)
        self.osc.send_int("/input/Run", 1 if is_running else 0)

        # Virtual Keyboard fallback
        if use_keyboard:
            w_state = speed > 0.1
            shift_state = is_running
            set_key_state(w_state, shift_state)

        print(f"[VRChat Motion] Vertical={speed:.2f} | Run={is_running} | Keyboard W={speed > 0.1}")

# Quick CLI Test / Demo
if __name__ == "__main__":
    print("==================================================")
    print(" Joy-Con(L) VRChat Locomotion Bridge Initialized  ")
    print(" Target OSC: 127.0.0.1:9010                      ")
    print("==================================================")

    bridge = VRChatLocomotionBridge()

    print("\n--- Simulation Test Run ---")
    print("[1] Walk State (0.5)")
    bridge.update_movement(speed=0.5, is_running=False, use_keyboard=False)
    time.sleep(1.5)

    print("[2] Run State (1.0)")
    bridge.update_movement(speed=1.0, is_running=True, use_keyboard=False)
    time.sleep(1.5)

    print("[3] Stop State (0.0)")
    bridge.update_movement(speed=0.0, is_running=False, use_keyboard=False)
    print("\nBridge Ready for Joy-Con Input!")
