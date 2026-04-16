# gesture-dino-avr

> Wrist gesture control glove using ATmega328P, ADXL345 accelerometer, and Edge Impulse ML — flick your wrist to jump, tilt to duck, control Chrome Dino hands-free. Bare metal AVR C firmware + Python inference pipeline.

---
![alt text](https://github.com/Shruti7110/gesture-dino-avr/blob/main/gesture-dino-avr-introduction-img.png)

## What Is This?

Strap the sensor to your glove, flick your wrist forward to **jump**, tilt sideways to **duck**. No Arduino libraries, no shortcuts — pure bare metal AVR C firmware reading wrist movements and feeding them into a machine learning model running on your PC to control the Chrome Dino game in real time.

This project combines a wearable sensor glove, embedded firmware, I2C communication, Edge Impulse gesture ML, and Python automation into one complete pipeline.

---

## Demo

```
Flick wrist forward  →  JUMP  →  Spacebar
Tilt wrist sideways  →  DUCK  →  Down Arrow
Hold wrist flat      →  IDLE  →  No action
```

---

## Hardware Required

| Component | Details |
|---|---|
| Arduino Uno | ATmega328P @ 16MHz |
| ADXL345 Module | HW-014, I2C mode, mounted on glove |
| Glove | Any snug fitting glove |
| USB Cable | Arduino to PC |
| Jumper Wires | 4 wires for I2C |

### Glove Setup
The ADXL345 module is strapped to the back of the hand on a glove, with wires running down to the Arduino. This lets natural wrist gestures control the game — forward flick for jump, sideways tilt for duck.

---

## Wiring

| ADXL345 Pin | Arduino Pin |
|---|---|
| 3V3 | 3.3V |
| GND | GND |
| SCL | A5 |
| SDA | A4 |
| SDO | GND (sets I2C address 0x53) |

> Note: The HW-014 module has CS internally pulled HIGH — this forces I2C mode. SPI is not available on this module without hardware modification.

---

## Project Structure

```
gesture-glove-dino/
│
├── firmware/                   ← Atmel Studio AVR C project
│   ├── main.c                  ← main loop, reads XYZ, sends via UART
│   ├── uart.c / uart.h         ← UART init, send char, send string
│   ├── i2c.c  / i2c.h          ← I2C init, start, stop, read, write
│   └── adxl345.c / adxl345.h  ← ADXL345 register map, init, ReadXYZ
│
├── python/
│   ├── data_collect.py         ← collect labeled XYZ data via UART
│   ├── clean_data.py           ← remove bad recordings from CSV
│   ├── format_ei.py            ← format CSV for Edge Impulse upload
│   └── dino_controller.py      ← runs ML model, controls Dino game
│
├── model/
│   └── gesture_model.tflite    ← trained Edge Impulse model (float32)
│
└── README.md
```

---

## Firmware — How It Works

Written in bare metal AVR C using Atmel Studio 7. No Arduino libraries used.

The ATmega328P reads X, Y, Z acceleration from the ADXL345 over I2C every 100ms and streams raw values over UART:

```
12,-8,256
11,-7,255
180,-6,200
```

Key registers used:

| Register | Purpose |
|---|---|
| TWCR | I2C control register |
| TWDR | I2C data register |
| TWBR | I2C clock speed |
| UBRR0 | UART baud rate |
| UCSR0B | UART enable TX/RX |

---

## Machine Learning — Edge Impulse

Gesture data was collected wearing the glove at 10Hz sampling rate using `data_collect.py`. Each gesture was performed naturally as you would during a game:

| Gesture | Samples | Description |
|---|---|---|
| jump | ~1054 | Quick forward wrist flick, return flat |
| duck | ~1060 | Quick sideways wrist tilt, return flat |
| idle | ~1051 | Hold wrist flat and still |

Impulse design on Edge Impulse:

```
Input (10Hz, 2000ms window)
  → Spectral Analysis (FFT features per axis)
  → Classification (Neural Network)
  → Output: jump / duck / idle
```

Training results:

```
Training accuracy   → 100%
Test accuracy       → 100%
F1 Score            → 1.00
Inferencing time    → 1ms
Peak RAM usage      → 1.4K
Flash usage         → 15.1K
```

Model exported as TensorFlow Lite Float32 and used in Python inference pipeline on PC.

---

## Python Pipeline

### Collect Training Data
```bash
python data_collect.py
# enter COM port, gesture label, number of reps
# saves to gesture_data.csv automatically after each recording
# run separately for each gesture: jump, duck, idle
```

### Clean Data
```bash
python clean_data.py
# removes recordings with less than 40 samples
# saves gesture_data_clean.csv
```

### Format for Edge Impulse
```bash
python format_ei.py
# splits into individual files per recording
# saves to ei_upload/ folder
# upload these files to Edge Impulse dashboard
```

### Run Dino Controller
```bash
python dino_controller.py
# connects to Arduino
# runs gesture inference
# controls Chrome Dino game via wrist movements
```

---

## How The Inference Works

```
Glove sensor streams x,y,z every 100ms via UART
              ↓
Python builds sliding window (20 samples = 2 seconds)
              ↓
extract_features() → time domain + FFT spectral features per axis
              ↓
TFLite model → confidence scores for [duck, idle, jump]
              ↓
if confidence > 85% and not idle and cooldown passed
              ↓
pyautogui presses spacebar or down arrow
              ↓
Chrome Dino jumps or ducks
```

---

## Setup & Requirements

### Firmware
- Atmel Studio 7
- AVR-GCC toolchain (bundled with Atmel Studio)
- Upload tool of your choice (USBasp or bootloader via AVRDUDE)

### Python
```bash
pip install pyserial numpy tensorflow pyautogui pandas
```

### Python Version
Tested on Python 3.13, Windows 11

---

## Playing The Game

```
1. Wear the glove with ADXL345 mounted on back of hand
2. Flash firmware to Arduino
3. Open chrome://dino in Chrome
4. Run: python dino_controller.py
5. Enter your COM port
6. Click on the Dino game window within 5 seconds
7. Flick your wrist and play!
```

---

## Why ATmega328P?

Most gesture ML projects use ESP32 or Raspberry Pi. This project deliberately uses the ATmega328P — one of the most constrained popular MCUs — to demonstrate that good firmware and a clean data pipeline matter more than powerful hardware.

```
ATmega328P specs:
├── Flash  →  32KB
├── RAM    →  2KB
├── Speed  →  16MHz
└── No FPU, no WiFi, no OS
```

The MCU only handles sensor reading and UART streaming. The ML inference runs on PC via Python — a deliberate architecture choice that keeps the firmware lean and portable.

---

## What I Learned

- Bare metal AVR C programming with Atmel Studio from scratch
- I2C protocol implementation using TWI registers directly
- UART communication without libraries
- Hardware debugging — discovered HW-014 module forces I2C via pulled-up CS pin
- Edge Impulse data collection, spectral feature extraction, model training
- TensorFlow Lite inference pipeline in Python
- Connecting embedded firmware to PC software via serial UART
- Building a complete wearable gesture control system end to end

---

## Built With

- Atmel Studio 7 — bare metal AVR C firmware
- Edge Impulse — gesture ML model training
- TensorFlow Lite — Python inference
- PyAutoGUI — keyboard automation
- PySerial — UART communication

---

## License

MIT License — free to use, modify, and share.
