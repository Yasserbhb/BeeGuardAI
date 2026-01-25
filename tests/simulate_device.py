"""
BeeGuardAI - Device Simulator (ALERT TEST MODE)

Simulates beehives with HIGH HORNET counts to trigger alerts.
Run: python simulate_device.py
"""

import requests
import random
import time
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000/api/iot/data"
INTERVAL = 5  # seconds between each data point
DURATION = 180  # 3 minutes total

# Ruche to test
RUCHES = [
    {"device_id": "beehive-27789", "name": "Ruche Test 1P", "has_hornets": True},
    {"device_id": "beehive-7074", "name": "Ruche 333", "has_hornets": True},
]


def generate_winter_data(ruche):
    """Generate winter sensor data (8-10°C, reduced bee activity)"""

    # Winter temperature (8-10°C)
    temperature = round(random.uniform(8, 10), 1)

    # Higher humidity in winter
    humidity = round(random.uniform(70, 85), 1)

    # Daytime for testing
    luminosite = 1

    # Bees at entry
    total_bees = random.randint(20, 40)

    # HIGH HORNETS for alert testing
    if ruche["has_hornets"]:
        hornets = random.randint(5, 15)  # High numbers to trigger 1% threshold
        acoustic = "alert"
        bee_status = "stressed"
    else:
        hornets = 0
        acoustic = "normal"
        bee_status = "normal"

    data = {
        "nombre_frelons": hornets,
        "nombre_abeilles": total_bees,
        "temperature": temperature,
        "humidite": humidity,
        "luminosite": luminosite,
        "etat_abeilles": bee_status,
        "etat_acoustique": acoustic
    }

    # Use device_id if available, otherwise ruche_id
    if "device_id" in ruche:
        data["device_id"] = ruche["device_id"]
    else:
        data["ruche_id"] = ruche["id"]

    return data


def send_data(data):
    """Send data to API"""
    try:
        response = requests.post(API_URL, json=data, timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"  ERROR: {e}")
        return False


def main():
    print("=" * 65)
    print("  BeeGuardAI - ALERT TEST MODE (High Hornets)")
    print("=" * 65)
    print(f"\nSimulating {len(RUCHES)} ruche(s):")
    for r in RUCHES:
        status = " [HIGH HORNETS!]" if r["has_hornets"] else ""
        device = r.get("device_id", f"id:{r.get('id')}")
        print(f"  - {r['name']} ({device}){status}")
    print(f"\nSending 5-15 hornets per reading to trigger alerts")
    print(f"Sending data every {INTERVAL}s for {DURATION // 60} minutes")
    print(f"API: {API_URL}")
    print("\nPress Ctrl+C to stop\n")
    print("-" * 65)

    start_time = time.time()
    cycle = 0

    while (time.time() - start_time) < DURATION:
        cycle += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[Cycle {cycle}] {timestamp}")

        for ruche in RUCHES:
            data = generate_winter_data(ruche)

            if send_data(data):
                # Format output
                name = ruche["name"].ljust(12)
                temp = f"{data['temperature']}°C".ljust(7)
                hum = f"{data['humidite']}%".ljust(6)
                hornets = str(data['nombre_frelons']).ljust(2)
                bees = str(data['nombre_abeilles']).ljust(4)

                # Highlight hornets
                status = "OK"
                if data['nombre_frelons'] > 0:
                    status = f"⚠️  HORNETS ({data['nombre_frelons']})"

                print(f"  {name} | {temp} | {hum} | Hornets: {hornets} | Bees: {bees} | {status}")
            else:
                print(f"  {ruche['name'].ljust(12)} | FAILED")

        time.sleep(INTERVAL)

    elapsed = int(time.time() - start_time)
    total_points = cycle * len(RUCHES)
    print(f"\n" + "=" * 65)
    print(f"Done! Ran for {elapsed}s, sent {total_points} data points.")
    print(f"Check the dashboard to see winter data + hornet alerts!")
    print("=" * 65)


if __name__ == "__main__":
    main()
