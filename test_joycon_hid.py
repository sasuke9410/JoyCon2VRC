import time
import struct
import hid

def main():
    print("Searching for Joy-Con (L) [Vendor ID: 0x057e, Product ID: 0x2006]...")
    devices = hid.enumerate(0x057e, 0x2006)
    
    if not devices:
        print("Joy-Con (L) not found via hidapi.")
        print("Checking all Nintendo devices...")
        all_nintendo = hid.enumerate(0x057e, 0)
        if not all_nintendo:
            print("No Nintendo Bluetooth HID devices detected. Please ensure Joy-Con (L) is paired and connected via Bluetooth.")
            return
        else:
            print("Found Nintendo devices:")
            for d in all_nintendo:
                print(f" - {d['product_string']} (PID: {hex(d['product_id'])}, Path: {d['path']})")
            devices = [all_nintendo[0]]

    target = devices[0]
    print(f"\nOpening device: {target.get('product_string', 'Joy-Con (L)')}")
    print(f"Path: {target['path']}")

    device = hid.device()
    try:
        device.open_path(target['path'])
        device.set_nonblocking(False)
        print("Device opened successfully!")

        # Step 1: Enable 6-Axis IMU Sensor (Subcommand 0x40 -> 0x01)
        print("Enabling IMU sensors...")
        packet_count = 0
        
        def send_subcommand(subcmd, args):
            nonlocal packet_count
            rumble = [0x00, 0x01, 0x40, 0x40, 0x00, 0x01, 0x40, 0x40]
            buf = [0x01, packet_count & 0x0F] + rumble + [subcmd] + args
            packet_count = (packet_count + 1) & 0x0F
            device.write(buf)
            time.sleep(0.05)

        # Set Standard Full 60Hz Report Mode (Subcmd 0x03, Arg 0x30)
        send_subcommand(0x03, [0x30])
        # Enable IMU (Subcmd 0x40, Arg 0x01)
        send_subcommand(0x40, [0x01])

        print("\n=== Reading 6-Axis Sensor Data (20 samples) ===")
        print(f"{'Sample':<8} | {'Accel X (G)':<12} | {'Accel Y (G)':<12} | {'Accel Z (G)':<12} | {'Gyro Pitch':<12} | {'Gyro Roll':<12}")
        print("-" * 80)

        samples_read = 0
        start_time = time.time()

        while samples_read < 20 and (time.time() - start_time) < 10.0:
            data = device.read(49, timeout_ms=500)
            if not data:
                continue

            # Report ID 0x21 or 0x30 contains IMU data at offset 13
            report_id = data[0]
            if report_id in (0x21, 0x30) and len(data) >= 25:
                # First IMU frame (12 bytes starting at index 13)
                # Int16 Little Endian
                raw_ax = struct.unpack('<h', bytes(data[13:15]))[0]
                raw_ay = struct.unpack('<h', bytes(data[15:17]))[0]
                raw_az = struct.unpack('<h', bytes(data[17:19]))[0]

                raw_gx = struct.unpack('<h', bytes(data[19:21]))[0]
                raw_gy = struct.unpack('<h', bytes(data[21:23]))[0]

                # Convert to G and deg/s
                ax = raw_ax * 0.000244
                ay = raw_ay * 0.000244
                az = raw_az * 0.000244

                gx = raw_gx * 0.061
                gy = raw_gy * 0.061

                samples_read += 1
                print(f"{samples_read:<8} | {ax:<12.3f} | {ay:<12.3f} | {az:<12.3f} | {gx:<12.1f} | {gy:<12.1f}")

        print("-" * 80)
        if samples_read > 0:
            print("SUCCESS: Joy-Con (L) sensor data read successfully!")
        else:
            print("WARNING: Connected to Joy-Con (L), but no IMU reports received. Please check Bluetooth connection state.")

    except Exception as e:
        print(f"Error accessing Joy-Con (L): {e}")
    finally:
        try:
            device.close()
        except:
            pass

if __name__ == "__main__":
    main()
