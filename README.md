# BeeGuardAI

IoT beehive monitoring system with AI-powered Asian hornet detection.

**Sorbonne Université - PFE Project**

---

## Quick Start

```bash
cd backend
npm install
npm run dev
```

Open http://localhost:3000

**Login:** `admin@sorbonne.fr` / `admin123`

---

## Documentation

- **[SETUP.md](SETUP.md)** - Installation, running, and usage guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical architecture and system design

---

## Tech Stack

- **Backend:** Node.js + Express + SQLite
- **Frontend:** Vanilla JavaScript + Chart.js
- **Embedded:** ESP32 + Edge Impulse + LoRaWAN
- **Sensors:** Camera (OV2640), Microphone (I2S), DHT22

---

## Project Structure

```
PFE/
├── backend/          # Node.js server
├── frontend/         # Web dashboard
├── embedded/         # ESP32 code
└── docs/            # PDFs and documentation
```

---

## Features

- Real-time Asian hornet detection (AI)
- Bee traffic monitoring (entry/exit counting)
- Temperature & humidity tracking
- Historical data visualization
- Multi-organization support
- API keys for IoT devices
- LoRaWAN long-range communication

---

## License

Academic project - Sorbonne Université
