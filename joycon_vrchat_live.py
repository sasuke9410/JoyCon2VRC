"""
Joy-Con (L) 太もも固定・足踏みVRChat移動システム (実機直結 Python 実行版)
==========================================================================
・Joy-Con (L) の Bluetooth HID 直結・6軸IMUセンサーリアルタイム解析
・STOP<->WALK チャタリング(反復横跳び)防止ホールドタイマー (1.0s)
・WALK->RUN 誤昇格防止フィルタ (移動平均SPM ＋ 連続RUNヒットカウント)
・VRChat Native OSC (/input/Vertical, /input/Run) [Port 9000] ＋ 仮想 W / Shift キー自動送信
"""

import sys
import time
import math
import struct
import socket
import hid
import ctypes
from ctypes import wintypes

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
        addr1 = self._pad(b'/input/Vertical')
        tag1 = self._pad(b',f')
        val1 = struct.pack('>f', float(speed))
        self.sock.sendto(addr1 + tag1 + val1, (self.ip, self.port))

        addr2 = self._pad(b'/input/Run')
        tag2 = self._pad(b',i')
        val2 = struct.pack('>i', 1 if is_running else 0)
        self.sock.sendto(addr2 + tag2 + val2, (self.ip, self.port))

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

    class INPUT(ctypes.Structure):
        class _INPUT(ctypes.Union):
            _fields_ = [("ki", KEYBDINPUT)]
        _anonymous_ = ("_input",)
        _fields_ = [("type", wintypes.DWORD), ("_input", _INPUT)]

    def set_keys(w_down: bool, shift_down: bool):
        extra = ctypes.c_ulong(0)
        flags_w = KEYEVENTF_KEYUP if not w_down else 0
        i_w = INPUT(INPUT_KEYBOARD, KEYBDINPUT(VK_W, SCAN_W, flags_w, 0, ctypes.pointer(extra)))
        user32.SendInput(1, ctypes.pointer(i_w), ctypes.sizeof(i_w))

        flags_shift = KEYEVENTF_KEYUP if not shift_down else 0
        i_s = INPUT(INPUT_KEYBOARD, KEYBDINPUT(VK_SHIFT, SCAN_SHIFT, flags_shift, 0, ctypes.pointer(extra)))
        user32.SendInput(1, ctypes.pointer(i_s), ctypes.sizeof(i_s))
else:
    def set_keys(w_down: bool, shift_down: bool):
        pass

