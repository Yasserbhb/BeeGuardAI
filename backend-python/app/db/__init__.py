# Database module
from .mysql import get_db, init_database
from .influxdb import init_influxdb, write_sensor_data, get_latest_data, get_historical_data
