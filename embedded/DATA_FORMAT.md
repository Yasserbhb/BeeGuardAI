# Data Format Reference

Exact format the database expects from IoT devices.

---

## API Endpoint

```
POST http://YOUR_SERVER_IP:3000/api/iot/data
```

---

## Request Format

### Headers

```
Content-Type: application/json
```

### Body (JSON)

```json
{
  "api_key": "bga_your_api_key_here",
  "ruche_id": 1,
  "nombre_frelons": 3,
  "nombre_abeilles_entrees": 45,
  "nombre_abeilles_sorties": 38,
  "temperature": 24.5,
  "humidite": 65.0,
  "etat_abeilles": "normal",
  "etat_acoustique": "normal"
}
```

---

## Field Descriptions

| Field | Type | Required | Description | Valid Values |
|-------|------|----------|-------------|--------------|
| `api_key` | string | ✅ | API key from "Clés API" page | `bga_...` |
| `ruche_id` | integer | ❌ | Beehive ID (optional if using api_key) | 1, 2, 3... |
| `nombre_frelons` | integer | ✅ | Number of Asian hornets detected | 0-100 |
| `nombre_abeilles_entrees` | integer | ✅ | Number of bees entering | 0-1000 |
| `nombre_abeilles_sorties` | integer | ✅ | Number of bees exiting | 0-1000 |
| `temperature` | float | ✅ | Temperature in Celsius | -50 to 100 |
| `humidite` | float | ✅ | Humidity percentage | 0 to 100 |
| `etat_abeilles` | string | ✅ | Bee health status | `normal`, `affaiblies`, `mortes` |
| `etat_acoustique` | string | ✅ | Acoustic stress level | `normal`, `stress`, `alerte` |

---

## Valid Values for Status Fields

### `etat_abeilles` (Bee Health)

- `"normal"` - Bees are healthy and active
- `"affaiblies"` - Bees appear weakened (low activity, hornets present)
- `"mortes"` - Bees are dead or dying

### `etat_acoustique` (Acoustic State)

- `"normal"` - Normal buzzing sound
- `"stress"` - Stressed buzzing (irregular frequency)
- `"alerte"` - Alert state (very irregular, potential attack)

---

## Example Requests

### Normal Activity

```json
{
  "api_key": "bga_abc123xyz789",
  "nombre_frelons": 0,
  "nombre_abeilles_entrees": 42,
  "nombre_abeilles_sorties": 38,
  "temperature": 24.5,
  "humidite": 62.0,
  "etat_abeilles": "normal",
  "etat_acoustique": "normal"
}
```

### Hornet Attack

```json
{
  "api_key": "bga_abc123xyz789",
  "nombre_frelons": 8,
  "nombre_abeilles_entrees": 12,
  "nombre_abeilles_sorties": 45,
  "temperature": 26.3,
  "humidite": 58.0,
  "etat_abeilles": "affaiblies",
  "etat_acoustique": "alerte"
}
```

### Testing Data

```json
{
  "api_key": "bga_test_key_123",
  "nombre_frelons": 2,
  "nombre_abeilles_entrees": 50,
  "nombre_abeilles_sorties": 48,
  "temperature": 23.0,
  "humidite": 65.0,
  "etat_abeilles": "normal",
  "etat_acoustique": "stress"
}
```

---

## Success Response

```json
{
  "success": true,
  "data_id": 123,
  "ruche_id": 1,
  "message": "Data received successfully"
}
```

**HTTP Status:** `200 OK`

---

## Error Responses

### Missing API Key

```json
{
  "error": "API key required"
}
```

**HTTP Status:** `401 Unauthorized`

### Invalid API Key

```json
{
  "error": "Invalid or inactive API key"
}
```

**HTTP Status:** `401 Unauthorized`

### Invalid Data

```json
{
  "error": "Missing required field: nombre_frelons"
}
```

**HTTP Status:** `400 Bad Request`

---

## Arduino/C++ Code Example

```cpp
#include <ArduinoJson.h>
#include <WiFiNINA.h>
#include <ArduinoHttpClient.h>

void sendData() {
  // Create JSON document
  StaticJsonDocument<512> doc;

  doc["api_key"] = "bga_your_key";
  doc["nombre_frelons"] = 3;
  doc["nombre_abeilles_entrees"] = 45;
  doc["nombre_abeilles_sorties"] = 38;
  doc["temperature"] = 24.5;
  doc["humidite"] = 65.0;
  doc["etat_abeilles"] = "normal";
  doc["etat_acoustique"] = "normal";

  // Serialize to string
  String payload;
  serializeJson(doc, payload);

  // Send HTTP POST
  client.post("/api/iot/data");
  client.sendHeader("Content-Type", "application/json");
  client.beginBody();
  client.print(payload);
  client.endRequest();

  // Check response
  int status = client.responseStatusCode();
  if (status == 200) {
    Serial.println("✓ Success!");
  }
}
```

---

## Python Code Example

```python
import requests
import json

def send_data():
    url = "http://192.168.1.100:3000/api/iot/data"

    payload = {
        "api_key": "bga_your_key",
        "nombre_frelons": 3,
        "nombre_abeilles_entrees": 45,
        "nombre_abeilles_sorties": 38,
        "temperature": 24.5,
        "humidite": 65.0,
        "etat_abeilles": "normal",
        "etat_acoustique": "normal"
    }

    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        print("✓ Success!")
        print(response.json())
    else:
        print("✗ Error:", response.text)
```

---

## cURL Testing

Test the API from command line:

```bash
curl -X POST http://192.168.1.100:3000/api/iot/data \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "bga_your_key",
    "nombre_frelons": 3,
    "nombre_abeilles_entrees": 45,
    "nombre_abeilles_sorties": 38,
    "temperature": 24.5,
    "humidite": 65.0,
    "etat_abeilles": "normal",
    "etat_acoustique": "normal"
  }'
```

---

## Database Storage

Once received, the data is stored in the `donnees_capteurs` table:

```sql
INSERT INTO donnees_capteurs (
  ruche_id,
  nombre_frelons,
  nombre_abeilles_entrees,
  nombre_abeilles_sorties,
  temperature,
  humidite,
  etat_abeilles,
  etat_acoustique,
  timestamp
) VALUES (
  1,           -- from api_key or ruche_id
  3,           -- nombre_frelons
  45,          -- nombre_abeilles_entrees
  38,          -- nombre_abeilles_sorties
  24.5,        -- temperature
  65.0,        -- humidite
  'normal',    -- etat_abeilles
  'normal',    -- etat_acoustique
  CURRENT_TIMESTAMP
);
```

The `timestamp` is automatically set by the server when data is received.

---

## Tips

### Optimal Values

- **Send frequency:** Every 5-10 minutes
- **Temperature:** Should be realistic (15-35°C for beehives)
- **Humidity:** 40-80% is typical
- **Bee counts:** 20-200 per period is realistic
- **Hornets:** 0-10 per period (more indicates serious attack)

### Status Logic

```cpp
// Determine bee status based on hornets
if (hornets > 10) {
  status = "mortes";
} else if (hornets > 5) {
  status = "affaiblies";
} else {
  status = "normal";
}

// Determine acoustic status
if (hornets > 5) {
  acoustic = "alerte";
} else if (hornets > 0) {
  acoustic = "stress";
} else {
  acoustic = "normal";
}
```
