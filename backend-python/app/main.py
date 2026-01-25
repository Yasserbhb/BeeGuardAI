"""
BeeGuardAI - FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import INFLUX_URL, MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, SMTP_USER
from app.db import init_database, init_influxdb
from app.routes import auth_router, ruchers_router, ruches_router, data_router, settings_router
from app.services.alert_service import start_alert_scheduler
from app.services.report_service import start_report_scheduler

# ============================================
# APP SETUP
# ============================================

app = FastAPI(
    title="BeeGuardAI API",
    description="Backend pour surveillance des ruches",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# REGISTER ROUTES
# ============================================

app.include_router(auth_router)
app.include_router(ruchers_router)
app.include_router(ruches_router)
app.include_router(data_router)
app.include_router(settings_router)


# ============================================
# HEALTH CHECK
# ============================================

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "beeguardai-backend"}


# ============================================
# STARTUP
# ============================================

@app.on_event("startup")
async def startup():
    print("\n" + "=" * 50)
    print("   BeeGuardAI Backend")
    print("=" * 50)

    init_influxdb()
    init_database()

    # Start background services
    start_alert_scheduler()
    start_report_scheduler()

    print(f"\n🚀 Server running on http://localhost:8000")
    print(f"📊 InfluxDB: {INFLUX_URL}")
    print(f"🗄️  MySQL: {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")
    if SMTP_USER:
        print(f"📧 SMTP configured: {SMTP_USER}")
    else:
        print(f"⚠️  SMTP not configured - emails will be logged only")
    print("\n")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
