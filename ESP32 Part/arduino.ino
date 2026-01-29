#include <BeeGuardAI_inferencing.h>
#include "esp_camera.h"
#include "esp_heap_caps.h"
#include <DHT.h>

// --- CONFIGURATION CAPTEURS ---
#define DHTPIN 4     
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);
#define LoraSerial Serial1 

// --- STRUCTURE POUR LE FILTRE ANTI-DOUBLON ---
struct Point {
    int x;
    int y;
};

// --- CONFIGURATION PINS XIAO ESP32-S3 SENSE ---
#define PWDN_GPIO_NUM     -1
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM     10
#define SIOD_GPIO_NUM     40
#define SIOC_GPIO_NUM     39
#define Y9_GPIO_NUM       48
#define Y8_GPIO_NUM       11
#define Y7_GPIO_NUM       12
#define Y6_GPIO_NUM       14
#define Y5_GPIO_NUM       16
#define Y4_GPIO_NUM       18
#define Y3_GPIO_NUM       17
#define Y2_GPIO_NUM       15
#define VSYNC_GPIO_NUM    38
#define HREF_GPIO_NUM     47
#define PCLK_GPIO_NUM     13

static uint8_t *snapshot_buf = nullptr;

camera_config_t camera_config = {
    .pin_pwdn = PWDN_GPIO_NUM,
    .pin_reset = RESET_GPIO_NUM,
    .pin_xclk = XCLK_GPIO_NUM,
    .pin_sscb_sda = SIOD_GPIO_NUM,
    .pin_sscb_scl = SIOC_GPIO_NUM,
    .pin_d7 = Y9_GPIO_NUM,
    .pin_d6 = Y8_GPIO_NUM,
    .pin_d5 = Y7_GPIO_NUM,
    .pin_d4 = Y6_GPIO_NUM,
    .pin_d3 = Y5_GPIO_NUM,
    .pin_d2 = Y4_GPIO_NUM,
    .pin_d1 = Y3_GPIO_NUM,
    .pin_d0 = Y2_GPIO_NUM,
    .pin_vsync = VSYNC_GPIO_NUM,
    .pin_href = HREF_GPIO_NUM,
    .pin_pclk = PCLK_GPIO_NUM,
    .xclk_freq_hz = 20000000,
    .ledc_timer = LEDC_TIMER_0,
    .ledc_channel = LEDC_CHANNEL_0,
    .pixel_format = PIXFORMAT_RGB565,
    .frame_size = FRAMESIZE_240X240,
    .fb_count = 1,
    .fb_location = CAMERA_FB_IN_PSRAM,
    .grab_mode = CAMERA_GRAB_LATEST
};

// --- FONCTIONS LORA ---
void sendATCommand(String cmd) {
    LoraSerial.println(cmd);
    delay(500);
    while (LoraSerial.available()) {
        Serial.print((char)LoraSerial.read());
    }
}

// --- FONCTION DE RÉCUPÉRATION D'IMAGE ---
static int ei_camera_get_data(size_t offset, size_t length, float *out_ptr) {
    uint8_t *buf = snapshot_buf + (offset * 2);
    for (size_t i = 0; i < length; i++) {
        uint16_t pixel = (buf[0] << 8) | buf[1];
        uint8_t r = ((pixel >> 11) & 0x1F) << 3;
        uint8_t g = ((pixel >> 5) & 0x3F) << 2;
        uint8_t b = (pixel & 0x1F) << 3;
        out_ptr[i] = (float)((r << 16) | (g << 8) | b);
        buf += 2;
    }
    return 0;
}

