# BeeGuardAI - Setup & Run Guide

Quick guide to get the project running locally.

---

## Prerequisites

- **Node.js** 18+ ([Download](https://nodejs.org/))
- **Git** (optional, for cloning)

---

## Installation & Running

### 1. Install Backend Dependencies

```bash
cd backend
npm install
```

### 2. Start the Server

```bash
npm run dev
```

The server will start on **http://localhost:3000**

**Output you should see:**
```
Database initialized
Serveur BeeGuardAI démarré sur http://localhost:3000
```

### 3. Access the Application

Open your browser and go to:
- **http://localhost:3000** - Main dashboard
- **http://localhost:3000/login.html** - Login page

**Default credentials:**
- Email: `admin@sorbonne.fr`
- Password: `admin123`

---

## Project Structure

```
PFE/
├── backend/              # Node.js + Express backend
│   ├── server.js         # Main server file
│   ├── auth.js           # Authentication middleware
│   ├── database.js       # SQLite database setup
│   ├── ruches.db         # SQLite database file (auto-generated)
│   └── package.json      # Dependencies
│
├── frontend/             # Vanilla JavaScript frontend
│   └── public/
│       ├── index.html           # Dashboard page
│       ├── login.html           # Login page
│       ├── register.html        # Registration page
│       ├── manage-ruches.html   # Manage beehives
│       └── api-keys.html        # API keys for IoT devices
│
├── embedded/             # ESP32/Arduino code
│   └── bee_monitor/      # Edge Impulse + LoRaWAN code
│
└── docs/                 # Technical documentation (PDFs)
```

---

## Common Tasks

### Generate Test Data

1. Go to the dashboard (http://localhost:3000)
2. Click **"Générer Données Test"** button
3. Wait 5 seconds for data generation
4. Charts will populate with 1 week of historical data for 4 beehives

### View Logs

The terminal where you run `npm run dev` shows real-time logs:
- 🔐 Login events
- 🏠 Beehive creation
- 📊 Data ingestion
- 📈 API requests

### Stop the Server

Press `Ctrl+C` in the terminal

### Kill Stuck Server Processes

If port 3000 is already in use:

```bash
# Windows
powershell -Command "Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force"

# Linux/Mac
lsof -ti:3000 | xargs kill -9
```

---

## Adding IoT Devices

### 1. Create an API Key

1. Navigate to **Clés API** page
2. Click **"Générer une clé IoT"**
3. Copy the generated API key

### 2. Configure Your ESP32

Update your Arduino code with the API key:

```cpp
const char* apiKey = "YOUR_API_KEY_HERE";
const char* serverUrl = "http://YOUR_SERVER_IP:3000/api/iot/data";
```

### 3. Send Data

POST to `/api/iot/data` with your API key:

```json
{
  "api_key": "your-api-key",
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

## Troubleshooting

### Server won't start - "EADDRINUSE"

Port 3000 is already in use. Kill existing processes:

```bash
powershell -Command "Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force"
```

### Can't login

Make sure the database was initialized. Check for `backend/ruches.db` file. If missing, restart the server.

### Charts not showing data

1. Open browser console (F12)
2. Check for error messages
3. Click "Générer Données Test" to populate data
4. Refresh the page

### Database issues

Delete the database and restart:

```bash
cd backend
rm ruches.db
npm run dev
```

---

## Development

### File Locations

**To modify the frontend:**
- Dashboard: `frontend/public/index.html`
- Styles: Inline `<style>` tags in HTML files
- Charts: Chart.js configuration in `<script>` tags

**To modify the backend:**
- API endpoints: `backend/server.js`
- Authentication: `backend/auth.js`
- Database schema: `backend/database.js`

**To modify embedded code:**
- ESP32 code: `embedded/bee_monitor/`

### Adding New API Endpoints

Edit `backend/server.js`:

```javascript
app.get('/api/your-endpoint', requireAuth, (req, res) => {
  // Your code here
  res.json({ message: 'Hello' });
});
```

---

## Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) for system design details
- Check `docs/` folder for technical documentation (PDFs)
- Review embedded code in `embedded/` for hardware integration
