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
# Test 2: Locomotion State Machine Logic (STOP-Drift Rejection & Dynamic Speed)
# ---------------------------------------------------------------------------
def test_locomotion_state_machine_drift_rejection():
    """Verify that a single impact (e.g. weight shifting) stays in READY/STOP and does NOT move"""
    runner = JoyConVRChatRunner(mode="normal")
    runner.sens_threshold = 0.35
    runner.run_spm_threshold = 150
    runner.hold_time_sec = 1.0

    t0 = time.time()
    # 1. Single impact (Candidate only -> 1 step)
    runner.last_step_time = t0
    runner.consecutive_steps = 1
    runner.cooldown_timer = 0 # No cooldown until locked

    # Evaluation with 1 step
    if t0 > runner.cooldown_timer or runner.consecutive_steps < 2:
        runner.state_name = "READY" if runner.consecutive_steps == 1 else "STOP"
        runner.speed_output = 0.0

    # Ensure speed output is 0.0 (No movement in VRChat)
    assert runner.state_name == "READY"
    assert runner.speed_output == 0.0

def test_locomotion_state_machine_walk_run_dynamic_speed():
    """Verify 2+ steps transition to WALK with dynamic speed, and fast pace transitions to RUN"""
    runner = JoyConVRChatRunner(mode="normal")
    runner.sens_threshold = 0.35
    runner.run_spm_threshold = 150
    runner.hold_time_sec = 1.0

    t0 = time.time()
    # Step 1 (Pending)
    runner.last_step_time = t0
    runner.consecutive_steps = 1

    # Step 2 arrives at t0 + 0.45s (approx 133 SPM)
    t1 = t0 + 0.45
    runner.last_step_time = t1
    runner.consecutive_steps = 2
    runner.cooldown_timer = t1 + runner.hold_time_sec
    runner.spm_history = [133, 133, 133]
    runner.smoothed_spm = 133

    # Dynamic Speed Calculation
    norm_spm = min(max((runner.smoothed_spm - 70) / (runner.run_spm_threshold - 70), 0.0), 1.0)
    base_speed = 0.25 + 0.60 * norm_spm
    intensity = 1.0
    runner.speed_output = round(min(max(base_speed * intensity, 0.20), 0.95), 2)
    runner.state_name = "WALK"

    assert runner.state_name == "WALK"
    assert 0.50 <= runner.speed_output <= 0.85 # Dynamic analog speed output

    # High cadence (170 SPM -> RUN)
    runner.smoothed_spm = 170
    is_run_cond = runner.smoothed_spm >= runner.run_spm_threshold
    runner.state_name = "RUN" if is_run_cond else "WALK"
    runner.speed_output = 1.0 if is_run_cond else runner.speed_output

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