// --- TACHE 1 : IA AVEC FILTRE ANTI-DOUBLON ---
void inference_task(void *pvParameters) {
    while (1) {
        // 1. Prise de la photo
        camera_fb_t *fb = esp_camera_fb_get();
        if (!fb) { vTaskDelay(pdMS_TO_TICKS(100)); continue; }
        memcpy(snapshot_buf, fb->buf, fb->len);
        esp_camera_fb_return(fb);

        ei::signal_t signal;
        signal.total_length = EI_CLASSIFIER_INPUT_WIDTH * EI_CLASSIFIER_INPUT_HEIGHT;
        signal.get_data = &ei_camera_get_data;

        ei_impulse_result_t result = {0};
        
        // 2. Lancement de l'analyse
        if (run_classifier(&signal, &result, false) == EI_IMPULSE_OK) {
            
            // Stockage pour les frelons uniques trouvés (max 20 pour éviter dépassement mémoire)
            Point frelons_valides[20]; 
            int nombre_frelons_reels = 0; 

            // 3. Boucle sur TOUTES les détections brutes de l'IA
            for (size_t i = 0; i < result.bounding_boxes_count; i++) {
                
                // Filtre de confiance (on prend large à 0.5, le filtre de distance fera le tri)
                if (result.bounding_boxes[i].value < 0.5) continue;

                String label = String(result.bounding_boxes[i].label);
                
                // On ne s'intéresse qu'aux frelons
                if (label.equalsIgnoreCase("hornet") || label.equalsIgnoreCase("frelon")) {
                    
                    // Calcul du centre de la boîte détectée
                    int centre_x = result.bounding_boxes[i].x + (result.bounding_boxes[i].width / 2);
                    int centre_y = result.bounding_boxes[i].y + (result.bounding_boxes[i].height / 2);
                    
                    bool est_un_doublon = false;

                    // 4. Vérification : est-ce que ce point est trop proche d'un frelon déjà compté ?
                    for (int j = 0; j < nombre_frelons_reels; j++) {
                        int dist_x = abs(centre_x - frelons_valides[j].x);
                        int dist_y = abs(centre_y - frelons_valides[j].y);

                        // SEUIL : Si moins de 40 pixels de distance, c'est le même frelon !
                        if (dist_x < 40 && dist_y < 40) {
                            est_un_doublon = true;
                            break; 
                        }
                    }

                    // 5. Si ce n'est pas un doublon, on l'ajoute à la liste des "Vrais" frelons
                    if (!est_un_doublon) {
                        if (nombre_frelons_reels < 20) {
                            frelons_valides[nombre_frelons_reels].x = centre_x;
                            frelons_valides[nombre_frelons_reels].y = centre_y;
                            nombre_frelons_reels++;
                            
                            Serial.printf("   -> Frelon unique détecté (X:%d Y:%d)\n", centre_x, centre_y);
                        }
                    }
                }
            }

            // 6. Envoi du résultat final (filtré)
            if (nombre_frelons_reels > 0) {
                float t = dht.readTemperature();
                if (isnan(t)) t = 0.0;

                Serial.printf("🎯 ALERTE VALIDÉE : %d frelons réels ! | T:%.1f\n", nombre_frelons_reels, t);
                
                // Envoi LoRa
                LoraSerial.printf("AT+MSG=\"ALERTE Frelon Cnt:%d T:%.1f\"\n", nombre_frelons_reels, t);
                
                // Pause de 10s après une alerte pour ne pas saturer
                vTaskDelay(pdMS_TO_TICKS(10000)); 
            } else {
                Serial.println("📷 Scan terminé (0 frelon après filtrage)");
            }
        }
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}

// --- TACHE 2 : METEO (Toutes les 60 secondes) ---
void weather_task(void *pvParameters) {
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(60000)); 
        float t = dht.readTemperature();
        float h = dht.readHumidity();
        if (!isnan(t) && !isnan(h)) {
            Serial.printf("🌡️ Envoi météo: T:%.1f H:%.1f\n", t, h);
            LoraSerial.printf("AT+MSG=\"DATA T:%.1f H:%.1f\"\n", t, h);
        }
    }
}

void setup() {
    Serial.begin(115200);
    LoraSerial.begin(9600, SERIAL_8N1, 44, 43); 
    delay(2000);
    dht.begin();

    Serial.println("\n--- CONFIGURATION LORA ---");
    sendATCommand("AT+ID=DevEui, \"70B3D57ED0075559\"");
    sendATCommand("AT+ID=AppEui, \"0000000000000000\"");
    sendATCommand("AT+KEY=APPKEY, \"2A4038B69165EF3E53DA188E346A9A02\"");
    sendATCommand("AT+MODE=LWOTAA");
    sendATCommand("AT+DR=EU868");
    sendATCommand("AT+JOIN");
    
    // Petite pause pour laisser le temps au Join
    delay(5000);

    // Initialisation Caméra
    uint32_t buf_size = 240 * 240 * 2;
    snapshot_buf = (uint8_t*)heap_caps_malloc(buf_size, MALLOC_CAP_SPIRAM);
    if (!snapshot_buf || esp_camera_init(&camera_config) != ESP_OK) {
        Serial.println("❌ Erreur Caméra");
        while(1);
    }

    // Lancement des tâches
    xTaskCreatePinnedToCore(inference_task, "IA", 65536, NULL, 5, NULL, 1);
    xTaskCreatePinnedToCore(weather_task, "Meteo", 8192, NULL, 1, NULL, 0);
    
    Serial.println("✅ BeeGuardAI : Système actif (Filtre anti-doublon ON)");
}

void loop() {
    vTaskDelay(pdMS_TO_TICKS(1000));
}