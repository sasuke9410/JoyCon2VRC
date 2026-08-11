"""
VRChat OSC 疎通・強制移動テスト用デバッグスクリプト
--------------------------------------------------
実行すると 5秒間 強制的に VRChat へ前進OSC (/input/Vertical = 1.0, Port 9000) を送信します。
VRChat内でアバターが動くかテストしてください。
"""

import sys
import time
import socket
import struct

def send_osc_direct(ip="127.0.0.1", port=9000, speed=1.0, run=1):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    def pad(b): return b + b'\x00' * (4 - (len(b) % 4))
    
    # /input/Vertical
    data1 = pad(b'/input/Vertical') + pad(b',f') + struct.pack('>f', float(speed))
    sock.sendto(data1, (ip, port))
    
    # /input/Run
    data2 = pad(b'/input/Run') + pad(b',i') + struct.pack('>i', int(run))
    sock.sendto(data2, (ip, port))

if __name__ == "__main__":
    print("==================================================")
    print(" VRChat 強制OSC移動テストスクリプト")
    print(" ターゲット: 127.0.0.1:9000")
    print("==================================================")
    print("VRChat画面に切り替えてください。3秒後に 5秒間前進します...")
    
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
        
    print(">>> 送信中: /input/Vertical = 1.0 (前進) <<<")
    start = time.time()
    while time.time() - start < 5.0:
        send_osc_direct(speed=1.0, run=1)
        time.sleep(0.05)
        
    print(">>> 送信完了 (0.0 送信) <<<")
    send_osc_direct(speed=0.0, run=0)
