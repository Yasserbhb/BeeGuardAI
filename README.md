<p align="center">
  <img src="frontend-react/public/favicon.svg" alt="BeeGuardAI Logo" width="120" />
</p>

<h1 align="center">BeeGuardAI</h1>

<p align="center">
  <strong>Smart beehive monitoring system with AI-powered Asian hornet detection</strong>
</p>

<p align="center">
  Real-time monitoring of beehives wellbeing, temperature, humidity, and automatic detection of Asian hornets  to protect bee colonies.
</p>

---

## Team

| Name | Role |
|------|------|
| Yasser BOUHAI | Project Lead |
| Ghozlene HANAFI | Developer |
| Yanelle BEKKAR | Developer |
| Hadriel RATIARISON | Developer |
| Amine NAIT SI-AHMED | Developer |

*Sorbonne Université - 2025/2026*

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       ESP32 Device                          │
│              Edge Impulse AI Model (on-device)              │
│         Temperature, Humidity, Camera, Microphone           │
└─────────────────────────┬───────────────────────────────────┘
                          │ LoRaWAN
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  The Things Network (TTN)                   │
│                    Payload Formatter                        │
└─────────────────────────┬───────────────────────────────────┘
                          │ Webhook (POST /api/iot/data)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                         Backend                             │
│                   FastAPI + Python                          │
│                       (Port 8000)                           │
└──────────┬──────────────┼──────────────────┬────────────────┘
           │              │                  │
           ▼              ▼                  ▼
┌──────────────────┐ ┌──────────────┐ ┌─────────────────────┐
│      MySQL       │ │   InfluxDB   │ │      Frontend       │
│  (Relational DB) │ │ (Time-series)│ │  React + Nginx      │
│    Port 3306     │ │  Port 8086   │ │     Port 80         │
│                  │ │              │ │                     │
│ - Users          │ │ - Sensor data│ │ - Dashboard         │
│ - Organizations  │ │ - Temperature│ │ - Charts            │
│ - Beehives       │ │ - Humidity   │ │ - Settings          │
│ - Apiaries       │ │ - Bee counts │ │ - Alerts history    │
│ - Settings       │ │ - Hornets    │ │                     │
└──────────────────┘ └──────────────┘ └─────────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | React 18, Vite, CSS Modules |
| Backend | FastAPI, Python 3.11 |
| Database | MySQL 8.0 |
| Time-series DB | InfluxDB 2.7 |
| Containerization | Docker, Docker Compose |
| Reverse Proxy | Nginx |
| Hardware | ESP32 (Seeed XIAO) |
| AI Inference | Edge Impulse |
| Communication | LoRaWAN via TTN |
| Email | SMTP (Gmail compatible) |

## Quick Start

### Prerequisites
- **Docker Desktop** installed and running
- Git

### Run locally

```bash
# Clone the repo
git clone https://github.com/your-username/BeeGuardAI.git
cd BeeGuardAI

# Create environment file from template
cp .env.example .env

# Edit .env with your own credentials (SMTP, database passwords, etc.)

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f
```

Access the app at: **http://localhost**

### Default credentials
- Email: `admin@sorbonne.fr`
- Password: `admin123`

## Project Structure

```
BeeGuardAI/
├── backend-python/          # FastAPI backend
│   ├── app/
│   │   ├── main.py          # App entry point
│   │   ├── config.py        # Environment config
│   │   ├── models.py        # Pydantic models
│   │   ├── db/
│   │   │   ├── mysql.py     # MySQL operations
│   │   │   └── influxdb.py  # InfluxDB operations
│   │   ├── routes/
│   │   │   ├── auth.py      # Authentication
│   │   │   ├── ruchers.py   # Apiaries management
│   │   │   ├── ruches.py    # Beehives management
│   │   │   ├── data.py      # Sensor data & IoT
│   │   │   └── settings.py  # User settings
│   │   └── services/
│   │       ├── email_service.py   # SMTP emails
│   │       ├── alert_service.py   # Hornet alerts
│   │       └── report_service.py  # PDF reports
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend-react/          # React frontend
│   ├── src/
│   │   ├── pages/           # Page components
│   │   ├── components/      # Reusable components
│   │   ├── services/        # API client
│   │   └── context/         # Auth context
│   ├── nginx.conf           # Nginx config
│   ├── Dockerfile
│   └── package.json
│
├── esp32/                   # ESP32 firmware
│   ├── arduino.ino          # Main Arduino code
│   └── beeguardai_inferencing/  # Edge Impulse model library
│
├── tests/
│   ├── simulate_device.py   # Device simulator
│   └── test_report.py       # Email test script
│
├── docker-compose.yml       # Docker services
├── .env.example             # Environment template
└── README.md
```

## ESP32 Hardware

The ESP32 device runs on-device AI inference using Edge Impulse.

### Components
- **Microcontroller**: Seeed XIAO ESP32S3 
- **Sensors**: Temperature, humidity,Luminosity, camera, microphone
- **Communication**: LoRaWAN module

### Firmware Structure
- `arduino.ino` - Main code that reads sensors, runs inference, and sends data via LoRaWAN
- `beeguardai_inferencing/` - Edge Impulse exported library containing the trained AI model

### Data Flow
1. ESP32 reads sensors and runs AI inference locally
2. Results sent via LoRaWAN to The Things Network (TTN)
3. TTN payload formatter decodes the raw bytes to JSON
4. TTN webhook sends POST request directly to backend `/api/iot/data`
5. Backend stores in InfluxDB and triggers email alerts if hornets detected

