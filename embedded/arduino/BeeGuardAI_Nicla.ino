/*
 * BeeGuardAI - Arduino Nicla Vision Client
 *
 * Optimized for Arduino Nicla Vision board
 * - Built-in camera for Edge Impulse AI
 * - WiFi connectivity
 * - Microphone for acoustic analysis
 *
 * Instructions:
 * 1. Open Arduino IDE
 * 2. Install board: Tools > Board > Boards Manager > "Arduino Mbed OS Nicla Boards"
 * 3. Install libraries: WiFiNINA, ArduinoJson
 * 4. Configure WiFi and server below
 * 5. Upload to Nicla Vision
 */

#include <WiFiNINA.h>
#include <ArduinoHttpClient.h>
#include <ArduinoJson.h>

// ============================================
// CONFIGURATION - FILL THESE IN!
// ============================================

// WiFi credentials
const char* WIFI_SSID = "YOUR_WIFI_NAME";          // ← Change this!
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";   // ← Change this!

// BeeGuardAI Server (your computer's IP)
const char* SERVER_HOST = "192.168.1.100";         // ← Your server IP (without http://)
const int SERVER_PORT = 3000;                       // ← Server port
const char* API_KEY = "bga_your_api_key_here";     // ← From "Clés API" page
const int RUCHE_ID = 1;                            // ← From "Gérer Ruches" page

// How often to send data (milliseconds)
const unsigned long SEND_INTERVAL = 300000;  // 5 minutes (300000ms)

// ============================================
// GLOBAL VARIABLES
// ============================================

WiFiClient wifi;
HttpClient client = HttpClient(wifi, SERVER_HOST, SERVER_PORT);

// Counters
int beesEntered = 0;
int beesExited = 0;
int hornetsDetected = 0;
float temperature = 0.0;
float humidity = 0.0;

// Timing
unsigned long lastSendTime = 0;

// Status
int wifiStatus = WL_IDLE_STATUS;

// ============================================
// SETUP
// ============================================

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 3000); // Wait up to 3 seconds for Serial

  Serial.println("\n\n========================================");
  Serial.println("  BeeGuardAI - Nicla Vision Client");
  Serial.println("========================================\n");

  // Built-in LED (RGB on Nicla)
  pinMode(LED_BUILTIN, OUTPUT);
  blinkLED(3); // 3 quick blinks on startup

  // Connect to WiFi
  connectWiFi();

  // Print configuration
  Serial.println("\n--- Configuration ---");
  Serial.print("Server: http://");
  Serial.print(SERVER_HOST);
  Serial.print(":");
  Serial.print(SERVER_PORT);
  Serial.println("/api/iot/data");
  Serial.print("API Key: ");
  Serial.println(API_KEY);
  Serial.print("Ruche ID: ");
  Serial.println(RUCHE_ID);
  Serial.println("Send Interval: 5 minutes");

  Serial.println("\n✓ System ready! Starting data collection...\n");
}

// ============================================
// MAIN LOOP
// ============================================

void loop() {
  unsigned long currentTime = millis();

  // Check if it's time to send data
  if (currentTime - lastSendTime >= SEND_INTERVAL) {
    lastSendTime = currentTime;

    // Collect sensor data
    collectData();

    // Send to server
    sendDataToServer();

    // Reset counters after sending
    beesEntered = 0;
    beesExited = 0;
    hornetsDetected = 0;
  }

  // TODO: Add your Edge Impulse inference here
  // runEdgeImpulseInference();

  // TODO: Add bee counting logic here
  // countBees();

  delay(100); // Small delay
}

// ============================================
// WiFi CONNECTION
// ============================================

void connectWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);

  // Check for WiFi module
  if (WiFi.status() == WL_NO_MODULE) {
    Serial.println("✗ WiFi module not found!");
    while (true) {
      blinkLED(1);
      delay(1000);
    }
  }

  // Attempt to connect
  int attempts = 0;
  while (wifiStatus != WL_CONNECTED && attempts < 20) {
    wifiStatus = WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    Serial.print(".");
    delay(500);
    attempts++;
  }

  if (wifiStatus == WL_CONNECTED) {
    Serial.println("\n✓ WiFi connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    blinkLED(2); // 2 blinks for success
  } else {
    Serial.println("\n✗ WiFi connection failed!");
    Serial.println("Check your SSID and password");
    while (true) {
      blinkLED(1);
      delay(1000);
    }
  }
}

