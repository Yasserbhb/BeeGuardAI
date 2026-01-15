# Embedded Systems - BeeGuardAI

This directory contains the embedded code for IoT devices used in the BeeGuardAI project.

## 📁 Structure

```
embedded/
├── esp32/              # ESP32-based implementations
│   └── BeeGuardAI_ESP32.ino
└── arduino/            # Arduino Nicla Vision implementations
```

## 🔧 Hardware Options

### Option A: XIAO ESP32-S3 Sense
**Recommended for**: Cost-effective deployment, large scale

**Components:**
- Seeed Studio XIAO ESP32-S3 Sense (camera integrated)
- LiPo Rider Pro (power management)
- Li-Po Battery 3.7V (1000-2000 mAh)
- Solar panel 6V / 1-2W
- microSD card (8-32 GB for local storage)
- USB-C cable (programming & power)
- Waterproof enclosure

**Specs:**
- MCU: ESP32-S3
- Camera: OV2640 (2MP)
- Storage: 8MB PSRAM, 8MB Flash
- WiFi: 802.11 b/g/n
- Bluetooth: BLE 5.0

### Option B: Arduino Nicla Vision
**Recommended for**: Advanced features, professional deployment

**Components:**
- Arduino Nicla Vision
- LiPo Rider Pro or equivalent
- Li-Po Battery 3.7V
- Solar panel 5-6V
- USB cable (programming)
- Waterproof enclosure

**Specs:**
- MCU: STM32H747 (dual-core Cortex-M7 + M4)
- Camera: GC2145 (2MP)
- WiFi: Murata 1DX module
- Bluetooth: BLE 5.0
- Integrated 6-axis IMU
- Integrated microphone

## 🚀 Getting Started

