"""
BeeGuardAI - MQTT Listener for TTN

Receives data from ESP32 devices via TTN and writes to InfluxDB.
Looks up ruche by ttn_device_id in MySQL.
"""

import json
import os
import paho.mqtt.client as mqtt
import pymysql
from pymysql.cursors import DictCursor
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# ============================================
# CONFIGURATION
# ============================================

# TTN Configuration
TTN_HOST = os.getenv("TTN_HOST", "eu1.cloud.thethings.network")
TTN_PORT = int(os.getenv("TTN_PORT", "1883"))
TTN_APP_ID = os.getenv("TTN_APP_ID", "your-ttn-app-id")
TTN_API_KEY = os.getenv("TTN_API_KEY", "your-ttn-api-key")

# InfluxDB Configuration
INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "beeguardai-super-secret-token")
INFLUX_ORG = os.getenv("INFLUX_ORG", "beeguardai")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "sensor_data")

# MySQL Configuration
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "beeguard")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "secretpassword")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "beeguardai")

# ============================================
# DATABASE CLIENTS
# ============================================

influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)

def get_mysql_connection():
    """Get MySQL connection"""
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        cursorclass=DictCursor,
        autocommit=True
    )

def get_ruche_by_device_id(device_id: str) -> dict:
    """Lookup ruche by TTN device ID"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nom, organisation_id
            FROM ruches
            WHERE ttn_device_id = %s
        """, (device_id,))
        ruche = cursor.fetchone()
        conn.close()
        return ruche
    except Exception as e:
        print(f"MySQL error: {e}")
        return None

def write_sensor_data(data: dict):
    """Write sensor data to InfluxDB"""
    point = Point("sensor_data") \
        .tag("ruche_id", str(data.get("ruche_id", 1))) \
        .tag("ruche_name", data.get("ruche_name", f"Ruche {data.get('ruche_id', 1)}")) \
        .tag("organisation_id", str(data.get("organisation_id", 1))) \
        .field("nombre_frelons", int(data.get("nombre_frelons", 0))) \
        .field("nombre_abeilles_entrees", int(data.get("nombre_abeilles_entrees", 0))) \
        .field("nombre_abeilles_sorties", int(data.get("nombre_abeilles_sorties", 0))) \
        .field("temperature", float(data.get("temperature", 0))) \
        .field("humidite", float(data.get("humidite", 0))) \
        .field("etat_abeilles", str(data.get("etat_abeilles", "normal"))) \
        .field("etat_acoustique", str(data.get("etat_acoustique", "normal")))

    write_api.write(bucket=INFLUX_BUCKET, record=point)
    print(f"Data written for Ruche {data.get('ruche_id')} ({data.get('ruche_name')})")

# ============================================
# MQTT CALLBACKS
# ============================================

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("Connected to TTN")
        topic = f"v3/{TTN_APP_ID}@ttn/devices/+/up"
        client.subscribe(topic)
        print(f"Subscribed to: {topic}")
    else:
        print(f"Connection failed: {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())

        # Extract device_id from TTN message
        device_id = payload.get("end_device_ids", {}).get("device_id", "unknown")
        decoded = payload.get("uplink_message", {}).get("decoded_payload", {})

        if not decoded:
            print(f"No decoded payload for device {device_id}")
            return

        # Lookup ruche in MySQL by ttn_device_id
        ruche = get_ruche_by_device_id(device_id)

        if not ruche:
            print(f"Unknown device: {device_id} - not registered in database")
            return

        sensor_data = {
            "ruche_id": ruche["id"],
            "ruche_name": ruche["nom"],
            "organisation_id": ruche["organisation_id"],
            "nombre_frelons": decoded.get("nombre_frelons", decoded.get("hornets", 0)),
            "nombre_abeilles_entrees": decoded.get("nombre_abeilles_entrees", decoded.get("bees_in", 0)),
            "nombre_abeilles_sorties": decoded.get("nombre_abeilles_sorties", decoded.get("bees_out", 0)),
            "temperature": decoded.get("temperature", decoded.get("temp", 0)),
            "humidite": decoded.get("humidite", decoded.get("humidity", 0)),
            "etat_abeilles": decoded.get("etat_abeilles", decoded.get("bee_status", "normal")),
            "etat_acoustique": decoded.get("etat_acoustique", decoded.get("acoustic_status", "normal"))
        }

        write_sensor_data(sensor_data)

    except Exception as e:
        print(f"Error processing message: {e}")

def on_disconnect(client, userdata, rc, properties=None):
    print("Disconnected from TTN")

# ============================================
# MAIN
# ============================================

def main():
    print("\n" + "=" * 50)
    print("   BeeGuardAI - MQTT Listener")
    print("=" * 50)

    print(f"\nConnecting to TTN: {TTN_HOST}:{TTN_PORT}")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(f"{TTN_APP_ID}@ttn", TTN_API_KEY)

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    try:
        client.connect(TTN_HOST, TTN_PORT, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        client.disconnect()
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    main()
