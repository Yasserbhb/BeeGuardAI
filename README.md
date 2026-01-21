# BeeGuardAI

Smart beehive monitoring system with AI-powered hornet detection.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│                    React + Vite + Nginx                      │
│                        (Port 80)                             │
└─────────────────────────┬───────────────────────────────────┘
                          │ /api/*
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                         Backend                              │
│                   FastAPI + Python                           │
│                       (Port 8000)                            │
└──────────┬─────────────────────────────────┬────────────────┘
           │                                 │
           ▼                                 ▼
┌─────────────────────┐         ┌─────────────────────────────┐
│       MySQL         │         │         InfluxDB            │
│   (Relational DB)   │         │     (Time-series DB)        │
│     Port 3306       │         │        Port 8086            │
│                     │         │                             │
│ - Users             │         │ - Sensor data               │
│ - Organizations     │         │ - Temperature               │
│ - Beehives (ruches) │         │ - Humidity                  │
│ - Apiaries (ruchers)│         │ - Bee counts                │
│ - Sessions          │         │ - Hornet detections         │
└─────────────────────┘         └─────────────────────────────┘
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

## Quick Start

### Prerequisites
- Docker & Docker Compose installed
- Git

### Run locally

```bash
# Clone the repo
git clone https://github.com/your-username/BeeGuardAI.git
cd BeeGuardAI

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
│   │   └── routes/
│   │       ├── auth.py      # Authentication
│   │       ├── ruchers.py   # Apiaries management
│   │       ├── ruches.py    # Beehives management
│   │       └── data.py      # Sensor data
│   ├── mqtt_listener.py     # TTN MQTT integration
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
├── tests/
│   └── simulate_device.py   # Device simulator
│
├── docker-compose.yml       # Local development
└── .env.example             # Environment template
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/auth/me` | Get current user |
| GET | `/api/ruchers` | List apiaries |
| POST | `/api/ruchers` | Create apiary |
| GET | `/api/ruches` | List beehives |
| POST | `/api/ruches` | Create beehive |
| PUT | `/api/ruches/{id}` | Update beehive |
| DELETE | `/api/ruches/{id}` | Delete beehive |
| GET | `/api/donnees/latest` | Get latest sensor data |
| GET | `/api/ruches/{id}/donnees` | Get beehive history |
| POST | `/api/iot/data` | Receive IoT sensor data |

## Features

### Implemented
- [x] User authentication (register, login, logout)
- [x] Multi-organization support
- [x] Beehive management (CRUD)
- [x] Apiary management (CRUD)
- [x] Real-time dashboard with sensor data
- [x] Historical data charts
- [x] Auto-generated device IDs
- [x] IoT data ingestion endpoint
- [x] Device simulator for testing

### To Be Added
- [ ] AI hornet detection (image classification)
- [ ] TTN (The Things Network) integration
- [ ] Push notifications / alerts
- [ ] Mobile app
- [ ] Data export (CSV, PDF)
- [ ] Grafana dashboards
- [ ] User roles (admin, manager, viewer)

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# MySQL
MYSQL_ROOT_PASSWORD=rootpassword
MYSQL_DATABASE=beeguardai
MYSQL_USER=beeguard
MYSQL_PASSWORD=secretpassword

# InfluxDB
INFLUX_TOKEN=beeguardai-super-secret-token
INFLUX_ORG=beeguardai
INFLUX_BUCKET=sensor_data

# TTN (optional)
TTN_APP_ID=your-ttn-app-id
TTN_API_KEY=your-ttn-api-key
```

## Testing

### Simulate sensor data

```bash
cd tests
python simulate_device.py
```

Sends fake sensor data to all beehives every 5 seconds.

## Deployment

### Using ngrok (quick demo)

```bash
# Start the app
docker-compose up -d

# Expose to internet
ngrok http 80
```

### Production (VPS)

1. Get a VPS (Hetzner, OVH, DigitalOcean)
2. Install Docker & Coolify
3. Connect GitHub repo
4. Deploy

## License

MIT
