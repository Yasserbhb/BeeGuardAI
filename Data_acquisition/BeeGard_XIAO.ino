#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>

// ------------------- CONFIG WIFI -------------------
const char* ssid = "**********";     // ton Wi-Fi ou hotspot
const char* password = "*********";   // ton mot de passe Wi-Fi

// ------------------- CONFIG EDGE IMPULSE -------------------
const char* EI_API_KEY = "ei_1a6180d3630c85a0089e37a8e115e7fa7adddaba221f2e2254ffdd9f4c584674"; // API Edge Impulse
const char* EI_DEVICE_ID = "xiao-s3-amine";   // nom libre, juste pour identifier ton appareil
const char* EI_LABEL = "bee";   // pour les abeilles
const char* EI_LABEL = "hornet"; // pour les frelons

// ------------------- CAMERA CONFIG -------------------
#define CAMERA_MODEL_XIAO_ESP32S3
#include "camera_pins.h"

void sendToEdgeImpulse(camera_fb_t *fb);
void setupCamera();

void setup() {
  Serial.begin(115200);
  delay(2000);

  // Connexion WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connexion Wi-Fi en cours...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n Wi-Fi connecté");
  Serial.print("IP locale: ");
  Serial.println(WiFi.localIP());

  // Initialiser la caméra
  setupCamera();
}

void loop() {
  Serial.println(" Capture d’image...");
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println(" Erreur capture caméra !");
    delay(5000);
    return;
  }

  // Envoyer vers Edge Impulse
  sendToEdgeImpulse(fb);

  // Libérer la mémoire
  esp_camera_fb_return(fb);
  esp_camera_deinit();
  setupCamera(); // Réinitialiser la caméra pour éviter les erreurs GDMA

  Serial.println(" Caméra réinitialisée !");
  delay(120000);  //  2 min 
}

// =======================================================
//           INITIALISATION DE LA CAMERA
// =======================================================
void setupCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.frame_size = FRAMESIZE_QQVGA;    // 160x120 pour limiter la taille
  config.pixel_format = PIXFORMAT_JPEG;
  config.jpeg_quality = 15;               // qualité JPEG moyenne
  config.fb_count = 1;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;

  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println(" Échec d’initialisation de la caméra !");
    delay(2000);
  } else {
    Serial.println(" Camera initialisée");
  }
}

// =======================================================
//           ENVOI VERS EDGE IMPULSE
// =======================================================
void sendToEdgeImpulse(camera_fb_t *fb) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println(" Wi-Fi non connecté !");
    return;
  }

  HTTPClient http;
  String url = "https://ingestion.edgeimpulse.com/api/training/files";
  http.begin(url);

  String boundary = "----ESP32CAMBOUNDARY";
  String head =
    "--" + boundary + "\r\n"
    "Content-Disposition: form-data; name=\"data\"; filename=\"photo.jpg\"\r\n"
    "Content-Type: image/jpeg\r\n\r\n";
  String tail = "\r\n--" + boundary + "--\r\n";

  int totalLen = head.length() + fb->len + tail.length();

  http.addHeader("Content-Type", "multipart/form-data; boundary=" + boundary);
  http.addHeader("x-api-key", EI_API_KEY);
  http.addHeader("x-device-id", EI_DEVICE_ID);
  http.addHeader("x-label", EI_LABEL);
  http.addHeader("x-file-name", "photo.jpg");
  http.addHeader("Content-Length", String(totalLen));

  WiFiClient *stream = http.getStreamPtr();
  stream->print(head);
  stream->write(fb->buf, fb->len);
  stream->print(tail);

  int httpCode = http.POST((uint8_t *)NULL, 0);
  Serial.printf("Réponse HTTP: %d\n", httpCode);

  if (httpCode == 200 || httpCode == 201) {
    Serial.println(" Image enregistrée sur Edge Impulse !");
  } else {
    Serial.println("Edge Impulse n’a pas accepté l’image (vérifie la clé / label)");
  }

  http.end();
}
