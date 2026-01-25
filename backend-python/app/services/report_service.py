"""
BeeGuardAI - Report Service
Generates PDF reports and sends them via email
"""

import io
import threading
import time
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.widgets.markers import makeMarker
from app.db.mysql import get_db
from app.db.influxdb import query_api
from app.config import INFLUX_BUCKET
from .email_service import send_email

# Brand colors
HONEY_COLOR = colors.HexColor("#f59e0b")
BEE_COLOR = colors.HexColor("#fbbf24")
GREEN_COLOR = colors.HexColor("#22c55e")
RED_COLOR = colors.HexColor("#ef4444")
BLUE_COLOR = colors.HexColor("#3b82f6")
DARK_COLOR = colors.HexColor("#1e293b")
GRAY_COLOR = colors.HexColor("#64748b")


def get_period_data(ruche_id: int, days: int):
    """Get aggregated data for the period"""
    query = f'''
        from(bucket: "{INFLUX_BUCKET}")
            |> range(start: -{days}d)
            |> filter(fn: (r) => r._measurement == "sensor_data")
            |> filter(fn: (r) => r.ruche_id == "{ruche_id}")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    '''

    try:
        result = query_api.query(query)
        data_points = []

        for table in result:
            for record in table.records:
                data_points.append({
                    "timestamp": record.get_time(),
                    "temperature": record.values.get("temperature", 0),
                    "humidite": record.values.get("humidite", 0),
                    "nombre_abeilles": record.values.get("nombre_abeilles", 0),
                    "nombre_frelons": record.values.get("nombre_frelons", 0),
                })

        return data_points
    except Exception as e:
        print(f"❌ Error getting period data: {e}")
        return []


def calculate_stats(data_points):
    """Calculate statistics from data points"""
    if not data_points:
        return None

    temps = [d["temperature"] for d in data_points if d["temperature"]]
    hums = [d["humidite"] for d in data_points if d["humidite"]]
    bees = [d["nombre_abeilles"] for d in data_points if d["nombre_abeilles"] is not None]
    hornets = [d["nombre_frelons"] for d in data_points if d["nombre_frelons"] is not None]

    return {
        "temp_avg": sum(temps) / len(temps) if temps else 0,
        "temp_min": min(temps) if temps else 0,
        "temp_max": max(temps) if temps else 0,
        "hum_avg": sum(hums) / len(hums) if hums else 0,
        "hum_min": min(hums) if hums else 0,
        "hum_max": max(hums) if hums else 0,
        "bees_avg": sum(bees) / len(bees) if bees else 0,
        "bees_total": sum(bees),
        "bees_max": max(bees) if bees else 0,
        "hornets_total": sum(hornets),
        "hornets_max": max(hornets) if hornets else 0,
        "data_points": len(data_points),
    }