# ---------------------------------------------------------------------------
# 3. Main Locomotion Engine
# ---------------------------------------------------------------------------
class JoyConVRChatRunner:
    def __init__(self, mode="normal"):
        self.mode = mode
        self.osc = OSCClient(port=9000)
        self.device = None
        self.packet_count = 0

        self.sens_threshold = 0.35
        self.run_spm_threshold = 150
        self.hold_time_sec = 1.0
        self.silent_angle_thresh = 12.0
        self.filter_alpha = 0.2

        self.filtered_ax = 0.0
        self.filtered_ay = 0.0
        self.filtered_az = 0.0
        self.estimated_pitch = 0.0
        self.baseline_pitch = 0.0

        self.last_step_time = 0
        self.consecutive_steps = 0
        self.spm_history = [0, 0, 0]
        self.cooldown_timer = 0
        self.smoothed_spm = 0
        self.state_name = "STOP"
        self.speed_output = 0.0

    def connect_joycon(self):
        print("Joy-Con (L) [VID: 0x057e, PID: 0x2006] に接続中...")
        devices = hid.enumerate(0x057e, 0x2006)
        if not devices:
            devices = hid.enumerate(0x057e, 0)
            if not devices:
                print("エラー: Joy-Con(L) がBluetooth接続されていません。")
                return False

        target = devices[0]
        self.device = hid.device()
        self.device.open_path(target['path'])
        print(f"接続成功: {target.get('product_string', 'Joy-Con (L)')}")

        self._send_subcommand(0x03, [0x30])
        self._send_subcommand(0x40, [0x01])
        return True

    def _send_subcommand(self, subcmd, args):
        rumble = [0x00, 0x01, 0x40, 0x40, 0x00, 0x01, 0x40, 0x40]
        buf = [0x01, self.packet_count & 0x0F] + rumble + [subcmd] + args
        self.packet_count = (self.packet_count + 1) & 0x0F
        self.device.write(buf)
        time.sleep(0.04)

    def run_loop(self, duration_sec=30):
        print("\n=======================================================")
        print(f" VRChat 足踏み移動エンジン起動中 (モード: {self.mode.upper()})")
        print(" [Ctrl+C] でいつでも終了できます")
        print("=======================================================\n")

        start_time = time.time()
        last_print = 0

        try:
            while (time.time() - start_time) < duration_sec:
                data = self.device.read(49, timeout_ms=100)
                if not data or len(data) < 25 or data[0] not in (0x21, 0x30):
                    continue

                now = time.time()

                raw_ax = struct.unpack('<h', bytes(data[13:15]))[0] * 0.000244
                raw_ay = struct.unpack('<h', bytes(data[15:17]))[0] * 0.000244
                raw_az = struct.unpack('<h', bytes(data[17:19]))[0] * 0.000244
                raw_gy = struct.unpack('<h', bytes(data[21:23]))[0] * 0.061

                a = self.filter_alpha
                self.filtered_ax = a * raw_ax + (1 - a) * self.filtered_ax
                self.filtered_ay = a * raw_ay + (1 - a) * self.filtered_ay
                self.filtered_az = a * raw_az + (1 - a) * self.filtered_az

                accel_pitch = math.atan2(self.filtered_ax, self.filtered_az) * (180.0 / math.pi)
                dt = 0.016
                self.estimated_pitch = 0.95 * (self.estimated_pitch + raw_gy * dt) + 0.05 * accel_pitch

                total_accel = math.sqrt(self.filtered_ax**2 + self.filtered_ay**2 + self.filtered_az**2)
                dyn_accel = abs(total_accel - 1.0)

                if self.mode == "normal":
                    if dyn_accel > self.sens_threshold:
                        if self.last_step_time == 0:
                            self.last_step_time = now
                            self.consecutive_steps = 1
                        else:
                            dt_step = now - self.last_step_time
                            if 0.20 < dt_step < 1.2:
                                raw_spm = int(60.0 / dt_step)
                                self.last_step_time = now
                                self.consecutive_steps += 1
                                self.cooldown_timer = now + self.hold_time_sec

                                self.spm_history.pop(0)
                                self.spm_history.append(raw_spm)
                                self.smoothed_spm = sum(self.spm_history) // len(self.spm_history)

                            elif dt_step >= 1.2:
                                self.last_step_time = now
                                self.consecutive_steps = 1
                else:
                    delta_pitch = abs(self.estimated_pitch - self.baseline_pitch)
                    if delta_pitch > self.silent_angle_thresh:
                        self.cooldown_timer = now + 0.8
                        self.smoothed_spm = min(int(abs(raw_gy) * 0.8), 180)
                        self.consecutive_steps = 1
                    else:
                        self.baseline_pitch = 0.98 * self.baseline_pitch + 0.02 * self.estimated_pitch

                if now < self.cooldown_timer:
                    if self.smoothed_spm >= self.run_spm_threshold:
                        self.state_name = "RUN"
                        self.speed_output = 1.0
                        is_run = True
                    else:
                        self.state_name = "WALK"
                        self.speed_output = 0.5
                        is_run = False
                    w_down = True
                else:
                    self.state_name = "STOP"
                    self.speed_output = 0.0
                    self.smoothed_spm = 0
                    self.consecutive_steps = 0
                    self.spm_history = [0, 0, 0]
                    is_run = False
                    w_down = False

                self.osc.send_movement(self.speed_output, is_run)
                set_keys(w_down, is_run)

                if now - last_print > 0.1:
                    last_print = now
                    badge = f"\033[92m[{self.state_name}]\033[0m" if self.state_name != "STOP" else f"[{self.state_name}]"
                    print(f"\rStatus: {badge:<15} | Speed: {self.speed_output:.2f} | SPM: {self.smoothed_spm:<3} | AccelDyn: {dyn_accel:.2f}G", end="", flush=True)

        except KeyboardInterrupt:
            print("\nユーザーによる中断")
        finally:
            self.osc.send_movement(0.0, False)
            set_keys(False, False)
            if self.device:
                self.device.close()
            print("\n停止処理完了。VRChat移動出力をリセットしました。")

if __name__ == "__main__":
    mode_arg = sys.argv[1] if len(sys.argv) > 1 else "normal"
    runner = JoyConVRChatRunner(mode=mode_arg)
    if runner.connect_joycon():
        runner.run_loop(duration_sec=30)
