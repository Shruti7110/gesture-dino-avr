import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL']  = '3'

import serial
import numpy as np
import pyautogui
import time
import collections
import tensorflow as tf

# ── CONFIG ──────────────────────────────────────
PORT                 = 'COM19'
BAUD                 = 9600
WINDOW_SIZE          = 20        # 20 samples × 100ms = 2 seconds
CONFIDENCE_THRESHOLD = 0.85
COOLDOWN             = 0.8
LABELS               = ['duck', 'idle', 'jump']
# ────────────────────────────────────────────────

# ── Load model ──────────────────────────────────
interpreter = tf.lite.Interpreter(model_path="gesture_model.tflite")
interpreter.allocate_tensors()
input_details  = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Print what model expects → so we know correct shape
print("Model input shape:", input_details[0]['shape'])
expected_size = input_details[0]['shape'][1]
print(f"Model expects {expected_size} input features")

# ── Feature extraction ───────────────────────────
def extract_features(window):
    data = np.array(window, dtype=np.float32)  # shape (20, 3)

    features = []

    for axis in range(3):        # x, y, z
        signal = data[:, axis]

        # Time domain features
        features.append(np.mean(signal))         # mean
        features.append(np.std(signal))          # std deviation
        features.append(np.max(signal))          # max
        features.append(np.min(signal))          # min
        features.append(np.sqrt(np.mean(signal**2)))  # RMS

        # Frequency domain features
        fft_vals = np.abs(np.fft.rfft(signal))
        freqs    = np.fft.rfftfreq(len(signal), d=0.1)  # 10Hz sampling

        # Spectral power in frequency bands
        # matches Edge Impulse spectral analysis bands
        bands = [(0.5, 1.5), (1.5, 2.5), (2.5, 3.5), (3.5, 4.5)]
        for low, high in bands:
            mask  = (freqs >= low) & (freqs < high)
            power = np.sum(fft_vals[mask]**2)
            features.append(power)

    return np.array(features, dtype=np.float32)

def run_inference(window):
    features = extract_features(window)

    # Pad or trim to match exact model input size
    if len(features) < expected_size:
        features = np.pad(features, (0, expected_size - len(features)))
    else:
        features = features[:expected_size]

    features = features.reshape(1, expected_size)

    interpreter.set_tensor(input_details[0]['index'], features)
    interpreter.invoke()

    output     = interpreter.get_tensor(output_details[0]['index'])
    scores     = output[0]
    best_idx   = np.argmax(scores)
    best_label = LABELS[best_idx]
    confidence = scores[best_idx]

    return best_label, confidence

def press_key(label):
    if label == 'jump':
        pyautogui.press('space')
        print("\nJUMP → SPACE")
    elif label == 'duck':
        pyautogui.keyDown('down')
        time.sleep(0.3)
        pyautogui.keyUp('down')
        print("\nDUCK → DOWN")

def parse_line(line):
    try:
        parts = line.strip().split(',')
        x = int(parts[0])
        y = int(parts[1])
        z = int(parts[2])
        return [x, y, z]
    except:
        return None

def main():
    print("=== DINO GESTURE CONTROLLER ===")
    print(f"Connecting to {PORT}...")

    ser = serial.Serial(PORT, BAUD, timeout=2)
    time.sleep(2)
    ser.reset_input_buffer()

    print("Connected! Open Chrome Dino game now.")
    print("You have 5 seconds to click on the game window...")
    time.sleep(5)

    window           = collections.deque(maxlen=WINDOW_SIZE)
    last_action_time = 0

    print("GO! Gesture control active.\n")

    while True:
        if ser.in_waiting > 0:
            try:
                raw    = ser.readline()
                line   = raw.decode('utf-8', errors='ignore')
                parsed = parse_line(line)

                if parsed:
                    window.append(parsed)

                    if len(window) == WINDOW_SIZE:
                        label, confidence = run_inference(list(window))
                        print(f"  {label} ({confidence:.2f})", end='\r')

                        now = time.time()
                        if (label != 'idle' and
                            confidence > CONFIDENCE_THRESHOLD and
                            (now - last_action_time) > COOLDOWN):
                            press_key(label)
                            last_action_time = now

            except Exception as e:
                print(f"Error: {e}")
                continue
        else:
            time.sleep(0.01)

if __name__ == "__main__":
    main()