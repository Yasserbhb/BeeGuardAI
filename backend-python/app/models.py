"""
BeeGuardAI - Pydantic Models
"""

from pydantic import BaseModel
from typing import Optional


class UserRegister(BaseModel):
    email: str
    mot_de_passe: str
    nom: str
    prenom: str
    organisation_nom: str


class UserLogin(BaseModel):
    email: str
    mot_de_passe: str


class RucherCreate(BaseModel):
    nom: str
    localisation: Optional[str] = None


class RucherUpdate(BaseModel):
    nom: Optional[str] = None
    localisation: Optional[str] = None


class RucheCreate(BaseModel):
    nom: str
    rucher_id: Optional[int] = None


class RucheUpdate(BaseModel):
    nom: Optional[str] = None
    ttn_device_id: Optional[str] = None
    rucher_id: Optional[int] = None


class SensorData(BaseModel):
    ruche_id: Optional[int] = None
    device_id: Optional[str] = None  # TTN device ID (e.g., "beehive-7074")
    nombre_frelons: int = 0
    nombre_abeilles_entrees: int = 0
    nombre_abeilles_sorties: int = 0
    temperature: float = 0.0
    humidite: float = 0.0
    luminosite: int = 1  # 0=night, 1=day
    etat_abeilles: str = "normal"
    etat_acoustique: str = "normal"
