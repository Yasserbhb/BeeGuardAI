# BeeGuardAI - Architecture Overview

System architecture for the BeeGuardAI beehive monitoring platform.

---

## System Overview

BeeGuardAI is a **full-stack IoT monitoring system** that combines:
- **Edge AI** on ESP32 microcontrollers for real-time hornet detection
- **LoRaWAN** for long-range wireless communication
- **Cloud backend** for data aggregation and visualization
- **Web dashboard** for monitoring and alerts

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    BEEHIVE (Physical)                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Camera     │  │ Microphone   │  │ DHT Sensor   │     │
│  │  (OV2640)    │  │   (I2S)      │  │(Temp/Humid)  │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │             │
│         └──────────────────┼──────────────────┘             │
│                            │                                │
│                    ┌───────▼────────┐                       │
│                    │   ESP32-CAM    │                       │
│                    │  + LoRa SX1276 │                       │
│                    └───────┬────────┘                       │
│                            │                                │
│         ┌──────────────────┴──────────────────┐            │
│         │                                      │            │
│    ┌────▼─────┐                         ┌─────▼────┐       │
│    │  Edge    │                         │  LoRa    │       │
│    │Impulse AI│                         │  Module  │       │
│    │(TinyML)  │                         │ (SX1276) │       │
│    └──────────┘                         └──────────┘       │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ LoRaWAN
                            │
                    ┌───────▼────────┐
                    │  LoRa Gateway  │
                    │  (Raspberry Pi)│
                    └───────┬────────┘
                            │
                            │ Internet
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                     CLOUD SERVER                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Node.js + Express.js                  │    │
│  │                 (Backend API)                      │    │
│  └────────────┬───────────────────────┬───────────────┘    │
│               │                       │                    │
│     ┌─────────▼─────────┐   ┌────────▼────────┐          │
│     │   SQLite DB       │   │  Authentication │          │
│     │  (ruches.db)      │   │   (JWT tokens)  │          │
│     └───────────────────┘   └─────────────────┘          │
│                                                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTP/REST API
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    WEB BROWSER                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Vanilla JavaScript Frontend                  │  │
│  │              + Chart.js                              │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Dashboard   │  │ Gérer Ruches │  │  Clés API    │    │
│  │ (Real-time)  │  │   (CRUD)     │  │ (IoT Keys)   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Frontend
- **Vanilla JavaScript** - No frameworks, lightweight
- **Chart.js** - Real-time data visualization
- **HTML5 + CSS3** - Modern responsive design
- **Fetch API** - REST API communication

### Backend
- **Node.js 18+** - JavaScript runtime
- **Express.js** - Web server framework
- **SQLite (sql.js)** - Embedded database
- **Cookie-based auth** - Session management
- **CORS** - Cross-origin resource sharing

### Embedded (ESP32)
- **Arduino Framework** - Microcontroller programming
- **Edge Impulse** - On-device AI inference (TinyML)
- **LoRaWAN** - Long-range wireless (SX1276 module)
- **OV2640** - Camera module
- **I2S Microphone** - Audio capture
- **DHT22** - Temperature/humidity sensor

### DevOps
- **nodemon** - Auto-restart during development
- **Git** - Version control

---

## Data Flow

### 1. Data Collection (Edge Device)

```
Sensors → ESP32 → Edge Impulse Model → Classification
                         ↓
                   LoRa Transmission
```

**Frequency:** Every 5 minutes
**Data Collected:**
- Hornet count (AI classification)
- Bee entry/exit count (AI classification)
- Temperature (°C)
- Humidity (%)
- Bee health status (audio analysis)
- Acoustic state (stress detection)

### 2. Data Transmission

```
ESP32 → LoRa SX1276 → Gateway → Internet → Server
```

**Protocol:** LoRaWAN
**Range:** Up to 10km (line of sight)
**Bandwidth:** ~50 kbps

### 3. Data Storage