def generate_report(user_id: int, frequency: str = "weekly") -> bytes:
    """Generate a high-fidelity PDF report mirroring the React dashboard identity"""

    days = 7 if frequency == "weekly" else 1
    period_label = "HEBDOMADAIRE" if frequency == "weekly" else "QUOTIDIEN"

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        topMargin=0, # We'll use a full-width header
        bottomMargin=15*mm, 
        leftMargin=15*mm, 
        rightMargin=15*mm
    )

    styles = getSampleStyleSheet()
    
    # Ensure all used styles are defined
    styles.add(ParagraphStyle(name='BrandLogo', fontSize=22, textColor=HONEY_COLOR, fontName='Helvetica-Bold', spaceAfter=2))
    styles.add(ParagraphStyle(name='ReportType', fontSize=10, textColor=colors.white, fontName='Helvetica-Bold', letterSpacing=2))
    styles.add(ParagraphStyle(name='Subtitle', fontSize=12, textColor=GRAY_COLOR, spaceAfter=20))
    styles.add(ParagraphStyle(name='SectionHeader', fontSize=14, textColor=DARK_COLOR, fontName='Helvetica-Bold', spaceBefore=15, spaceAfter=10))
    styles.add(ParagraphStyle(name='StatLabel', fontSize=8, textColor=GRAY_COLOR, fontName='Helvetica', alignment=1))
    styles.add(ParagraphStyle(name='StatValue', fontSize=14, textColor=DARK_COLOR, fontName='Helvetica-Bold', alignment=1))
    # Card styles for ruche data display
    styles.add(ParagraphStyle(name='SectionTitle', fontSize=14, textColor=DARK_COLOR, fontName='Helvetica-Bold', spaceBefore=15, spaceAfter=10))
    styles.add(ParagraphStyle(name='BadgeAlert', fontSize=10, textColor=RED_COLOR, fontName='Helvetica-Bold', alignment=1))
    styles.add(ParagraphStyle(name='BadgeNormal', fontSize=10, textColor=GREEN_COLOR, fontName='Helvetica-Bold', alignment=1))
    styles.add(ParagraphStyle(name='CardTitle', fontSize=8, textColor=GRAY_COLOR, fontName='Helvetica'))
    styles.add(ParagraphStyle(name='CardValue', fontSize=14, textColor=DARK_COLOR, fontName='Helvetica-Bold'))
    elements = []

    # --- 1. FULL WIDTH BRANDED HEADER ---
    # Matches the black top-bar in your screenshot
    header_data = [[Paragraph("<b>BeeGuardAI</b>", ParagraphStyle(name='H', fontSize=18, textColor=HONEY_COLOR))]]
    header = Table(header_data, colWidths=[210*mm])
    header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#111827")),
        ('LEFTPADDING', (0, 0), (-1, -1), 20*mm),
        ('TOPPADDING', (0, 0), (-1, -1), 10*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10*mm),
    ]))
    elements.append(header)
    elements.append(Spacer(1, 10*mm))

    # Title Section
    elements.append(Paragraph(f"Tableau de bord {period_label.capitalize()}", ParagraphStyle(name='T', fontSize=22, fontName='Helvetica-Bold', textColor=DARK_COLOR)))
    elements.append(Paragraph(f"Période: {days} jour(s) jusqu'au {datetime.now().strftime('%d/%m/%Y')}", styles['Subtitle']))
    elements.append(Spacer(1, 8*mm))

    # --- 2. STAT CARDS (The 4 Boxes) ---
    # We fetch data points for the whole account first to show the top 4 cards
    # For simplicity here, we'll build them for each hive below
    
    # --- 3. RUCHE CARDS ---
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT r.id, r.nom, rc.nom as rucher_nom FROM ruches r LEFT JOIN ruchers rc ON r.rucher_id = rc.id WHERE r.organisation_id = (SELECT organisation_id FROM utilisateurs WHERE id = %s)", (user_id,))
    ruches = cursor.fetchall()
    conn.close()

    for ruche in ruches:
        data_points = get_period_data(ruche["id"], days)
        stats = calculate_stats(data_points)
        
        if not stats: continue

        # Visual Card Header
        elements.append(Paragraph(f"<b>{ruche['nom']}</b> — {ruche['rucher_nom'] or 'Général'}", styles['SectionTitle']))
        
        # Grid layout for hive stats: [Temp] [Hum] [Frelons] [Abeilles]
        is_alert = stats['hornets_total'] > 0
        status_text = "ALERTE" if is_alert else "NORMAL"
        status_style = styles['BadgeAlert'] if is_alert else styles['BadgeNormal']

        card_table_data = [
            [Paragraph("TEMPÉRATURE", styles['CardTitle']), Paragraph("HUMIDITÉ", styles['CardTitle']), Paragraph("FRELONS", styles['CardTitle']), Paragraph("STATUT", styles['CardTitle'])],
            [Paragraph(f"{stats['temp_avg']:.1f}°C", styles['CardValue']), 
             Paragraph(f"{stats['hum_avg']:.0f}%", styles['CardValue']), 
             Paragraph(f"{int(stats['hornets_total'])}", styles['CardValue']),
             Paragraph(status_text, status_style)]
        ]

        t = Table(card_table_data, colWidths=[45*mm, 45*mm, 45*mm, 45*mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#e5e7eb")),
            ('TOPPADDING', (0,0), (-1,-1), 12),
            ('BOTTOMPADDING', (0,0), (-1,-1), 12),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 10*mm))

    # --- 4. DATA CHART (Simple LinePlot) ---
    # This adds the "visual" touch of the dashboard
    elements.append(Paragraph("Activité des Frelons", styles['SectionHeader']))
    drawing = Drawing(400, 150)
    lp = LinePlot()
    lp.x = 30
    lp.y = 30
    lp.height = 100
    lp.width = 350
    # Add logic here to format stats['data_points'] into (x, y) tuples
    drawing.add(lp)
    elements.append(drawing)

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()


