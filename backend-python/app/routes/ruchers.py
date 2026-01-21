"""
BeeGuardAI - Ruchers (Apiaries) Routes
"""

from fastapi import APIRouter, HTTPException, Request
from app.models import RucherCreate, RucherUpdate
from app.db.mysql import get_db
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/ruchers", tags=["ruchers"])


@router.post("")
async def create_rucher(rucher: RucherCreate, request: Request):
    user = get_current_user(request)

    if user["role"] not in ["admin", "gestionnaire"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO ruchers (nom, localisation, organisation_id)
        VALUES (%s, %s, %s)
    ''', (rucher.nom, rucher.localisation, user["organisation_id"]))

    rucher_id = cursor.lastrowid
    conn.close()

    return {"id": rucher_id, "nom": rucher.nom, "localisation": rucher.localisation}


@router.get("")
async def list_ruchers(request: Request):
    user = get_current_user(request)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ruchers WHERE organisation_id = %s ORDER BY nom", (user["organisation_id"],))

    ruchers = cursor.fetchall()
    conn.close()

    return ruchers


@router.put("/{rucher_id}")
async def update_rucher(rucher_id: int, rucher_data: RucherUpdate, request: Request):
    user = get_current_user(request)

    if user["role"] not in ["admin", "gestionnaire"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    conn = get_db()
    cursor = conn.cursor()

    updates = []
    values = []

    if rucher_data.nom is not None:
        updates.append("nom = %s")
        values.append(rucher_data.nom)
    if rucher_data.localisation is not None:
        updates.append("localisation = %s")
        values.append(rucher_data.localisation)

    if not updates:
        conn.close()
        raise HTTPException(status_code=400, detail="No fields to update")

    values.extend([rucher_id, user["organisation_id"]])

    cursor.execute(f'''
        UPDATE ruchers SET {", ".join(updates)}
        WHERE id = %s AND organisation_id = %s
    ''', values)

    conn.close()

    return {"success": True, "rucher_id": rucher_id}


@router.delete("/{rucher_id}")
async def delete_rucher(rucher_id: int, request: Request):
    user = get_current_user(request)

    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ruchers WHERE id = %s AND organisation_id = %s", (rucher_id, user["organisation_id"]))
    conn.close()

    return {"success": True}
