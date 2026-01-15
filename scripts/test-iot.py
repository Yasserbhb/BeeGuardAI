#!/usr/bin/env python3
"""
BeeGuardAI - IoT Testing Script
Simulates ESP32 device sending data
"""

import requests
import time
import random

# Configuration
SERVER_URL = "http://localhost:3000"
API_KEY = input("Enter your API key (bga_...): ").strip()

# Ruche information
RUCHE_NAME = "Ruche Python Test"
RUCHE_LOCATION = "Test Laboratory"

print("=" * 70)
print("BeeGuardAI - IoT Device Simulator")
print("=" * 70)
print()

# Step 1: Register ruche
print("[1/2] Registering ruche...")
response = requests.post(
    f"{SERVER_URL}/api/iot/register-ruche",
    headers={
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    },
    json={
        "nom": RUCHE_NAME,
        "localisation": RUCHE_LOCATION
    }
)

if response.status_code == 200:
    data = response.json()
    ruche_id = data['ruche_id']
    print(f"✓ Ruche registered: ID {ruche_id}")
    if data.get('existing'):
        print("  (Already existed, using existing ID)")
    print()
else:
    print(f"✗ Error: {response.text}")
    exit(1)

# Step 2: Send data in a loop
print("[2/2] Sending sensor data...")
print("Press Ctrl+C to stop")
print()

try:
    count = 0
    while True:
        count += 1

        # Simulate sensor readings
        nombre_frelons = random.randint(0, 10)
        abeilles_entrees = random.randint(40, 120)
        abeilles_sorties = random.randint(35, 115)
        temperature = round(random.uniform(20.0, 28.0), 1)
        humidite = round(random.uniform(55.0, 75.0), 1)

        # Determine states based on hornet count
        if nombre_frelons > 6:
            etat_abeilles = random.choice(['affaiblies', 'normal'])
            etat_acoustique = random.choice(['stress', 'normal'])
        else:
            etat_abeilles = 'normal'
            etat_acoustique = 'normal'

        # Send data
        response = requests.post(
            f"{SERVER_URL}/api/iot/data",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": API_KEY
            },
            json={
                "ruche_id": ruche_id,
                "nombre_frelons": nombre_frelons,
                "nombre_abeilles_entrees": abeilles_entrees,
                "nombre_abeilles_sorties": abeilles_sorties,
                "temperature": temperature,
                "humidite": humidite,
                "etat_abeilles": etat_abeilles,
                "etat_acoustique": etat_acoustique
            }
        )

        if response.status_code == 200:
            status = "🟢 NORMAL" if nombre_frelons < 3 else "🟡 WARNING" if nombre_frelons < 6 else "🔴 ALERT"
            print(f"[{count:3d}] {status} | Frelons: {nombre_frelons:2d} | Abeilles: {abeilles_entrees:3d}↓ {abeilles_sorties:3d}↑ | {temperature}°C {humidite}%")
        else:
            print(f"✗ Error sending data: {response.text}")

        # Wait 5 seconds (simulating 5 minute intervals, but faster for demo)
        time.sleep(5)

except KeyboardInterrupt:
    print()
    print()
    print("=" * 70)
    print(f"Stopped. Sent {count} data packets.")
    print()
    print("Check your dashboard at: http://localhost:3000")
    print("=" * 70)
