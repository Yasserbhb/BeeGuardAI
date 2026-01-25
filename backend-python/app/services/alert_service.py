"""
BeeGuardAI - Alert Service
Checks for hornet alerts and sends email notifications
"""

import asyncio
import threading
from datetime import datetime, timedelta
from app.db.mysql import get_db
from app.db.influxdb import query_api
from app.config import INFLUX_BUCKET
from .email_service import send_hornet_alert

# Track last alert time per ruche to avoid spam
last_alert_times = {}
ALERT_COOLDOWN_MINUTES = 60  # Don't send another alert for same ruche within 1 hour


def get_hourly_stats(ruche_id: int):
    """Get hornet and bee counts for last hour"""
    query = f'''
        from(bucket: "{INFLUX_BUCKET}")
            |> range(start: -1h)
            |> filter(fn: (r) => r._measurement == "sensor_data")
            |> filter(fn: (r) => r.ruche_id == "{ruche_id}")
            |> filter(fn: (r) => r._field == "nombre_frelons" or r._field == "nombre_abeilles")
            |> sum()
    '''

    try:
        result = query_api.query(query)
        stats = {"hornets": 0, "bees": 0}

        for table in result:
            for record in table.records:
                field = record.values.get("_field")
                value = record.get_value() or 0
                if field == "nombre_frelons":
                    stats["hornets"] = int(value)
                elif field == "nombre_abeilles":
                    stats["bees"] = int(value)

        return stats
    except Exception as e:
        print(f"❌ Error getting hourly stats for ruche {ruche_id}: {e}")
        return {"hornets": 0, "bees": 0}


def check_alerts():
    """Check all users' alert settings and send notifications if thresholds exceeded"""
    print("🔔 Checking hornet alerts...")

    conn = get_db()
    cursor = conn.cursor()

    # Get users with alerts enabled
    cursor.execute("""
        SELECT us.*, u.email as user_email
        FROM user_settings us
        JOIN utilisateurs u ON us.user_id = u.id
        WHERE us.alerts_enabled = TRUE
    """)
    users_with_alerts = cursor.fetchall()

    for user_settings in users_with_alerts:
        user_id = user_settings["user_id"]
        alert_email = user_settings["alerts_email"] or user_settings["user_email"]
        threshold = user_settings["alerts_threshold"]

        if not alert_email:
            continue

        # Get user's ruches
        cursor.execute("""
            SELECT r.id, r.nom, rc.nom as rucher_nom
            FROM ruches r
            LEFT JOIN ruchers rc ON r.rucher_id = rc.id
            JOIN utilisateurs u ON r.organisation_id = u.organisation_id
            WHERE u.id = %s
        """, (user_id,))
        ruches = cursor.fetchall()

        for ruche in ruches:
            ruche_id = ruche["id"]
            ruche_name = ruche["nom"]
            rucher_name = ruche["rucher_nom"] or "Sans rucher"

            # Check cooldown
            cooldown_key = f"{user_id}_{ruche_id}"
            if cooldown_key in last_alert_times:
                last_alert = last_alert_times[cooldown_key]
                if datetime.now() - last_alert < timedelta(minutes=ALERT_COOLDOWN_MINUTES):
                    continue

            # Get hourly stats
            stats = get_hourly_stats(ruche_id)
            hornets = stats["hornets"]
            bees = stats["bees"]

            # Calculate ratio
            if bees > 0:
                ratio = (hornets / bees) * 100
            else:
                ratio = 100 if hornets > 0 else 0

            # Check threshold
            if ratio >= threshold and hornets > 0:
                print(f"⚠️  Alert triggered for {ruche_name}: {ratio:.1f}% (threshold: {threshold}%)")

                # Send alert
                success = send_hornet_alert(
                    to_email=alert_email,
                    ruche_name=ruche_name,
                    rucher_name=rucher_name,
                    hornet_count=hornets,
                    bee_count=bees,
                    ratio=ratio
                )

                if success:
                    last_alert_times[cooldown_key] = datetime.now()

    conn.close()
    print("✅ Alert check complete")


def alert_checker_loop():
    """Background loop that checks alerts every 5 minutes"""
    while True:
        try:
            check_alerts()
        except Exception as e:
            print(f"❌ Alert checker error: {e}")

        # Wait 5 minutes before next check
        asyncio.run(asyncio.sleep(300))


def start_alert_scheduler():
    """Start the background alert checker thread"""
    thread = threading.Thread(target=alert_checker_loop, daemon=True)
    thread.start()
    print("🔔 Alert scheduler started (checking every 5 minutes)")
