/*
 * BeeGuardAI - ESP32 Client
 *
 * This is the ACTUAL code you flash to your ESP32 device
 * Place this on each beehive to monitor in real-time
 *
 * Hardware Requirements:
 * - ESP32 DevKit board
 * - DHT22 sensor (temperature/humidity)
 * - 2x IR beam break sensors (bee counting)
 * - Camera module (optional, for hornet detection)
 *
 * Instructions:
 * 1. Open Arduino IDE
 * 2. Install ESP32 board support:
 *    Tools > Board > Boards Manager > Search "ESP32" > Install
 * 3. Install libraries:
 *    - DHT sensor library by Adafruit
 *    - ArduinoJson by Benoit Blanchon
 * 4. Fill in WiFi credentials below
 * 5. Fill in your BeeGuardAI server details
 * 6. Upload to ESP32
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

// ============================================
// CONFIGURATION - FILL THESE IN!
// ============================================

// WiFi credentials
const char* WIFI_SSID = "YOUR_WIFI_NAME";          // ← Change this!
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";   // ← Change this!

// BeeGuardAI Server (get these from web interface)
const char* SERVER_URL = "http://192.168.1.100:3000/api/iot/data";  // ← Your server IP
const char* API_KEY = "bga_your_api_key_here";      // ← From "Gérer Ruches" page
const int RUCHE_ID = 1;                             // ← From "Gérer Ruches" page
const char* RUCHE_NAME = "Ruche Jussieu 01";       // ← Your hive name

// Sensor pins
#define DHT_PIN 4              // DHT22 connected to GPIO 4
#define DHT_TYPE DHT22
#define IR_SENSOR_IN 5         // IR sensor for bees entering (GPIO 5)
#define IR_SENSOR_OUT 18       // IR sensor for bees exiting (GPIO 18)
#define LED_PIN 2              // Built-in LED for status

// How often to send data (milliseconds)
const unsigned long SEND_INTERVAL = 300000;  // 5 minutes

// ============================================
// GLOBAL VARIABLES
// ============================================

DHT dht(DHT_PIN, DHT_TYPE);
HTTPClient http;

// Counters
int beesEntered = 0;
int beesExited = 0;
int hornetsDetected = 0;

// Timing
unsigned long lastSendTime = 0;
unsigned long lastPrintTime = 0;

// IR sensor states (for edge detection)
bool lastIRStateIn = HIGH;
bool lastIRStateOut = HIGH;

// ============================================
// SETUP
// ============================================

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n\n========================================");
  Serial.println("  BeeGuardAI - ESP32 Client");
  Serial.println("========================================");
  Serial.println();

  // Setup pins
  pinMode(LED_PIN, OUTPUT);
  pinMode(IR_SENSOR_IN, INPUT_PULLUP);
  pinMode(IR_SENSOR_OUT, INPUT_PULLUP);

  // Initialize DHT sensor
  dht.begin();
  Serial.println("✓ DHT22 sensor initialized");

  // Connect to WiFi
  connectWiFi();

  // Verify configuration
  Serial.println("\n--- Configuration ---");
  Serial.print("Ruche ID: ");
  Serial.println(RUCHE_ID);
  Serial.print("Ruche Name: ");
  Serial.println(RUCHE_NAME);
  Serial.print("Server: ");
  Serial.println(SERVER_URL);
  Serial.print("API Key: ");
  Serial.print(String(API_KEY).substring(0, 10));
  Serial.println("...");
  Serial.println("-------------------\n");

  Serial.println("✓ System ready! Starting monitoring...\n");

  // Send initial data
  sendDataToServer();
}

// ============================================
// MAIN LOOP
// ============================================

void loop() {
  unsigned long currentTime = millis();

  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠ WiFi disconnected! Reconnecting...");
    connectWiFi();
  }

  // Count bees passing through IR sensors
  countBees();

  // Send data periodically
  if (currentTime - lastSendTime >= SEND_INTERVAL) {
    sendDataToServer();
    lastSendTime = currentTime;

    // Reset counters after sending
    beesEntered = 0;
    beesExited = 0;
    hornetsDetected = 0;
  }

  // Print status every 10 seconds
  if (currentTime - lastPrintTime >= 10000) {
    printStatus();
    lastPrintTime = currentTime;
  }

  // Blink LED to show activity
  blinkLED();

  delay(10);  // Small delay to prevent sensor reading errors
}

// ============================================
// WIFI CONNECTION
// ============================================

void connectWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));  // Blink while connecting
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✓ WiFi connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("Signal strength: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
    digitalWrite(LED_PIN, HIGH);  // LED on when connected
  } else {
    Serial.println("\n✗ WiFi connection failed!");
    Serial.println("Check your SSID and password");
    digitalWrite(LED_PIN, LOW);
  }
}

// ============================================
// BEE COUNTING (IR Sensors)
// ============================================

void countBees() {
  // Read IR sensors (LOW = beam broken = bee detected)
  bool currentIRStateIn = digitalRead(IR_SENSOR_IN);
  bool currentIRStateOut = digitalRead(IR_SENSOR_OUT);

  // Detect bee entering (beam broken on IN sensor)
  if (lastIRStateIn == HIGH && currentIRStateIn == LOW) {
    beesEntered++;
    Serial.println("→ Bee entering");
  }
  lastIRStateIn = currentIRStateIn;

  // Detect bee exiting (beam broken on OUT sensor)
  if (lastIRStateOut == HIGH && currentIRStateOut == LOW) {
    beesExited++;
    Serial.println("← Bee exiting");
  }
  lastIRStateOut = currentIRStateOut;
}

// ============================================
// SEND DATA TO SERVER
// ============================================

void sendDataToServer() {
  Serial.println("\n--- Sending Data ---");

  // Read temperature and humidity
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  // Check if readings are valid
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("✗ Failed to read from DHT sensor!");
    temperature = 0;
    humidity = 0;
  }

  // In a real system, you'd get hornets from camera/ML model
  // For now, we simulate occasional hornet detection
  if (random(0, 100) < 20) {  // 20% chance
    hornetsDetected = random(1, 5);
  }

  // Create JSON payload
  StaticJsonDocument<256> doc;
  doc["ruche_id"] = RUCHE_ID;
  doc["nombre_frelons"] = hornetsDetected;
  doc["nombre_abeilles_entrees"] = beesEntered;
  doc["nombre_abeilles_sorties"] = beesExited;
  doc["temperature"] = temperature;
  doc["humidite"] = humidity;
  doc["etat_abeilles"] = beesEntered > 10 ? "actif" : "calme";
  doc["etat_acoustique"] = "normal";

  String jsonString;
  serializeJson(doc, jsonString);

  Serial.println("Payload: " + jsonString);

  // Send HTTP POST request
  if (WiFi.status() == WL_CONNECTED) {
    http.begin(SERVER_URL);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-API-Key", API_KEY);

    int httpCode = http.POST(jsonString);

    if (httpCode > 0) {
      Serial.print("✓ Server response: ");
      Serial.println(httpCode);

      if (httpCode == 200) {
        String response = http.getString();
        Serial.println("✓ Data sent successfully!");
        Serial.println("Response: " + response);
      }
    } else {
      Serial.print("✗ HTTP error: ");
      Serial.println(http.errorToString(httpCode));
    }

    http.end();
  } else {
    Serial.println("✗ WiFi not connected, cannot send data");
  }

  Serial.println("-------------------\n");
}

// ============================================
// STATUS PRINTING
// ============================================

void printStatus() {
  Serial.println("--- Status ---");
  Serial.print("Time: ");
  Serial.print(millis() / 1000);
  Serial.println("s");

  Serial.print("WiFi: ");
  Serial.print(WiFi.status() == WL_CONNECTED ? "Connected" : "Disconnected");
  Serial.print(" (");
  Serial.print(WiFi.RSSI());
  Serial.println(" dBm)");

  float temp = dht.readTemperature();
  float hum = dht.readHumidity();
  Serial.print("Temp: ");
  Serial.print(temp);
  Serial.print("°C | Humidity: ");
  Serial.print(hum);
  Serial.println("%");

  Serial.print("Bees in: ");
  Serial.print(beesEntered);
  Serial.print(" | Bees out: ");
  Serial.println(beesExited);

  Serial.print("Next send in: ");
  Serial.print((SEND_INTERVAL - (millis() - lastSendTime)) / 1000);
  Serial.println("s");

  Serial.println("-------------\n");
}

// ============================================
// LED BLINK
// ============================================

void blinkLED() {
  static unsigned long lastBlink = 0;
  if (millis() - lastBlink > 1000) {
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
    lastBlink = millis();
  }
}

/*
 * ============================================
 * DEPLOYMENT STEPS FOR REAL BEEHIVE:
 * ============================================
 *
 * 1. HARDWARE SETUP:
 *    - Connect DHT22 sensor to GPIO 4
 *    - Connect IR sensors to GPIO 5 and 18
 *    - Add solar panel + battery for power
 *    - Waterproof enclosure for electronics
 *
 * 2. SOFTWARE SETUP:
 *    - Go to http://your-server:3000/manage-ruches.html
 *    - Add a new ruche, copy the API key and Ruche ID
 *    - Paste them into this sketch above
 *    - Add your WiFi credentials
 *    - Change SERVER_URL to your server's IP
 *
 * 3. UPLOAD:
 *    - Connect ESP32 via USB
 *    - Select board: ESP32 Dev Module
 *    - Select correct COM port
 *    - Click Upload
 *
 * 4. DEPLOY:
 *    - Place in waterproof box
 *    - Mount near beehive entrance
 *    - Position sensors to detect bee traffic
 *    - Connect power
 *
 * 5. MONITOR:
 *    - Open Serial Monitor (115200 baud) to see logs
 *    - Check dashboard at http://your-server:3000
 *    - Data should appear every 5 minutes
 *
 * ============================================
 * TROUBLESHOOTING:
 * ============================================
 *
 * Problem: WiFi won't connect
 * Solution: Check SSID/password, ensure 2.4GHz WiFi
 *
 * Problem: "API Key invalid"
 * Solution: Copy API key again from web interface
 *
 * Problem: DHT sensor returns NaN
 * Solution: Check wiring, add 10kΩ pull-up resistor
 *
 * Problem: No data on dashboard
 * Solution: Check server IP is accessible from ESP32
 *           Ping the server from same WiFi network
 *
 * ============================================
 */
