"""
BeeGuardAI - Ruches Routes
"""

from fastapi import APIRouter, HTTPException, Request
from app.models import RucheCreate, RucheUpdate
from app.db.mysql import get_db
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/ruches", tags=["ruches"])


@router.post("")
async def create_ruche(ruche: RucheCreate, request: Request):
    user = get_current_user(request)

    if user["role"] not in ["admin", "gestionnaire"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO ruches (nom, rucher_id, organisation_id)
        VALUES (%s, %s, %s)
    ''', (ruche.nom, ruche.rucher_id, user["organisation_id"]))

    ruche_id = cursor.lastrowid
    conn.close()

    return {"id": ruche_id, "nom": ruche.nom, "rucher_id": ruche.rucher_id}


@router.get("")
async def list_ruches(request: Request):
    user = get_current_user(request)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.*, ru.nom as rucher_nom, ru.localisation as rucher_localisation
        FROM ruches r
        LEFT JOIN ruchers ru ON r.rucher_id = ru.id
        WHERE r.organisation_id = %s
        ORDER BY ru.nom, r.nom
    ''', (user["organisation_id"],))

    ruches = cursor.fetchall()
    conn.close()

    return ruches


@router.put("/{ruche_id}")
async def update_ruche(ruche_id: int, ruche_data: RucheUpdate, request: Request):
    """Update ruche details including TTN device ID"""
    user = get_current_user(request)

    if user["role"] not in ["admin", "gestionnaire"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    conn = get_db()
    cursor = conn.cursor()

    # Build update query dynamically
    updates = []
    values = []

    if ruche_data.nom is not None:
        updates.append("nom = %s")
        values.append(ruche_data.nom)
    if ruche_data.ttn_device_id is not None:
        updates.append("ttn_device_id = %s")
        values.append(ruche_data.ttn_device_id)
    if ruche_data.rucher_id is not None:
        updates.append("rucher_id = %s")
        values.append(ruche_data.rucher_id if ruche_data.rucher_id != 0 else None)

    if not updates:
        conn.close()
        raise HTTPException(status_code=400, detail="No fields to update")

    values.extend([ruche_id, user["organisation_id"]])

    cursor.execute(f'''
        UPDATE ruches SET {", ".join(updates)}
        WHERE id = %s AND organisation_id = %s
    ''', values)

    conn.close()

    return {"success": True, "ruche_id": ruche_id}


@router.delete("/{ruche_id}")
async def delete_ruche(ruche_id: int, request: Request):
    user = get_current_user(request)

    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ruches WHERE id = %s AND organisation_id = %s", (ruche_id, user["organisation_id"]))
    conn.close()

    return {"success": True}
