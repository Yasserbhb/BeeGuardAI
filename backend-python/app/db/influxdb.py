"""
BeeGuardAI - InfluxDB Database
"""

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from app.config import INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET

# Global clients
influx_client = None
write_api = None
query_api = None


def init_influxdb():
    """Initialize InfluxDB connection"""
    global influx_client, write_api, query_api
    influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    write_api = influx_client.write_api(write_options=SYNCHRONOUS)
    query_api = influx_client.query_api()
    print(f"✅ InfluxDB connected: {INFLUX_URL}")


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
        .field("luminosite", int(data.get("luminosite", 1))) \
        .field("etat_abeilles", str(data.get("etat_abeilles", "normal"))) \
        .field("etat_acoustique", str(data.get("etat_acoustique", "normal")))

    write_api.write(bucket=INFLUX_BUCKET, record=point)
    print(f"📊 Data written for Ruche {data.get('ruche_id')}")


def get_latest_data():
    """Get latest data for all beehives"""
    query = f'''
        from(bucket: "{INFLUX_BUCKET}")
            |> range(start: -24h)
            |> filter(fn: (r) => r._measurement == "sensor_data")
            |> last()
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    '''

    result = query_api.query(query)
    data = []

    for table in result:
        for record in table.records:
            data.append({
                "ruche_id": int(record.values.get("ruche_id", 0)),
                "ruche_name": record.values.get("ruche_name", ""),
                "organisation_id": int(record.values.get("organisation_id", 1)),
                "nombre_frelons": record.values.get("nombre_frelons", 0),
                "nombre_abeilles_entrees": record.values.get("nombre_abeilles_entrees", 0),
                "nombre_abeilles_sorties": record.values.get("nombre_abeilles_sorties", 0),
                "temperature": record.values.get("temperature", 0),
                "humidite": record.values.get("humidite", 0),
                "luminosite": record.values.get("luminosite", 1),
                "etat_abeilles": record.values.get("etat_abeilles", "normal"),
                "etat_acoustique": record.values.get("etat_acoustique", "normal"),
                "timestamp": record.get_time().isoformat()
            })

    return data


def get_historical_data(ruche_id: int, hours: int = 168, start_time: str = None, end_time: str = None):
    """Get historical data for a specific beehive"""
    if start_time and end_time:
        time_range = f'range(start: {start_time}, stop: {end_time})'
    else:
        time_range = f'range(start: -{hours}h)'

    query = f'''
        from(bucket: "{INFLUX_BUCKET}")
            |> {time_range}
            |> filter(fn: (r) => r._measurement == "sensor_data")
            |> filter(fn: (r) => r.ruche_id == "{ruche_id}")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            |> sort(columns: ["_time"], desc: false)
    '''

    result = query_api.query(query)
    data = []

    for table in result:
        for record in table.records:
            data.append({
                "timestamp": record.get_time().isoformat(),
                "nombre_frelons": record.values.get("nombre_frelons", 0),
                "nombre_abeilles_entrees": record.values.get("nombre_abeilles_entrees", 0),
                "nombre_abeilles_sorties": record.values.get("nombre_abeilles_sorties", 0),
                "temperature": record.values.get("temperature", 0),
                "humidite": record.values.get("humidite", 0),
                "luminosite": record.values.get("luminosite", 1),
                "etat_abeilles": record.values.get("etat_abeilles", "normal"),
                "etat_acoustique": record.values.get("etat_acoustique", "normal")
            })

    return data
