"""
BeeGuardAI - Device Simulator

Simulates multiple beehives sending sensor data.
Run: python simulate_device.py
"""

import requests
import random
import time
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000/api/iot/data"
INTERVAL = 10  # seconds between each data point
DURATION = 300  # 5 minutes total

# Ruches configuration with realistic scenarios
RUCHES = [
    {
        "id": 1,
        "name": "Ruche Alpha",
        "scenario": "healthy",  # Healthy hive, normal activity
        "temp_range": (32, 36),  # Ideal brood temperature
        "humidity_range": (55, 65),
        "hornets_chance": 0.1,  # 10% chance of hornets
    },
    {
        "id": 2,
        "name": "Ruche Beta",
        "scenario": "active",  # Very active hive, lots of bees
        "temp_range": (30, 35),
        "humidity_range": (50, 70),
        "hornets_chance": 0.2,  # 20% chance of hornets
    },
    {
        "id": 3,
        "name": "Ruche Gamma",
        "scenario": "stressed",  # Stressed hive, more hornets
        "temp_range": (28, 38),  # More variable temperature
        "humidity_range": (45, 75),
        "hornets_chance": 0.4,  # 40% chance of hornets
    },
]


def generate_sensor_data(ruche):
    """Generate realistic sensor data based on ruche scenario"""
    scenario = ruche["scenario"]

    # Temperature
    temp_min, temp_max = ruche["temp_range"]
    temperature = round(random.uniform(temp_min, temp_max), 1)

    # Humidity
    hum_min, hum_max = ruche["humidity_range"]
    humidity = round(random.uniform(hum_min, hum_max), 1)

    # Hornets based on scenario
    if random.random() < ruche["hornets_chance"]:
        hornets = random.randint(1, 5 if scenario == "stressed" else 3)
    else:
        hornets = 0

    # Bee activity based on scenario
    if scenario == "healthy":
        bees_in = random.randint(80, 150)
        bees_out = random.randint(70, 140)
        bee_status = "normal"
    elif scenario == "active":
        bees_in = random.randint(150, 250)
        bees_out = random.randint(140, 230)
        bee_status = random.choice(["normal", "active"])
    else:  # stressed
        bees_in = random.randint(40, 100)
        bees_out = random.randint(50, 120)
        bee_status = random.choice(["normal", "agitated", "stressed"])

    # Acoustic status
    if hornets > 2:
        acoustic = "alert"
    elif hornets > 0:
        acoustic = "loud"
    else:
        acoustic = "normal"

    return {
        "ruche_id": ruche["id"],
        "nombre_frelons": hornets,
        "nombre_abeilles_entrees": bees_in,
        "nombre_abeilles_sorties": bees_out,
        "temperature": temperature,
        "humidite": humidity,
        "etat_abeilles": bee_status,
        "etat_acoustique": acoustic
    }


def send_data(ruche):
    """Send data for a single ruche"""
    data = generate_sensor_data(ruche)

    try:
        response = requests.post(API_URL, json=data, timeout=5)

        if response.status_code == 200:
            status = "OK"
            if data["nombre_frelons"] > 0:
                status = f"ALERT ({data['nombre_frelons']} hornets!)"
        else:
            status = f"ERROR {response.status_code}"

        return data, status
    except requests.exceptions.RequestException as e:
        return data, f"FAILED: {e}"


def main():
    print("=" * 60)
    print("  BeeGuardAI - Multi-Ruche Simulator")
    print("=" * 60)
    print(f"\nSimulating {len(RUCHES)} ruches:")
    for r in RUCHES:
        print(f"  - {r['name']} ({r['scenario']})")
    print(f"\nSending data every {INTERVAL}s for {DURATION // 60} minutes")
    print(f"API: {API_URL}")
    print("\nPress Ctrl+C to stop\n")
    print("-" * 60)

    start_time = time.time()
    cycle = 0

    while (time.time() - start_time) < DURATION:
        cycle += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[Cycle {cycle}] {timestamp}")

        for ruche in RUCHES:
            data, status = send_data(ruche)

            # Color output based on status
            name = ruche["name"].ljust(12)
            temp = f"{data['temperature']}°C".ljust(7)
            hum = f"{data['humidite']}%".ljust(5)
            hornets = str(data['nombre_frelons']).ljust(2)
            bees = f"{data['nombre_abeilles_entrees']}/{data['nombre_abeilles_sorties']}"

            print(f"  {name} | Temp: {temp} | Hum: {hum} | Hornets: {hornets} | Bees: {bees.ljust(8)} | {status}")

        time.sleep(INTERVAL)

    elapsed = int(time.time() - start_time)
    print(f"\n" + "=" * 60)
    print(f"Done! Ran for {elapsed}s, sent {cycle * len(RUCHES)} data points.")
    print("=" * 60)


if __name__ == "__main__":
    main()