def send_report(user_id: int, email: str, frequency: str):
    """Generate and send a report to a user"""
    period_label = "hebdomadaire" if frequency == "weekly" else "quotidien"

    try:
        pdf_data = generate_report(user_id, frequency)

        subject = f"📊 Rapport {period_label} BeeGuardAI - {datetime.now().strftime('%d/%m/%Y')}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .content {{ padding: 30px; }}
                .footer {{ background: #f8fafc; padding: 20px; text-align: center; color: #64748b; font-size: 13px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🐝 BeeGuardAI</h1>
                    <p>Rapport {period_label}</p>
                </div>
                <div class="content">
                    <p>Bonjour,</p>
                    <p>Veuillez trouver ci-joint votre rapport {period_label} BeeGuardAI.</p>
                    <p>Ce rapport contient:</p>
                    <ul>
                        <li>Résumé de toutes vos ruches</li>
                        <li>Températures moyennes, min et max</li>
                        <li>Taux d'humidité</li>
                        <li>Activité des abeilles</li>
                        <li>Détections de frelons</li>
                    </ul>
                    <p>Cordialement,<br>L'équipe BeeGuardAI</p>
                </div>
                <div class="footer">
                    <p>Vous recevez cet email car les rapports sont activés dans vos paramètres.</p>
                </div>
            </div>
        </body>
        </html>
        """

        filename = f"rapport-beeguardai-{datetime.now().strftime('%Y%m%d')}.pdf"
        return send_email(email, subject, html_content, pdf_data, filename)

    except Exception as e:
        print(f"❌ Failed to generate/send report for user {user_id}: {e}")
        return False


def check_and_send_reports():
    """Check if any reports need to be sent and send them"""
    now = datetime.now()
    current_hour = now.hour
    current_day = now.weekday()  # Monday = 0, Sunday = 6

    print(f"📊 Checking reports to send (hour: {current_hour}, day: {current_day})")

    conn = get_db()
    cursor = conn.cursor()

    # Get users with reports enabled
    cursor.execute("""
        SELECT us.*, u.email as user_email
        FROM user_settings us
        JOIN utilisateurs u ON us.user_id = u.id
        WHERE us.reports_enabled = TRUE
    """)
    users_with_reports = cursor.fetchall()
    conn.close()

    for user_settings in users_with_reports:
        user_id = user_settings["user_id"]
        report_email = user_settings["reports_email"] or user_settings["user_email"]
        frequency = user_settings["reports_frequency"]
        day_of_week = user_settings["reports_day_of_week"]
        hour_of_day = user_settings["reports_hour_of_day"]

        if not report_email:
            continue

        # Check if it's time to send
        if current_hour != hour_of_day:
            continue

        if frequency == "weekly" and current_day != day_of_week:
            continue

        print(f"📬 Sending {frequency} report to {report_email}")
        send_report(user_id, report_email, frequency)


def report_scheduler_loop():
    """Background loop that checks for reports to send every hour"""
    while True:
        try:
            check_and_send_reports()
        except Exception as e:
            print(f"❌ Report scheduler error: {e}")

        # Wait 1 hour before next check
        time.sleep(3600)


def start_report_scheduler():
    """Start the background report scheduler thread"""
    thread = threading.Thread(target=report_scheduler_loop, daemon=True)
    thread.start()
    print("📊 Report scheduler started (checking every hour)")
