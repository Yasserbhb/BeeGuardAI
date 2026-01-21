"""
BeeGuardAI - Sensor Data Routes
"""

from fastapi import APIRouter, HTTPException, Request
from app.models import SensorData
from app.db.mysql import get_db
from app.db.influxdb import write_sensor_data, get_latest_data, get_historical_data
from app.routes.auth import get_current_user

router = APIRouter(tags=["data"])


@router.post("/api/iot/data")
async def receive_iot_data(data: SensorData):
    """Receive data from IoT devices or simulator (test endpoint)"""

    # Lookup ruche to get organisation_id
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, organisation_id FROM ruches WHERE id = %s", (data.ruche_id,))
    ruche = cursor.fetchone()
    conn.close()

    if not ruche:
        raise HTTPException(status_code=404, detail=f"Ruche {data.ruche_id} not found")

    sensor_data = {
        "ruche_id": data.ruche_id,
        "organisation_id": ruche["organisation_id"],
        "nombre_frelons": data.nombre_frelons,
        "nombre_abeilles_entrees": data.nombre_abeilles_entrees,
        "nombre_abeilles_sorties": data.nombre_abeilles_sorties,
        "temperature": data.temperature,
        "humidite": data.humidite,
        "etat_abeilles": data.etat_abeilles,
        "etat_acoustique": data.etat_acoustique
    }

    write_sensor_data(sensor_data)

    return {"success": True, "ruche_id": data.ruche_id, "message": "Data received"}


@router.post("/api/donnees")
async def post_donnees(data: SensorData, request: Request):
    """Receive data from authenticated users"""
    user = get_current_user(request)

    sensor_data = {
        "ruche_id": data.ruche_id,
        "organisation_id": user["organisation_id"],
        "nombre_frelons": data.nombre_frelons,
        "nombre_abeilles_entrees": data.nombre_abeilles_entrees,
        "nombre_abeilles_sorties": data.nombre_abeilles_sorties,
        "temperature": data.temperature,
        "humidite": data.humidite,
        "etat_abeilles": data.etat_abeilles,
        "etat_acoustique": data.etat_acoustique
    }

    write_sensor_data(sensor_data)

    return {"success": True, "message": "Data recorded"}


@router.get("/api/donnees/latest")
async def get_latest(request: Request):
    """Get latest data for all beehives (dashboard)"""
    user = get_current_user(request)

    data = get_latest_data()

    filtered = [d for d in data if d.get("organisation_id") == user["organisation_id"]]

    return filtered


@router.get("/api/ruches/{ruche_id}/donnees")
async def get_ruche_history(ruche_id: int, hours: int = 168):
    """Get historical data for a beehive"""
    return get_historical_data(ruche_id, hours)