```json
POST /api/donnees
{
  "ruche_id": 1,
  "nombre_frelons": 3,
  "nombre_abeilles_entrees": 45,
  "nombre_abeilles_sorties": 38,
  "temperature": 24.5,
  "humidite": 65.0,
  "etat_abeilles": "normal",
  "etat_acoustique": "normal",
  "timestamp": "2025-01-15T14:30:00Z"
}
```

**Storage:** SQLite database (`backend/ruches.db`)

### 4. Data Visualization

```
Browser → GET /api/donnees/latest → Server → Database
                                        ↓
                              JSON Response
                                        ↓
                            Chart.js Rendering
```

**Update Frequency:** Every 30 seconds (auto-refresh)

---

## Database Schema

### Tables

#### `utilisateurs` (Users)
```sql
CREATE TABLE utilisateurs (
  id INTEGER PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  mot_de_passe TEXT NOT NULL,
  nom TEXT,
  prenom TEXT,
  role TEXT CHECK(role IN ('admin', 'gestionnaire', 'lecteur')),
  organisation_id INTEGER,
  date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### `organisations` (Organizations)
```sql
CREATE TABLE organisations (
  id INTEGER PRIMARY KEY,
  nom TEXT UNIQUE NOT NULL,
  adresse TEXT,
  date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### `ruches` (Beehives)
```sql
CREATE TABLE ruches (
  id INTEGER PRIMARY KEY,
  nom TEXT NOT NULL,
  localisation TEXT,
  organisation_id INTEGER,
  date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### `donnees_capteurs` (Sensor Data)
```sql
CREATE TABLE donnees_capteurs (
  id INTEGER PRIMARY KEY,
  ruche_id INTEGER NOT NULL,
  nombre_frelons INTEGER DEFAULT 0,
  nombre_abeilles_entrees INTEGER DEFAULT 0,
  nombre_abeilles_sorties INTEGER DEFAULT 0,
  temperature REAL,
  humidite REAL,
  etat_abeilles TEXT,
  etat_acoustique TEXT,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### `cles_api` (API Keys)
```sql
CREATE TABLE cles_api (
  id INTEGER PRIMARY KEY,
  cle TEXT UNIQUE NOT NULL,
  ruche_id INTEGER,
  organisation_id INTEGER,
  actif BOOLEAN DEFAULT 1,
  date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login and get token |
| POST | `/api/auth/logout` | Logout and clear session |
| GET | `/api/auth/me` | Get current user info |

### Beehives (Ruches)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/ruches` | List all beehives | ✅ |
| POST | `/api/ruches` | Create new beehive | ✅ Admin/Gestionnaire |
| GET | `/api/ruches/:id` | Get beehive details | ✅ |
| PUT | `/api/ruches/:id` | Update beehive | ✅ Admin/Gestionnaire |
| DELETE | `/api/ruches/:id` | Delete beehive | ✅ Admin |

### Sensor Data (Données)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/donnees` | Submit sensor data | ❌ (uses API key) |
| GET | `/api/donnees/latest` | Get latest data for all beehives | ✅ |
| GET | `/api/ruches/:id/donnees` | Get historical data for one beehive | ❌ |
| GET | `/api/ruches/:id/donnees/latest` | Get latest data for one beehive | ❌ |

### IoT (API Keys)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/iot/data` | Submit data via API key | ❌ (API key in body) |
| GET | `/api/cles` | List API keys | ✅ |
| POST | `/api/cles` | Generate new API key | ✅ Admin/Gestionnaire |
| DELETE | `/api/cles/:id` | Delete API key | ✅ Admin/Gestionnaire |

---

## Authentication & Authorization

### Cookie-Based Sessions

1. User logs in with email/password
2. Server validates credentials and creates session
3. Server sends JWT token as HttpOnly cookie
4. Browser automatically includes cookie in subsequent requests
5. Server validates token on each protected endpoint

### Role-Based Access Control

- **Admin**: Full access (create/delete beehives, manage users, generate API keys)
- **Gestionnaire**: Manage beehives and view data (no user management)
- **Lecteur**: Read-only access to data

### Multi-Organization Support

- Each organization has isolated data
- Users only see beehives from their organization
- API keys are scoped to specific organizations

---

## Edge AI (TinyML)

### Model Training (Edge Impulse)

1. **Data Collection**: Record images/audio of hornets and bees
2. **Preprocessing**: Resize images (96x96), extract audio features (MFCC)
3. **Training**: Convolutional Neural Network (CNN)
4. **Optimization**: Quantization for ESP32 (INT8)
5. **Deployment**: Export as Arduino library

### Inference on ESP32

```cpp
// Capture image from camera
ei_impulse_result_t result;
signal_t signal;

// Run inference
EI_IMPULSE_ERROR res = run_classifier(&signal, &result);

// Get prediction
if (result.classification[0].value > 0.8) {
  // Hornet detected!
  hornetCount++;
}
```

**Inference Time:** ~200ms per image
**Accuracy:** ~92% (from Edge Impulse model)
**Power:** ~500mA @ 3.3V during inference

---

## LoRaWAN Communication

### Network Architecture

- **Device Class:** Class A (low power, uplink initiated)
- **Frequency:** 868 MHz (EU) or 915 MHz (US)
- **Spreading Factor:** SF7-SF12 (adaptive)
- **Payload Size:** Max 51 bytes per message

### Message Format

```
[Header(1)] [DeviceID(4)] [Hornet(1)] [BeesIn(1)] [BeesOut(1)] [Temp(2)] [Humid(1)] [Status(1)]
```

**Total:** 12 bytes

### Gateway

- **Hardware:** Raspberry Pi + LoRa HAT (RAK2245 or similar)
- **Software:** ChirpStack or TTN (The Things Network)
- **Function:** Bridge between LoRa and IP network

---

## Security Considerations

### Authentication
- Passwords hashed with SHA-256
- HttpOnly cookies prevent XSS attacks
- Session tokens expire after 24 hours

### API Keys
- 32-character random strings (crypto.randomBytes)
- Can be revoked at any time
- Scoped to specific beehives

### Database
- Prepared statements prevent SQL injection
- Organization-level data isolation
- No sensitive data in logs

### Network
- CORS enabled for trusted origins only
- HTTPS recommended for production
- LoRaWAN encryption (AES-128)

---

## Scalability

### Current Limits
- **Beehives:** ~1000 per server
- **Concurrent Users:** ~100
- **Data Points:** ~1M per year

### Scaling Strategies
- **Horizontal:** Multiple servers with load balancer
- **Database:** Migrate to PostgreSQL for larger datasets
- **Caching:** Redis for frequently accessed data
- **CDN:** Static assets served from CDN

---

## Monitoring & Logs

### Server Logs

Console output shows real-time activity:
- 🔐 Authentication events
- 🏠 Beehive CRUD operations
- 📊 Data ingestion
- 📈 Dashboard requests

### Error Handling

- All API errors return JSON with `{ error: "message" }`
- HTTP status codes: 200 (OK), 400 (Bad Request), 401 (Unauthorized), 500 (Server Error)
- Client-side errors logged to browser console

---

## Future Enhancements

### Planned Features
- Email/SMS alerts for hornet attacks
- Historical data export (CSV/Excel)
- Mobile app (React Native)
- Integration with weather APIs
- Predictive analytics (ML forecasting)

### Hardware Improvements
- Solar panel + battery for autonomous operation
- Multi-camera setup for better coverage
- Thermal imaging for hive health

### Software Improvements
- Real-time WebSocket updates
- User-configurable alert thresholds
- API rate limiting
- Automated backups

---

## References

- Edge Impulse: https://edgeimpulse.com
- LoRaWAN Specification: https://lora-alliance.org
- ESP32 Documentation: https://docs.espressif.com
- Chart.js: https://www.chartjs.org
