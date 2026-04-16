import serial
import csv
import time
import os

# ── CONFIG ──────────────────────────────────────
BAUD        = 9600
DURATION    = 3          # seconds per recording
OUTPUT_FILE = 'gesture_data.csv'
# ────────────────────────────────────────────────

def init_csv():
    # Create file with header if it doesnt exist yet
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'x', 'y', 'z', 'label'])
        print(f"Created new file: {OUTPUT_FILE}")
    else:
        print(f"Appending to existing file: {OUTPUT_FILE}")

def save_samples(samples):
    # Append samples to CSV immediately after each recording
    with open(OUTPUT_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(samples)
    print(f"  Saved {len(samples)} samples to {OUTPUT_FILE}")

def parse_line(line):
    # Parse "X: 12  Y: -8  Z: 256" format
    try:
        parts = line.replace('X:','').replace('Y:','').replace('Z:','').split()
        x = int(parts[0])
        y = int(parts[1])
        z = int(parts[2])
        return x, y, z
    except:
        return None

def record_gesture(ser, label, rep_number):
    print(f"\n  Rep {rep_number} → perform: '{label}'")
    print("  Starting in 3 seconds... get ready")
    time.sleep(3)

    # Flush anything that built up during countdown
    ser.reset_input_buffer()

    print("  >>> RECORDING <<<")
    samples   = []
    start     = time.time()
    last_time = start

    while (time.time() - start) < DURATION:

        # Safety check → if no data for 2 seconds something is wrong
        if (time.time() - last_time) > 2.0:
            print("  WARNING: No data received for 2s, check connection")
            break

        # Check if data is waiting → non blocking
        if ser.in_waiting > 0:
            try:
                raw      = ser.readline()
                line     = raw.decode('utf-8', errors='ignore').strip()
                parsed   = parse_line(line)
                last_time = time.time()    # reset timeout

                if parsed:
                    x, y, z   = parsed
                    timestamp = round(time.time() - start, 4)
                    samples.append([timestamp, x, y, z, label])
                    print(f"    t={timestamp}s  X={x:5d}  Y={y:5d}  Z={z:5d}")

            except Exception as e:
                print(f"  Read error: {e}")
                continue

        else:
            time.sleep(0.01)    # small sleep → prevents CPU spin

    return samples

def get_serial(port):
    try:
        ser = serial.Serial(
            port     = port,
            baudrate = BAUD,
            timeout  = 1,        # 1 second read timeout
            write_timeout = 1
        )
        time.sleep(2)            # wait for Arduino reset
        ser.reset_input_buffer() # clear garbage on connect
        return ser
    except Exception as e:
        print(f"Could not open port: {e}")
        return None

def count_existing():
    # Show how many recordings already in file
    if not os.path.exists(OUTPUT_FILE):
        return 0
    with open(OUTPUT_FILE, 'r') as f:
        return sum(1 for line in f) - 1   # subtract header

def main():
    print("=== GESTURE DATA COLLECTOR ===\n")

    # Get port
    port = input("Enter COM port (e.g. COM6 or /dev/ttyUSB0): ").strip()

    # Get label
    print("\nAvailable gestures: jump | duck | idle")
    label = input("Enter gesture label to record: ").strip().lower()
    if label not in ['jump', 'duck', 'idle']:
        print("Invalid label. Use: jump, duck, or idle")
        return

    # Get how many reps this session
    reps = int(input("How many recordings this session? (e.g. 10): ").strip())

    # Connect serial
    ser = get_serial(port)
    if ser is None:
        return

    # Init CSV
    init_csv()

    existing = count_existing()
    print(f"\nExisting samples in file: {existing}")
    print(f"\nRecording {reps}x '{label}' gesture")
    print("Instructions:")

    if label == 'jump':
        print("  → Quick forward tilt then return flat")
    elif label == 'duck':
        print("  → Quick sideways tilt then return flat")
    elif label == 'idle':
        print("  → Hold board flat and still")

    input("\nPress ENTER to begin...")

    total_saved = 0

    for i in range(1, reps + 1):
        print(f"\n--- Recording {i}/{reps} ---")

        samples = record_gesture(ser, label, i)

        if len(samples) == 0:
            print("  No samples captured, skipping save")
        else:
            save_samples(samples)           # save immediately after each rep
            total_saved += len(samples)

        # Short break between reps
        if i < reps:
            print("  Rest... next rep coming up")
            time.sleep(1)

    ser.close()

    print(f"\n=== SESSION COMPLETE ===")
    print(f"Recordings done  : {reps}")
    print(f"Samples saved    : {total_saved}")
    print(f"Total in file now: {count_existing()}")
    print(f"File             : {OUTPUT_FILE}")
    print("\nRun again with same file to add more recordings")

if __name__ == "__main__":
    main()