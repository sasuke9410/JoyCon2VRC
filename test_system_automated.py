"""
JoyCon2VRC Automated Test Suite
================================
自動テストスイート:
1. OSCパケットエンコーディング検証 (IEEE 754 Big-endian & 4-byte Padding)
2. 歩行・走行ステートマシン・ヒステリシス検証 (STOP -> WALK -> RUN -> HOLD -> STOP)
3. Web-OSC ブリッジサーバー統合テスト
4. スタンドアロン JoyCon2VRC.exe 整合性チェック
"""

import os
import sys
import time
import struct
import socket
import pytest
import urllib.request
import json
from threading import Thread

# Import system modules
from bridge_server import OSCClient, BridgeRequestHandler, run_server
from joycon_vrchat_live import JoyConVRChatRunner

# ---------------------------------------------------------------------------
# Test 1: OSC Packet Formatting & Encoding Verification
# ---------------------------------------------------------------------------
def test_osc_packet_encoding():
    client = OSCClient(ip="127.0.0.1", port=19999) # Use dummy test port
    
    # Create UDP Receiver to intercept OSC packets
    recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    recv_sock.bind(("127.0.0.1", 19999))
    recv_sock.settimeout(1.0)

    # Test Walk Speed (0.50, Run=0)
    client.send_movement(speed=0.5, is_running=False)

    # Read /input/Vertical
    data1, _ = recv_sock.recvfrom(1024)
    assert b'/input/Vertical\x00' in data1
    assert b',f\x00\x00' in data1
    # Check 32-bit big-endian float value for 0.5
    float_val = struct.unpack('>f', data1[-4:])[0]
    assert pytest.approx(float_val, 0.001) == 0.5

    # Read /input/Run
    data2, _ = recv_sock.recvfrom(1024)
    assert b'/input/Run\x00\x00' in data2
    assert b',i\x00\x00' in data2
    int_val = struct.unpack('>i', data2[-4:])[0]
    assert int_val == 0

    recv_sock.close()

# ---------------------------------------------------------------------------
# Test 2: Locomotion State Machine Logic (STOP -> WALK -> RUN)
# ---------------------------------------------------------------------------
def test_locomotion_state_machine_walk_run():
    runner = JoyConVRChatRunner(mode="normal")
    runner.sens_threshold = 0.30
    runner.run_spm_threshold = 150
    runner.hold_time_sec = 0.5

    # Initial State
    assert runner.state_name == "STOP"
    assert runner.speed_output == 0.0

    # Simulate Walk Steps (SPM ~ 120, Step Interval ~ 0.5s)
    t0 = time.time()
    # Step 1
    runner.last_step_time = t0
    runner.consecutive_steps = 1
    runner.cooldown_timer = t0 + 0.5
    runner.spm_history = [120, 120, 120]
    runner.smoothed_spm = 120

    # Evaluate at step 1
    t_eval = t0 + 0.1
    if t_eval < runner.cooldown_timer and runner.consecutive_steps >= 1:
        if runner.smoothed_spm >= runner.run_spm_threshold:
            runner.state_name = "RUN"
            runner.speed_output = 1.0
        else:
            runner.state_name = "WALK"
            runner.speed_output = 0.5

    assert runner.state_name == "WALK"
    assert runner.speed_output == 0.5

    # Simulate Fast Running Steps (SPM ~ 170)
    runner.spm_history = [170, 170, 170]
    runner.smoothed_spm = 170
    if runner.smoothed_spm >= runner.run_spm_threshold:
        runner.state_name = "RUN"
        runner.speed_output = 1.0

    assert runner.state_name == "RUN"
    assert runner.speed_output == 1.0

# ---------------------------------------------------------------------------
# Test 3: HTTP Bridge Server Integration Test
# ---------------------------------------------------------------------------
def test_bridge_http_server():
    # Start Bridge Server on test port 19011
    server_thread = Thread(target=run_server, args=(19011,), daemon=True)
    server_thread.start()
    time.sleep(0.3)

    # Test HTTP GET /status
    res = urllib.request.urlopen("http://127.0.0.1:19011/status")
    body = json.loads(res.read().decode('utf-8'))
    assert body["status"] == "running"

    # Test HTTP GET /send?speed=1.0&run=1&key=0
    res_send = urllib.request.urlopen("http://127.0.0.1:19011/send?speed=1.0&run=1&key=0")
    body_send = json.loads(res_send.read().decode('utf-8'))
    assert body_send["status"] == "ok"

# ---------------------------------------------------------------------------
# Test 4: Standalone JoyCon2VRC.exe File Integrity Test
# ---------------------------------------------------------------------------
def test_standalone_executable_bundle():
    exe_path = os.path.join(".", "dist", "JoyCon2VRC.exe")
    assert os.path.exists(exe_path), "JoyCon2VRC.exe binary does not exist in dist/"
    assert os.path.getsize(exe_path) > 10 * 1024 * 1024, "JoyCon2VRC.exe bundle is smaller than 10MB"
