"""
BeeGuardAI - Device Simulator (ALERT TEST MODE)

Simulates beehives with realistic sensor data that evolves gradually.
Run: python simulate_device.py
"""

import requests
import random
import time
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000/api/iot/data"
INTERVAL = 20  # seconds between each data point
DURATION = 3900  # 5 minutes total

# Ruche to test
RUCHES = [
    {"device_id": "beehive-27789", "name": "Ruche Test 1P", "has_hornets": True},
    {"device_id": "beehive-7074", "name": "Ruche 333", "has_hornets": True},
    {"device_id": "beehive-001", "name": "Ruche Alpha", "has_hornets": False},
    {"device_id": "beehive-002", "name": "Ruche Beta", "has_hornets": True},
    {"device_id": "beehive-81146", "name": "Ruche Test 2P", "has_hornets": False},
]

# Persistent state per ruche so values drift gradually
_state = {}


def _init_state(device_id):
    """Initialize starting state for a ruche"""
    _state[device_id] = {
        "temperature": round(random.uniform(8.5, 9.5), 1),
        "humidity": round(random.uniform(75, 80), 1),
        "bees": random.randint(28, 35),
        "hornets": 0,  # current hornet count (drifts smoothly)
        "hornet_wave": 0,  # cycles remaining in a hornet attack wave
    }


def _drift(current, step, low, high):
    """Drift a value by a small random step, clamped to [low, high]"""
    new = current + random.uniform(-step, step)
    return round(max(low, min(high, new)), 1)


def generate_winter_data(ruche):
    """Generate winter sensor data with gradual, realistic changes"""
    device_id = ruche.get("device_id", str(ruche.get("id")))

    if device_id not in _state:
        _init_state(device_id)

    s = _state[device_id]

    # Temperature drifts slowly (±0.3 per cycle, range 7-11°C)
    s["temperature"] = _drift(s["temperature"], 0.3, 7, 11)

    # Humidity drifts slowly (±1 per cycle, range 65-90%)
    s["humidity"] = _drift(s["humidity"], 1.0, 65, 90)

    # Daytime for testing
    luminosite = 1

    # Bee count drifts (±3 per cycle, range 0-50)
    s["bees"] = int(_drift(s["bees"], 3, 0, 50))

    # Hornets: come in waves, count drifts smoothly
    if ruche["has_hornets"]:
        if s["hornet_wave"] > 0:
            # In a wave: drift hornets up slowly (±1, max 6)
            s["hornets"] = int(_drift(s["hornets"], 1, 1, 6))
            s["hornet_wave"] -= 1
        elif s["hornets"] > 0:
            # Wave ended: drift down toward 0
            s["hornets"] = max(0, s["hornets"] - random.randint(1, 2))
        elif random.random() < 0.15:
            # 15% chance to start a new wave (lasts 3-8 cycles)
            s["hornet_wave"] = random.randint(3, 8)
            s["hornets"] = random.randint(1, 2)  # start small
        hornets = s["hornets"]
    else:
        hornets = 0

    # Acoustic state correlates with situation
    if hornets > 0:
        # Hornets present: bees are agitated or silent (fled)
        acoustic = random.choices(["bees", "no_bees"], weights=[70, 30])[0]
    elif random.random() < 0.05:
        # Rare queen detection
        acoustic = "queen"
    elif random.random() < 0.1:
        # Occasional silence
        acoustic = "no_bees"
    else:
        acoustic = "bees"

    data = {
        "nombre_frelons": hornets,
        "nombre_abeilles": s["bees"],
        "temperature": s["temperature"],
        "humidite": s["humidity"],
        "luminosite": luminosite,
        "etat_acoustique": acoustic
    }

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
    print("  BeeGuardAI - Device Simulator")
    print("=" * 65)
    print(f"\nSimulating {len(RUCHES)} ruche(s):")
    for r in RUCHES:
        status = " [HORNET WAVES]" if r["has_hornets"] else " [NO HORNETS]"
        device = r.get("device_id", f"id:{r.get('id')}")
        print(f"  - {r['name']} ({device}){status}")
    print(f"\nData drifts gradually between readings")
    print(f"Hornets come in waves on marked ruches")
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
    print(f"Check the dashboard to see the data!")
    print("=" * 65)


if __name__ == "__main__":
    main()