### 1. Install Arduino IDE
Download from [arduino.cc](https://www.arduino.cc/en/software)

### 2. Add Board Support

#### For ESP32:
1. File → Preferences
2. Add to "Additional Board Manager URLs":
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
3. Tools → Board → Boards Manager
4. Search "ESP32" and install

#### For Arduino Nicla Vision:
1. File → Preferences
2. Add to "Additional Board Manager URLs":
   ```
   https://downloads.arduino.cc/packages/package_index.json
   ```
3. Tools → Board → Boards Manager
4. Search "Arduino Mbed OS Nicla Boards" and install

### 3. Install Required Libraries

Go to Sketch → Include Library → Manage Libraries

**Common libraries:**
- `ArduinoJson` - JSON parsing
- `DHT sensor library` - Temperature/humidity sensors
- `Adafruit BME280 Library` - Alternative temp/humidity sensor

**For LoRaWAN:**
- `MCCI LoRaWAN LMIC library` (ESP32)
- `MKRWAN` (for Arduino MKR boards if used as gateway)

**For Edge Impulse:**
- Download SDK from your Edge Impulse project
- Add as ZIP library

### 4. Configure and Upload

1. Open the `.ino` file for your board
2. Update configuration:
   ```cpp
   // WiFi credentials (if using WiFi instead of LoRaWAN)
   const char* ssid = "YOUR_SSID";
   const char* password = "YOUR_PASSWORD";

   // Server endpoint
   const char* serverUrl = "http://your-server.com:3000";
   const char* apiKey = "YOUR_API_KEY";

   // LoRaWAN keys (if using LoRaWAN)
   const char* devEui = "YOUR_DEV_EUI";
   const char* appEui = "YOUR_APP_EUI";
   const char* appKey = "YOUR_APP_KEY";
   ```

3. Select board:
   - Tools → Board → ESP32 Arduino → XIAO_ESP32S3
   - OR Tools → Board → Arduino Mbed OS Nicla Boards → Arduino Nicla Vision

4. Select port: Tools → Port → (your device port)

5. Upload: Sketch → Upload (or Ctrl+U)

## 🤖 Edge Impulse Integration

### Training Your Model

1. **Create Edge Impulse Account**: [edgeimpulse.com](https://edgeimpulse.com)

2. **Create Project**:
   - New Project → Select "Computer Vision" or "Audio"
   - Choose "Object Detection" for bee/hornet detection
   - Choose "Classification" for acoustic analysis

3. **Collect Data**:
   - Data Acquisition → Connect your device
   - Or upload images/audio from local dataset
   - Label your data:
     - Classes: `abeille`, `frelon`, `abeille_morte`, `vide`

4. **Design Impulse**:
   - Image: 96x96 or 160x160 (depending on memory)
   - Processing block: Image or MFCC (for audio)
   - Learning block: Object Detection (FOMO) or Transfer Learning

5. **Train Model**:
   - Generate features
   - Train neural network
   - Optimize (quantization for TinyML)

6. **Deploy**:
   - Deployment → Arduino library
   - Download ZIP
   - Add to Arduino IDE: Sketch → Include Library → Add .ZIP Library

7. **Use in Code**:
   ```cpp
   #include <your_project_inferencing.h>

   void runInference() {
       // Capture image or audio
       // Run inference
       ei_impulse_result_t result;
       run_classifier(&signal, &result, false);

       // Process results
       for (size_t ix = 0; ix < EI_CLASSIFIER_LABEL_COUNT; ix++) {
           if (result.classification[ix].value > 0.6) {
               // Detection found!
           }
       }
   }
   ```

## 📡 LoRaWAN Setup

### Hardware Requirements
- LoRa module (e.g., RFM95W, SX1276)
- Antenna (868 MHz for EU, 915 MHz for US)
- Gateway (The Things Network compatible)

### The Things Network Setup

1. Create account on [thethingsnetwork.org](https://www.thethingsnetwork.org)

2. Add Gateway (if you have one):
   - Console → Gateways → Add Gateway
   - Note Gateway EUI

3. Add Application:
   - Console → Applications → Add Application
   - Note Application ID

4. Register Device:
   - In your application → End Devices → Add End Device
   - Select "Manually"
   - LoRaWAN version: 1.0.3 (or higher)
   - Note: DevEUI, AppEUI, AppKey

5. Configure in Code:
   ```cpp
   static const u1_t PROGMEM APPEUI[8] = { YOUR_APP_EUI };
   static const u1_t PROGMEM DEVEUI[8] = { YOUR_DEV_EUI };
   static const u1_t PROGMEM APPKEY[16] = { YOUR_APP_KEY };
   ```

### Payload Format

To minimize bandwidth, send only processed results:

```cpp
// Pack data efficiently (example)
byte payload[12];
payload[0] = (byte)hornets_count;           // 1 byte
payload[1] = (byte)bees_in;                 // 1 byte
payload[2] = (byte)bees_out;                // 1 byte
payload[3] = (byte)(temperature * 10);      // 1 byte (0.1°C precision)
payload[4] = (byte)humidity;                // 1 byte
payload[5] = (byte)bee_state;               // 1 byte (enum)
payload[6] = (byte)acoustic_state;          // 1 byte (enum)

LMIC_setTxData2(1, payload, sizeof(payload), 0);
```

## 🔋 Power Management

### Solar + Battery Setup

```cpp
// Check battery level
int batteryLevel = analogRead(BATTERY_PIN);
float voltage = batteryLevel * (3.3 / 4095.0) * 2; // Voltage divider

if (voltage < 3.3) {
    // Low battery: reduce frequency, disable camera
    enableDeepSleep(60 * 60 * 1000); // 1 hour
} else {
    // Normal: run detection every 5 minutes
    enableDeepSleep(5 * 60 * 1000);
}
```

### Deep Sleep
```cpp
// ESP32 deep sleep
esp_sleep_enable_timer_wakeup(TIME_TO_SLEEP * 1000000);
esp_deep_sleep_start();
```

## 🐛 Troubleshooting

### Camera Not Working
- Check connections
- Verify camera is enabled in code
- Try lower resolution

### LoRaWAN Not Connecting
- Verify keys (DevEUI, AppEUI, AppKey)
- Check antenna connection
- Ensure gateway is in range
- Check frequency band (868/915 MHz)

### Out of Memory
- Reduce image resolution
- Use quantized models
- Enable PSRAM if available

### Model Accuracy Low
- Collect more training data
- Increase model size
- Adjust detection threshold

## 📚 Resources

- [Edge Impulse Documentation](https://docs.edgeimpulse.com/)
- [ESP32 Arduino Core](https://docs.espressif.com/projects/arduino-esp32/en/latest/)
- [Arduino Nicla Vision Docs](https://docs.arduino.cc/hardware/nicla-vision)
- [The Things Network Docs](https://www.thethingsnetwork.org/docs/)
- [LoRaWAN Specification](https://lora-alliance.org/resource_hub/lorawan-specification-v1-0-3/)

## 🤝 Contributing

When adding new embedded features:
1. Create a new branch
2. Test thoroughly on hardware
3. Document power consumption
4. Update this README
5. Submit PR with test results

---

**Note**: Always test in a controlled environment before deploying to beehives!