### TTN Payload Format
```javascript
// Device sends: "DATA T:25.4 H:40.2"
// Formatter outputs:
{
  "device_id": "xiao-beeguard",
  "temperature": 25.4,
  "humidite": 40.2,
  "nombre_frelons": 0,
  "nombre_abeilles": 0,
  "luminosite": 1,
  "etat_acoustique": "bees"
}
```

## Edge Impulse - Model Training & Optimization

### Dataset

We manually labeled over **1,000 images** to train our object detection model with three classes:

| Class | Description |
|-------|-------------|
| `bees` | Group of bees gathered in front of the hive |
| `bee` | Single bee |
| `hornet` | Asian hornet roaming around the hive |

### Training Process

We used an iterative training approach on Edge Impulse:

1. **Initial labeling** - Manual bounding box annotation of images
2. **Incremental training** - After each batch of labeled images, we retrained the model to monitor accuracy evolution
3. **Final model** - Achieved **85% accuracy** using **YOLO Pro** architecture

```
Training Evolution:
┌────────────────┬──────────────┐
│ Training Round │   Accuracy   │
├────────────────┼──────────────┤
│ Round 1        │    ~45%      │
│ Round 2        │    ~60%      │
│ Round 3        │    ~72%      │
│ Final (YOLO)   │    ~85%      │
└────────────────┴──────────────┘
```

### Model Optimization for ESP32

The YOLO Pro model could not run on the ESP32 due to severe **RAM limitations**. Even the **YOLO Nano** variant (the smallest YOLO format available) exceeded the memory capacity of the Seeed XIAO ESP32S3. We therefore switched to the **FOMO** architecture and applied several optimization techniques to achieve a good compromise between memory usage and accuracy:

| Optimization Technique | Description |
|------------------------|-------------|
| **Image size reduction** | Reduced input resolution to fit memory constraints |
| **Quantization** | Converted model weights from float32 to int8 |
| **Grayscale conversion** | Changed from RGB to grayscale images (3x less memory) |
| **Architecture tuning** | Modified convolution layers and classifier parameters |

### Final Deployed Model

| Parameter | Value |
|-----------|-------|
| Architecture | **FOMO** (Faster Objects, More Objects) |
| Accuracy | **70-75%** |
| Target device | Seeed XIAO ESP32S3 |
| Input format | RGB (camera native) |

### Performance Notes

- The optimized FOMO model has some false positives and false negatives
- Overall detection is reliable enough to **trigger hornet alerts** effectively
- The trade-off between accuracy and memory footprint was necessary for embedded deployment
- Real-world testing shows satisfactory hornet detection for alerting purposes

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/auth/me` | Get current user |

### Beehives & Apiaries
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/ruchers` | List apiaries |
| POST | `/api/ruchers` | Create apiary |
| GET | `/api/ruches` | List beehives |
| POST | `/api/ruches` | Create beehive |
| PUT | `/api/ruches/{id}` | Update beehive |
| DELETE | `/api/ruches/{id}` | Delete beehive |

### Sensor Data
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/donnees/latest` | Get latest sensor data |
| GET | `/api/ruches/{id}/donnees` | Get beehive history |
| POST | `/api/iot/data` | Receive IoT sensor data |

### Settings
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/settings` | Get user settings |
| PUT | `/api/settings` | Update settings |

## Features

- User authentication (register, login, logout)
- Multi-organization support
- Beehive management (CRUD)
- Apiary management (CRUD)
- Real-time dashboard with sensor data
- Historical data charts with time range filtering
- Acoustic state monitoring (bees, no_bees, queen)
- Auto-generated device IDs
- IoT data ingestion (direct HTTP + TTN webhook)
- Device simulator for testing
- Dark/Light theme toggle
- Email alerts for hornet detection
- PDF reports (daily/weekly)
- User settings page

## Environment Variables

Create `.env` from `.env.example` and configure with your credentials:

```bash
# MySQL
MYSQL_ROOT_PASSWORD=your-root-password
MYSQL_DATABASE=beeguardai
MYSQL_USER=beeguard
MYSQL_PASSWORD=your-password

# InfluxDB
INFLUX_TOKEN=your-influx-token
INFLUX_ORG=beeguardai
INFLUX_BUCKET=sensor_data

# SMTP Email (for alerts and reports)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=BeeGuardAI
```

## IoT Integration

### Direct HTTP POST
```bash
curl -X POST http://your-server/api/iot/data \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "beehive-12345",
    "temperature": 35.2,
    "humidite": 65.0,
    "nombre_abeilles": 150,
    "nombre_frelons": 0,
    "luminosite": 1,
    "etat_acoustique": "bees"
  }'
```

### Via TTN Webhook
Configure a webhook in TTN console pointing to:
```
https://your-server/api/iot/data
```

## Testing

### Simulate sensor data
```bash
cd tests
python simulate_device.py
```

### Test email services
```bash
cd tests
python test_report.py report  # Test PDF report
python test_report.py alert   # Test alert check
```

## Deployment

### Local Development
1. Install **Docker Desktop**
2. Clone repo and create `.env` with your credentials
3. Run `docker-compose up -d`
4. Access at http://localhost

### Production (VPS)
1. Get a VPS (OVH, Hetzner, DigitalOcean, etc.)
2. Install Docker & Docker Compose
3. Clone repo and configure `.env`
4. Run `docker-compose up -d`
5. Point your domain to the VPS IP
6. (Optional) Set up SSL with Let's Encrypt

## License

MIT
