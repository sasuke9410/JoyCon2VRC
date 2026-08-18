# JoyCon2VRC - Joy-Con(L) Locomotion Controller

[Japanese Edition (日本語版はこちら)](README.md)

---

JoyCon2VRC is a Windows desktop application that utilizes the motion sensors of a Nintendo Switch **Joy-Con (L)** to enable natural in-place stepping locomotion (walking/running) inside VRChat virtual spaces.

---

## ⚡ Quick Start (Using the Executable)

No Python environment is required to run the compiled application.

1. **Prepare Joy-Con**
   * Pair Joy-Con (L) via Windows Settings -> "Bluetooth & devices".
2. **Launch Application**
   * Double-click [**dist/JoyCon2VRC.exe**](file:///c:/Users/sasuke/Documents/Joycon2VRC/dist/JoyCon2VRC.exe). The application will automatically detect and connect to your paired Joy-Con (L) in the background (Status changes to "Joy-Con(L) Connected").
3. **Calibrate (Recommended for first use)**
   * Click "Calibration Wizard" on the UI and follow the on-screen countdowns: **Static (3s)** -> **Walk (5s)** -> **Run (5s)**.
4. **Configure VRChat**
   * Open the VRChat Action Menu (`R` key or Controller menu button) -> `Options` -> `OSC` -> **`Enabled: True`**.
5. **Start Locomotion**
   * Click the "VRChat Transmit: OFF" button on the UI to switch it **`ON`**. Step in place, and your avatar will move!

---

## ✨ Key Features (v1.1 Updates)

* **Drift Rejection (Accidental Step Filter)**: 
  * Features a **2-Step Confirmation Gate** (READY buffer state) combined with **Thigh Swing Gyro Validation** ($G_y$ / $G_x$). This successfully prevents VRChat movement drift when you are standing still and shifting weight between legs or adjusting your posture.
* **Dynamic Analog Speed Control**:
  * Instead of rigid binary speeds, the system dynamically calculates smooth analog movement input values (`0.25` to `0.95`) based on your stepping cadence (SPM) and impact intensity ($A_{dyn}$). It scales smoothly, triggering `1.0` (RUN) once the cadence threshold is met. You can toggle between "Dynamic" and "Fixed (0.5/1.0)" speed modes.
* **Auto-Sleep Prevention (Keep-Alive)**:
  * Periodically sends Player LED commands (subcommand `0x30`) to the Joy-Con every 15 seconds. This resets the Joy-Con's internal auto-sleep timer, keeping it active even when you stand still for long periods without pressing buttons.
* **Numerical Battery & Stability Badges**:
  * Joy-Con battery level is shown as a percentage (`100%`, `70%`, `30%`, `10%`, `0%`).
  * Bluetooth connection stability is calculated from real-time packet arrival rates (60Hz target) and interval jitter, throttled to 1000ms updates to ensure high readability.
* **Trimmed Average Calibration**:
  * Uses a **trimmed mean algorithm** to filter out start delays and end slowdowns during the 5-second calibration window, generating robust customized parameters.
* **Configuration Persistence**:
  * Automatically saves sensitivity, RUN SPM threshold, input hold time, and speed mode settings to local storage, restoring them on the next launch.
* **Emergency Clean-up**:
  * On application close, the background worker instantly broadcasts vertical speed `0.0` to VRChat to prevent your avatar from walking/running continuously in the world.

---

## Requirements

* **OS**: Windows 10 / 11 (Bluetooth capability required)
* **Hardware**: Nintendo Switch Joy-Con (L)
* **Equipment**: Strap or band to secure the Joy-Con to your left thigh.
* **Target App**: VRChat (PC Desktop / SteamVR Mode)

---

## 🐍 Developers Guide

To run and build the application from source code:

```powershell
# Setup dependencies via uv
uv sync

# Run the desktop application
uv run python main.py

# Run the automated test suite
uv run pytest test_system_automated.py
```

---

## License

[MIT License](LICENSE)
