"""
BeeGuardAI - Sensor Data Routes
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from app.models import SensorData
from app.db.mysql import get_db
from app.db.influxdb import write_sensor_data, get_latest_data, get_historical_data
from app.routes.auth import get_current_user

router = APIRouter(tags=["data"])


@router.post("/api/iot/data")
async def receive_iot_data(request: Request):
    """Receive data from IoT devices - accepts our format OR TTN webhook format"""

    raw_data = await request.json()
    print(f"🔍 RAW DATA RECEIVED: {raw_data}")

    # Check if it's TTN webhook format (has end_device_ids)
    if "end_device_ids" in raw_data:
        payload = raw_data.get("uplink_message", {}).get("decoded_payload", {})
        # Use device_id from payload, not TTN metadata
        device_id = payload.get("device_id")  
        print(f"🔍 TTN FORMAT - payload device_id: {device_id}, payload: {payload}")

        data = SensorData(
            device_id=device_id,
            nombre_frelons=payload.get("nombre_frelons", 0),
            nombre_abeilles=payload.get("nombre_abeilles", 0),
            temperature=payload.get("temperature", 0.0),
            humidite=payload.get("humidite", 0.0),
            luminosite=payload.get("luminosite", 1),
            etat_abeilles=payload.get("etat_abeilles", "normal"),
            etat_acoustique=payload.get("etat_acoustique", "normal")
        )
    else:
        # Our direct format
        data = SensorData(**raw_data)

    conn = get_db()
    cursor = conn.cursor()

    # Lookup by device_id (TTN) or ruche_id
    if data.device_id:
        cursor.execute("SELECT id, organisation_id FROM ruches WHERE ttn_device_id = %s", (data.device_id,))
        ruche = cursor.fetchone()
        if not ruche:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Device {data.device_id} not found")
        ruche_id = ruche["id"]
    elif data.ruche_id:
        cursor.execute("SELECT id, organisation_id FROM ruches WHERE id = %s", (data.ruche_id,))
        ruche = cursor.fetchone()
        if not ruche:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Ruche {data.ruche_id} not found")
        ruche_id = data.ruche_id
    else:
        conn.close()
        raise HTTPException(status_code=400, detail="Either ruche_id or device_id required")

    conn.close()

    sensor_data = {
        "ruche_id": ruche_id,
        "organisation_id": ruche["organisation_id"],
        "nombre_frelons": data.nombre_frelons,
        "nombre_abeilles": data.nombre_abeilles,
        "temperature": data.temperature,
        "humidite": data.humidite,
        "luminosite": data.luminosite,
        "etat_abeilles": data.etat_abeilles,
        "etat_acoustique": data.etat_acoustique
    }

    write_sensor_data(sensor_data)

    return {"success": True, "ruche_id": ruche_id, "message": "Data received"}


@router.post("/api/donnees")
async def post_donnees(data: SensorData, request: Request):
    """Receive data from authenticated users"""
    user = get_current_user(request)

    sensor_data = {
        "ruche_id": data.ruche_id,
        "organisation_id": user["organisation_id"],
        "nombre_frelons": data.nombre_frelons,
        "nombre_abeilles": data.nombre_abeilles,
        "temperature": data.temperature,
        "humidite": data.humidite,
        "luminosite": data.luminosite,
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
async def get_ruche_history(ruche_id: int, hours: int = 168, start: Optional[str] = None, end: Optional[str] = None):
    """Get historical data for a beehive. Use hours OR start/end ISO timestamps."""
    return get_historical_data(ruche_id, hours, start, end)
