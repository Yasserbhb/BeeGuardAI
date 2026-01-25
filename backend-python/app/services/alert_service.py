"""
BeeGuardAI - Alert Service (Averaging Mode)
"""

import asyncio
import threading
from datetime import datetime, timedelta
from app.db.mysql import get_db
# Note: Use the module import to avoid the NoneType issue we fixed earlier
from app.db import influxdb 
from app.config import INFLUX_BUCKET
from .email_service import  send_grouped_hornet_alert

last_alert_times = {}
ALERT_COOLDOWN_MINUTES = 60 

def get_hourly_stats(ruche_id: int):
    """Get AVERAGE hornet and bee counts for the last hour"""
    
    # We use mean() to get the average per sensor reading
    query = f'''
        from(bucket: "{INFLUX_BUCKET}")
            |> range(start: -1h)
            |> filter(fn: (r) => r._measurement == "sensor_data")
            |> filter(fn: (r) => r.ruche_id == "{ruche_id}")
            |> filter(fn: (r) => r._field == "nombre_frelons" or r._field == "nombre_abeilles")
            |> mean()
    '''

    try:
        from app.db import influxdb
        if influxdb.query_api is None:
            return {"hornets_avg": 0.0, "bees_avg": 0.0} # Use 0.0

        result = influxdb.query_api.query(query)
        # Initialize with floats (0.0) to satisfy the type checker
        stats = {"hornets_avg": 0.0, "bees_avg": 0.0}

        for table in result:
            for record in table.records:
                field = record.values.get("_field")
                value = record.get_value() # This comes back as a float from mean()
                
                if value is None:
                    continue

                if field == "nombre_frelons":
                    stats["hornets_avg"] = round(float(value), 1)
                elif field == "nombre_abeilles":
                    stats["bees_avg"] = round(float(value), 1)

        return stats
    except Exception as e:
        print(f"❌ Error getting hourly stats for ruche {ruche_id}: {e}")
        return {"hornets_avg": 0.0, "bees_avg": 0.0}

def check_alerts():
    """Check thresholds and send one grouped email per user if needed"""
    print("🔔 Checking hornet alerts (Grouped Mode)...")

    conn = get_db()
    cursor = conn.cursor()

    # 1. Fetch users with alerts enabled
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

        # 2. Get all ruches for this user
        cursor.execute("""
            SELECT r.id, r.nom, rc.nom as rucher_nom
            FROM ruches r
            LEFT JOIN ruchers rc ON r.rucher_id = rc.id
            JOIN utilisateurs u ON r.organisation_id = u.organisation_id
            WHERE u.id = %s
        """, (user_id,))
        ruches = cursor.fetchall()

        # --- START OF GROUPING LOGIC ---
        alerts_to_send = [] # This list will hold all hives in danger for THIS user

        for ruche in ruches:
            ruche_id = ruche["id"]
            ruche_name = ruche["nom"]
            rucher_name = ruche["rucher_nom"] or "Sans rucher"

            # Check individual cooldown per hive
            cooldown_key = f"{user_id}_{ruche_id}"
            if cooldown_key in last_alert_times:
                if datetime.now() - last_alert_times[cooldown_key] < timedelta(minutes=ALERT_COOLDOWN_MINUTES):
                    continue

            # Fetch data
            stats = get_hourly_stats(ruche_id)
            h_avg = stats["hornets_avg"]
            b_avg = stats["bees_avg"]

            # Calculate ratio
            if b_avg > 0:
                ratio = (h_avg / b_avg) * 100
            else:
                ratio = 100 if h_avg > 0 else 0

            # 3. Instead of sending, we collect
            if ratio >= threshold and h_avg > 0.1:
                print(f"⚠️ Alert collected for {ruche_name}: {ratio:.1f}%")
                
                alerts_to_send.append({
                    "name": ruche_name,
                    "rucher": rucher_name,
                    "ratio": round(ratio, 1),
                    "h_avg": h_avg,
                    "b_avg": b_avg
                })
                
                # Mark as alerted so we don't include it in next 5-min check
                last_alert_times[cooldown_key] = datetime.now()

        # 4. SEND ONE GROUPED EMAIL IF LIST IS NOT EMPTY
        if alerts_to_send:
            print(f"📧 Sending {len(alerts_to_send)} alerts to {alert_email}")
            send_grouped_hornet_alert(
                to_email=alert_email,
                alerts=alerts_to_send
            )
        # --- END OF GROUPING LOGIC ---

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