#include <Wire.h>
#include <DHT.h>

#define SENSOR_ADDR 0x23
#define DHTPIN 4
#define DHTTYPE DHT22
#define SEUIL_NUIT 60  // Lux en dessous = nuit
#define TEMPS_VEILLE 300  // Temps de veille en secondes avant la prochaine mesure de luminosité
#define TEMPS_MESURE 2 // Delai entre chaque mesure quand actif

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(115200);
  delay(2000);
  
  Wire.begin(5, 6);
  dht.begin();
  
  // Power ON capteur lumière
  Wire.beginTransmission(SENSOR_ADDR);
  Wire.write(0x01);
  Wire.endTransmission();
  delay(200);
}

void loop() {
  float lux = lireLux();
  
  Serial.print("Luminosite: ");
  Serial.print(lux);
  Serial.println(" lux");
  
  if (lux < SEUIL_NUIT) {
    Serial.println("Nuit detectee -> Deep Sleep");
    delay(200);
    esp_sleep_enable_timer_wakeup(TEMPS_VEILLE * 1000000ULL);  
    esp_deep_sleep_start();
  } else {
    Serial.print("Il fait jour... \n");
    // // Jour -> faire les mesures
    float h = dht.readHumidity();
    float t = dht.readTemperature();
    
    Serial.print("Temp: ");
    Serial.print(t);
    Serial.print(" C | Humidite: ");
    Serial.print(h);
    Serial.println(" %");
    
    delay(TEMPS_MESURE*1000);  
  }
}

float lireLux() {
  Wire.beginTransmission(SENSOR_ADDR);
  Wire.write(0x10);
  Wire.endTransmission();
  delay(500);
  
  Wire.requestFrom(SENSOR_ADDR, 2);
  if (Wire.available() >= 2) {
    uint16_t raw = Wire.read() << 8 | Wire.read();
    return raw / 1.2;
  }
  return -1;
}
