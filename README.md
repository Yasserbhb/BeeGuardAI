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
│ - User settings     │         │ - Hornet detections         │
│ - Sessions          │         │                             │
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
| PDF Reports | ReportLab |
| Email | SMTP (Gmail compatible) |

## Quick Start

### Prerequisites
- Docker & Docker Compose installed
- Git

### Run locally

```bash
# Clone the repo
git clone https://github.com/your-username/BeeGuardAI.git
cd BeeGuardAI

# Copy environment file
cp .env.example .env

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
├── tests/
│   ├── simulate_device.py   # Device simulator
│   └── test_report.py       # Email test script
│
├── docker-compose.yml       # Docker services
├── .env.example             # Environment template
└── README.md
```

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

### Implemented
- [x] User authentication (register, login, logout)
- [x] Multi-organization support
- [x] Beehive management (CRUD)
- [x] Apiary management (CRUD)
- [x] Real-time dashboard with sensor data
- [x] Historical data charts with date filtering
- [x] Auto-generated device IDs
- [x] IoT data ingestion endpoint
- [x] Device simulator for testing
- [x] Dark/Light theme toggle
- [x] Email alerts for hornet detection
- [x] PDF reports (daily/weekly)
- [x] User settings page

### To Be Added
- [ ] AI hornet detection (image classification)
- [ ] Push notifications
- [ ] Mobile app
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

# SMTP Email (for alerts and reports)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=BeeGuardAI
```

## IoT Integration

Send sensor data to your beehives via HTTP POST:

```bash
curl -X POST http://your-server/api/iot/data \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "beehive-12345",
    "temperature": 35.2,
    "humidite": 65.0,
    "nombre_abeilles": 150,
    "nombre_frelons": 0,
    "luminosite": 1
  }'
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

### Production (VPS)

1. Get a VPS (Hetzner, OVH, DigitalOcean)
2. Install Docker & Docker Compose
3. Clone repo and configure `.env`
4. Run `docker-compose up -d`
5. Point your domain to the VPS IP

### With Coolify

1. Install Coolify on your VPS
2. Connect GitHub repo
3. Set environment variables
4. Deploy

## License

MIT
