# ESP32 Device Setup Guide

Step-by-step guide to configure and flash your ESP32 device.

---

## Prerequisites

1. **Hardware:**
   - ESP32 DevKit board
   - DHT22 temperature/humidity sensor
   - USB cable (USB-A to Micro-USB or USB-C depending on your ESP32)
   - Optional: IR beam sensors for bee counting

2. **Software:**
   - Arduino IDE (Download: https://www.arduino.cc/en/software)
   - USB drivers for ESP32 (usually auto-installed)

---

## Step 1: Get Your Configuration Info

### A. Get Your Server IP Address

**On Windows:**
```bash
ipconfig
```
Look for "IPv4 Address" under your active network adapter (e.g., `192.168.1.100`)

**On Linux/Mac:**
```bash
ifconfig
# or
ip addr show
```

Your server URL will be: `http://YOUR_IP:3000/api/iot/data`

### B. Generate an API Key

1. Go to http://localhost:3000 (login first)
2. Click **"Clés API"** in the navigation
3. Click **"Générer une clé IoT"**
4. Select a beehive (or leave unassigned)
5. Copy the generated API key (starts with `bga_...`)

### C. Get Your Beehive ID

1. Go to **"Gérer Ruches"** page
2. Find your beehive in the list
3. Note the ID number

---

## Step 2: Install Arduino IDE

1. Download Arduino IDE 2.x from https://www.arduino.cc/en/software
2. Install and open it

---

## Step 3: Add ESP32 Board Support

1. Open Arduino IDE
2. Go to **File → Preferences**
3. In "Additional Board Manager URLs", add:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
4. Click **OK**
5. Go to **Tools → Board → Boards Manager**
6. Search for **"ESP32"**
7. Install **"esp32 by Espressif Systems"**
8. Wait for installation to complete

---

## Step 4: Install Required Libraries

1. Go to **Tools → Manage Libraries** (or press Ctrl+Shift+I)
2. Search and install these libraries:
   - **DHT sensor library** by Adafruit
   - **Adafruit Unified Sensor** by Adafruit (dependency)
   - **ArduinoJson** by Benoit Blanchon

---

## Step 5: Configure the Code

1. Open the file: `embedded/esp32/BeeGuardAI_ESP32.ino` in Arduino IDE
2. Find the configuration section (lines 35-42)
3. Update these values:

```cpp
// WiFi credentials
const char* WIFI_SSID = "YOUR_WIFI_NAME";          // ← Your WiFi network name
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";   // ← Your WiFi password

// BeeGuardAI Server
const char* SERVER_URL = "http://192.168.1.100:3000/api/iot/data";  // ← Your server IP
const char* API_KEY = "bga_abc123xyz456...";        // ← API key from web interface
const int RUCHE_ID = 1;                             // ← Beehive ID from web interface
const char* RUCHE_NAME = "Ruche Jussieu 01";       // ← Your beehive name
```

**Example Configuration:**
```cpp
const char* WIFI_SSID = "MyHomeWiFi";
const char* WIFI_PASSWORD = "MySecurePassword123";
const char* SERVER_URL = "http://192.168.1.50:3000/api/iot/data";
const char* API_KEY = "bga_1a2b3c4d5e6f7g8h9i0j";
const int RUCHE_ID = 1;
const char* RUCHE_NAME = "Ruche Test 01";
```

---

## Step 6: Connect ESP32 and Flash

1. **Connect ESP32** to your computer via USB cable
2. In Arduino IDE:
   - Go to **Tools → Board → ESP32 Arduino**
   - Select your board (e.g., **"ESP32 Dev Module"**)
3. Go to **Tools → Port**
   - Select the COM port (Windows: `COM3`, `COM4`, etc.)
   - Mac/Linux: `/dev/ttyUSB0` or `/dev/cu.usbserial-*`
4. Click the **Upload** button (→) at the top
5. Wait for compilation and upload (takes 1-2 minutes)

**Expected output:**
```
Connecting....
Writing at 0x00001000... (100%)
Wrote 234560 bytes in 20.5 seconds
Hard resetting via RTS pin...
```

---

## Step 7: Verify It's Working

### A. Open Serial Monitor

1. Go to **Tools → Serial Monitor**
2. Set baud rate to **115200**
3. You should see:

```
========================================
  BeeGuardAI - ESP32 Client
========================================

✓ DHT22 sensor initialized
Connecting to WiFi: MyHomeWiFi
✓ WiFi connected! IP: 192.168.1.105

--- Configuration ---
Server: http://192.168.1.50:3000/api/iot/data
API Key: bga_1a2b3c4d5e6f7g8h9i0j
Ruche ID: 1
Ruche Name: Ruche Test 01

✓ System ready! Sending data every 5 minutes...

[12:34:56] Temp: 24.5°C, Humidity: 65%, Bees In: 3, Bees Out: 2
→ Sending to server...
✓ Data sent successfully! HTTP 200
```

### B. Check Dashboard

1. Go to http://localhost:3000
2. You should see your beehive data updating!
3. Check the terminal where you ran `npm run dev` for logs:

```
📊 [POST /api/iot/data] Ruche 1 - Frelons: 0, Temp: 24.5°C
```

---

## Troubleshooting

### WiFi Connection Issues

**Problem:** `WiFi connection failed`

**Solution:**
- Check WiFi SSID and password are correct
- Make sure ESP32 is within WiFi range
- Try 2.4GHz WiFi (ESP32 doesn't support 5GHz)

### Upload Failed

**Problem:** `Failed to connect to ESP32`

**Solution:**
- Hold down the **BOOT** button on ESP32 while uploading
- Try a different USB cable (some are charge-only)
- Check the correct COM port is selected

### Server Connection Failed

**Problem:** `HTTP POST failed: Connection refused`

**Solution:**
- Make sure your server is running (`npm run dev`)
- Check the server IP is correct (use `ipconfig` / `ifconfig`)
- Ensure ESP32 and server are on the same network
- Try pinging the server from ESP32's IP

### No Data on Dashboard

**Problem:** Data not appearing on dashboard

**Solution:**
- Check API key is valid (generate a new one if needed)
- Verify RUCHE_ID matches a beehive in your database
- Check server logs for errors
- Open Serial Monitor to see ESP32 status

---

## Hardware Wiring (Optional Sensors)

### DHT22 Temperature/Humidity Sensor

```
DHT22          ESP32
------        -------
VCC    →      3.3V
GND    →      GND
DATA   →      GPIO 4
```

### IR Beam Break Sensors (Bee Counting)

```
IR Sensor IN    ESP32         IR Sensor OUT    ESP32
-------------   -------       --------------   -------
VCC      →      3.3V          VCC       →      3.3V
GND      →      GND           GND       →      GND
OUT      →      GPIO 5        OUT       →      GPIO 18
```

---

## Testing Without Physical Sensors

The code will work even without sensors connected! It will send simulated data:
- Temperature: Random between 20-28°C
- Humidity: Random between 50-70%
- Bee counts: Random values
- Hornets: 0 (requires camera + Edge Impulse)

This is perfect for testing the connection before adding real sensors.

---

## Next Steps

Once your device is connected and sending data:

1. **Add More Devices**: Flash more ESP32s with different `RUCHE_ID` values
2. **Add Real Sensors**: Wire up DHT22 and IR sensors as shown above
3. **Add Camera**: Integrate Edge Impulse model for hornet detection
4. **Switch to LoRaWAN**: For longer range (see LoRaWAN setup guide)

---

## Support

If you encounter issues:
1. Check Serial Monitor output (115200 baud)
2. Check server terminal logs
3. Verify all configuration values are correct
4. Make sure firewall isn't blocking port 3000
