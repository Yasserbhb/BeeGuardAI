"""
BeeGuardAI - Clear InfluxDB Data

Deletes all sensor data from InfluxDB to start fresh.
Run: python clear_data.py
"""

from influxdb_client import InfluxDBClient
from datetime import datetime, timezone

# Configuration
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "beeguardai-super-secret-token"
INFLUX_ORG = "beeguardai"
INFLUX_BUCKET = "sensor_data"


def main():
    print("=" * 50)
    print("  BeeGuardAI - Clear InfluxDB Data")
    print("=" * 50)

    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    delete_api = client.delete_api()

    # Delete all data from the beginning of time until now
    start = "1970-01-01T00:00:00Z"
    stop = datetime.now(timezone.utc).isoformat()

    print(f"\nDeleting all data from bucket '{INFLUX_BUCKET}'...")

    try:
        delete_api.delete(
            start=start,
            stop=stop,
            predicate='_measurement="sensor_data"',
            bucket=INFLUX_BUCKET,
            org=INFLUX_ORG
        )
        print("All sensor data deleted successfully!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

    print("\nYou can now run simulate_device.py to generate fresh data.")


if __name__ == "__main__":
    main()