// ============================================
// DATA COLLECTION
// ============================================

void collectData() {
  // Simulate sensor readings (replace with real sensors)
  // TODO: Replace with actual sensor readings

  // Random temperature (20-28°C)
  temperature = 20.0 + random(0, 80) / 10.0;

  // Random humidity (50-70%)
  humidity = 50.0 + random(0, 200) / 10.0;

  // Random bee activity
  beesEntered += random(20, 60);
  beesExited += random(15, 55);

  // Random hornets (0-3)
  hornetsDetected += random(0, 4);

  // Print collected data
  Serial.println("\n--- Data Collected ---");
  Serial.print("Temperature: ");
  Serial.print(temperature, 1);
  Serial.println("°C");
  Serial.print("Humidity: ");
  Serial.print(humidity, 0);
  Serial.println("%");
  Serial.print("Bees Entered: ");
  Serial.println(beesEntered);
  Serial.print("Bees Exited: ");
  Serial.println(beesExited);
  Serial.print("Hornets: ");
  Serial.println(hornetsDetected);
}

// ============================================
// SEND DATA TO SERVER
// ============================================

void sendDataToServer() {
  Serial.println("\n→ Sending data to server...");

  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("✗ WiFi disconnected! Reconnecting...");
    connectWiFi();
    return;
  }

  // Create JSON payload
  // IMPORTANT: This format matches EXACTLY what the database expects!
  StaticJsonDocument<512> doc;

  doc["api_key"] = API_KEY;
  doc["ruche_id"] = RUCHE_ID;
  doc["nombre_frelons"] = hornetsDetected;
  doc["nombre_abeilles_entrees"] = beesEntered;
  doc["nombre_abeilles_sorties"] = beesExited;
  doc["temperature"] = temperature;
  doc["humidite"] = humidity;
  doc["etat_abeilles"] = (hornetsDetected > 5) ? "affaiblies" : "normal";
  doc["etat_acoustique"] = (hornetsDetected > 0) ? "stress" : "normal";

  // Serialize JSON to string
  String jsonPayload;
  serializeJson(doc, jsonPayload);

  Serial.println("JSON Payload:");
  Serial.println(jsonPayload);

  // Make HTTP POST request
  client.beginRequest();
  client.post("/api/iot/data");
  client.sendHeader("Content-Type", "application/json");
  client.sendHeader("Content-Length", jsonPayload.length());
  client.beginBody();
  client.print(jsonPayload);
  client.endRequest();

  // Get response
  int statusCode = client.responseStatusCode();
  String response = client.responseBody();

  Serial.print("Response Code: ");
  Serial.println(statusCode);

  if (statusCode == 200) {
    Serial.println("✓ Data sent successfully!");
    Serial.print("Server response: ");
    Serial.println(response);
    blinkLED(2); // Success
  } else {
    Serial.println("✗ Failed to send data!");
    Serial.print("Error: ");
    Serial.println(response);
    blinkLED(5); // Error
  }

  client.stop();
}

// ============================================
// LED BLINK UTILITY
// ============================================

void blinkLED(int times) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(100);
    digitalWrite(LED_BUILTIN, LOW);
    delay(100);
  }
}

// ============================================
// EDGE IMPULSE INFERENCE (TODO)
// ============================================

/*
void runEdgeImpulseInference() {
  // TODO: Add Edge Impulse code here
  //
  // Example:
  // 1. Capture image from camera
  // 2. Run inference
  // 3. Get prediction results
  // 4. Update hornetsDetected counter
  //
  // if (result.classification[0].value > 0.8) {
  //   hornetsDetected++;
  // }
}
*/

// ============================================
// BEE COUNTING (TODO)
// ============================================

/*
void countBees() {
  // TODO: Add bee counting logic here
  //
  // Options:
  // 1. IR beam break sensors
  // 2. Computer vision (count bees in frame)
  // 3. Manual simulation for testing
  //
  // beesEntered++;
  // beesExited++;
}
*/
