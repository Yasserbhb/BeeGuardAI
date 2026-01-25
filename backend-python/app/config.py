"""
BeeGuardAI - Configuration
"""

import os

# InfluxDB
INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "beeguardai-super-secret-token")
INFLUX_ORG = os.getenv("INFLUX_ORG", "beeguardai")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "sensor_data")

# MySQL
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "beeguard")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "secretpassword")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "beeguardai")

# SMTP Email Configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "noreply@beeguardai.com")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "BeeGuardAI")
