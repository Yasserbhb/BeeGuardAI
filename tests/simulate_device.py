"""
BeeGuardAI - Device Simulator

Simulates beehives sending sensor data with day/night cycle.
Run: python simulate_device.py
"""

import requests
import random
import time
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000/api/iot/data"
INTERVAL = 5  # seconds between each data point

# Test ruche (change to your ruche id)
TEST_RUCHE = {"id": 1, "name": "Ruche Alpha"}

# Day/Night cycle config
DAY_READINGS = 6      # Send 6 readings during "day" (luminosite=1)
NIGHT_SLEEP = 30      # Sleep 30 seconds during "night"
CYCLES = 3            # Number of day/night cycles to simulate


def generate_day_data(ruche_id):
    """Generate daytime sensor data (luminosite=1)"""
    return {
        "ruche_id": ruche_id,
        "nombre_frelons": random.randint(0, 2),
        "nombre_abeilles_entrees": random.randint(80, 150),
        "nombre_abeilles_sorties": random.randint(70, 140),
        "temperature": round(random.uniform(32, 36), 1),
        "humidite": round(random.uniform(55, 65), 1),
        "luminosite": 1,
        "etat_abeilles": "normal",
        "etat_acoustique": "normal"
    }


def generate_night_data(ruche_id):
    """Generate night indicator data (luminosite=0) - sent once before sleep"""
    return {
        "ruche_id": ruche_id,
        "nombre_frelons": 0,
        "nombre_abeilles_entrees": 0,
        "nombre_abeilles_sorties": 0,
        "temperature": round(random.uniform(28, 32), 1),
        "humidite": round(random.uniform(60, 70), 1),
        "luminosite": 0,
        "etat_abeilles": "normal",
        "etat_acoustique": "normal"
    }


def send_data(data):
    """Send data to API"""
    try:
        response = requests.post(API_URL, json=data, timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"  ERROR: {e}")
        return False


def main():
    print("=" * 60)
    print("  BeeGuardAI - Day/Night Cycle Simulator")
    print("=" * 60)
    print(f"\nRuche: {TEST_RUCHE['name']} (ID: {TEST_RUCHE['id']})")
    print(f"Pattern: {DAY_READINGS} day readings -> 1 night indicator -> {NIGHT_SLEEP}s sleep")
    print(f"Cycles: {CYCLES}")
    print(f"API: {API_URL}")
    print("\nPress Ctrl+C to stop\n")
    print("-" * 60)

    for cycle in range(1, CYCLES + 1):
        print(f"\n{'='*20} CYCLE {cycle}/{CYCLES} {'='*20}")

        # DAY PHASE: Send readings with luminosite=1
        print(f"\n[DAY] Sending {DAY_READINGS} readings (luminosite=1)...")
        for i in range(DAY_READINGS):
            timestamp = datetime.now().strftime("%H:%M:%S")
            data = generate_day_data(TEST_RUCHE["id"])

            if send_data(data):
                print(f"  {timestamp} | Temp: {data['temperature']}°C | Hum: {data['humidite']}% | "
                      f"Bees: {data['nombre_abeilles_entrees']}/{data['nombre_abeilles_sorties']} | "
                      f"Lum: {data['luminosite']} | OK")
            else:
                print(f"  {timestamp} | FAILED")

            time.sleep(INTERVAL)

        # NIGHT INDICATOR: Send one reading with luminosite=0
        print(f"\n[NIGHT] Sending night indicator (luminosite=0)...")
        timestamp = datetime.now().strftime("%H:%M:%S")
        data = generate_night_data(TEST_RUCHE["id"])

        if send_data(data):
            print(f"  {timestamp} | Temp: {data['temperature']}°C | Hum: {data['humidite']}% | "
                  f"Bees: 0/0 | Lum: {data['luminosite']} | OK")
        else:
            print(f"  {timestamp} | FAILED")

        # SLEEP: Device sleeps, no data sent
        print(f"\n[SLEEP] Device sleeping for {NIGHT_SLEEP}s (no data)...")
        for remaining in range(NIGHT_SLEEP, 0, -5):
            print(f"  ... {remaining}s remaining")
            time.sleep(5)

        print(f"\n[WAKE] Device waking up!")

    print(f"\n" + "=" * 60)
    print(f"Done! Completed {CYCLES} day/night cycles.")
    print("Check the dashboard charts to see the night shading!")
    print("=" * 60)


if __name__ == "__main__":
    main()
