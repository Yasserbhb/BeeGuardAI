"""
BeeGuardAI - FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import INFLUX_URL, MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE
from app.db import init_database, init_influxdb
from app.routes import auth_router, ruchers_router, ruches_router, data_router

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

    print(f"\n🚀 Server running on http://localhost:8000")
    print(f"📊 InfluxDB: {INFLUX_URL}")
    print(f"🗄️  MySQL: {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")
    print("\n")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
