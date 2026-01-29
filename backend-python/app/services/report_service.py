"""
BeeGuardAI - Report Service
Generates PDF reports and sends them via email
"""

import io
import threading
import time
from datetime import datetime, timedelta
from collections import defaultdict
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.graphics.shapes import Drawing, Polygon, Circle, String, Line, Rect
from reportlab.graphics.charts.barcharts import VerticalBarChart
from app.db.mysql import get_db
from app.db.influxdb import query_api
from app.config import INFLUX_BUCKET
from .email_service import send_email

# Brand colors
HONEY = colors.HexColor("#f59e0b")
HONEY_LIGHT = colors.HexColor("#fbbf24")
GREEN = colors.HexColor("#22c55e")
RED = colors.HexColor("#ef4444")
BLUE = colors.HexColor("#3b82f6")
PURPLE = colors.HexColor("#8b5cf6")
DARK = colors.HexColor("#1e293b")
GRAY = colors.HexColor("#64748b")
LIGHT_GRAY = colors.HexColor("#f1f5f9")
WHITE = colors.white


def draw_logo(x, y, size=30):
    """Draw the hexagon logo"""
    d = Drawing(size, size)
    # Outer hexagon (lighter)
    s = size
    outer = [
        s*0.5, s*0.1,   # top
        s*0.9, s*0.3,   # top-right
        s*0.9, s*0.7,   # bottom-right
        s*0.5, s*0.9,   # bottom
        s*0.1, s*0.7,   # bottom-left
        s*0.1, s*0.3,   # top-left
    ]
    d.add(Polygon(outer, fillColor=HONEY, strokeColor=None, fillOpacity=0.3))

    # Inner hexagon (solid)
    inner = [
        s*0.5, s*0.2,
        s*0.8, s*0.35,
        s*0.8, s*0.65,
        s*0.5, s*0.8,
        s*0.2, s*0.65,
        s*0.2, s*0.35,
    ]
    d.add(Polygon(inner, fillColor=HONEY, strokeColor=None))

    # Center circle
    d.add(Circle(s*0.5, s*0.5, s*0.1, fillColor=DARK, strokeColor=None))

    return d


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
                    "hour": record.get_time().hour,
                    "temperature": record.values.get("temperature", 0),
                    "humidite": record.values.get("humidite", 0),
                    "nombre_abeilles": record.values.get("nombre_abeilles", 0),
                    "nombre_frelons": record.values.get("nombre_frelons", 0),
                })

        return data_points
    except Exception as e:
        print(f"Error getting period data: {e}")
        return []


def calculate_stats(data_points):
    """Calculate comprehensive statistics from data points"""
    if not data_points:
        return None

    temps = [d["temperature"] for d in data_points if d["temperature"]]
    hums = [d["humidite"] for d in data_points if d["humidite"]]
    bees = [d["nombre_abeilles"] for d in data_points if d["nombre_abeilles"] is not None]
    hornets = [d["nombre_frelons"] for d in data_points if d["nombre_frelons"] is not None]

    # Hourly averages
    hourly_temp = defaultdict(list)
    hourly_hornets = defaultdict(list)
    hourly_bees = defaultdict(list)

    for d in data_points:
        h = d["hour"]
        if d["temperature"]:
            hourly_temp[h].append(d["temperature"])
        if d["nombre_frelons"] is not None:
            hourly_hornets[h].append(d["nombre_frelons"])
        if d["nombre_abeilles"] is not None:
            hourly_bees[h].append(d["nombre_abeilles"])

    hourly_temp_avg = {h: sum(v)/len(v) for h, v in hourly_temp.items() if v}
    hourly_hornets_avg = {h: sum(v)/len(v) for h, v in hourly_hornets.items() if v}
    hourly_bees_avg = {h: sum(v)/len(v) for h, v in hourly_bees.items() if v}

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
        "bees_min": min(bees) if bees else 0,
        "hornets_total": sum(hornets),
        "hornets_avg": sum(hornets) / len(hornets) if hornets else 0,
        "hornets_max": max(hornets) if hornets else 0,
        "data_points": len(data_points),
        "hourly_temp": hourly_temp_avg,
        "hourly_hornets": hourly_hornets_avg,
        "hourly_bees": hourly_bees_avg,
    }


def create_hourly_chart(hourly_data, title, color, width=170, height=80):
    """Create a bar chart for hourly data"""
    d = Drawing(width, height)

    if not hourly_data:
        d.add(String(width/2, height/2, "Pas de données", fontSize=8, fillColor=GRAY, textAnchor='middle'))
        return d

    # Get hours 6-22 (daytime)
    hours = list(range(6, 23))
    values = [hourly_data.get(h, 0) for h in hours]
    max_val = max(values) if values and max(values) > 0 else 1

    bar_width = (width - 30) / len(hours)
    chart_height = height - 25

    # Draw bars
    for i, (h, v) in enumerate(zip(hours, values)):
        bar_height = (v / max_val) * chart_height if max_val > 0 else 0
        x = 15 + i * bar_width
        d.add(Rect(x, 15, bar_width - 2, bar_height, fillColor=color, strokeColor=None))

    # X-axis labels (every 4 hours)
    for i, h in enumerate(hours):
        if h % 4 == 0:
            x = 15 + i * bar_width + bar_width/2
            d.add(String(x, 3, f"{h}h", fontSize=6, fillColor=GRAY, textAnchor='middle'))

    # Title
    d.add(String(width/2, height - 8, title, fontSize=7, fillColor=DARK, textAnchor='middle'))

    return d


def generate_report(user_id: int, frequency: str = "weekly") -> bytes:
    """Generate a professional PDF report with charts and colors"""

    days = 7 if frequency == "weekly" else 1
    period_label = "Hebdomadaire" if frequency == "weekly" else "Quotidien"

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=10*mm,
        bottomMargin=10*mm,
        leftMargin=12*mm,
        rightMargin=12*mm
    )

    elements = []
    page_width = A4[0] - 24*mm

    # === HEADER WITH LOGO ===
    logo = draw_logo(0, 0, 35)
    header_data = [
        [logo,
         Paragraph("BeeGuardAI", ParagraphStyle(name='Logo', fontSize=22, textColor=HONEY, fontName='Helvetica-Bold')),
         Paragraph(f"Rapport {period_label}<br/><font size=9 color='#64748b'>{datetime.now().strftime('%d/%m/%Y')}</font>",
                   ParagraphStyle(name='Date', fontSize=12, textColor=DARK, alignment=2))]
    ]
    header_table = Table(header_data, colWidths=[40, page_width - 120, 80])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 5*mm))

    # Colored line separator
    line_drawing = Drawing(page_width, 3)
    line_drawing.add(Rect(0, 0, page_width, 3, fillColor=HONEY, strokeColor=None))
    elements.append(line_drawing)
    elements.append(Spacer(1, 8*mm))

    # === GET DATA ===
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.id, r.nom, rc.nom as rucher_nom
        FROM ruches r
        LEFT JOIN ruchers rc ON r.rucher_id = rc.id
        WHERE r.organisation_id = (SELECT organisation_id FROM utilisateurs WHERE id = %s)
    """, (user_id,))
    ruches = cursor.fetchall()
    conn.close()

    all_stats = []
    all_data_points = []
    for ruche in ruches:
        data_points = get_period_data(ruche["id"], days)
        all_data_points.extend(data_points)
        stats = calculate_stats(data_points)
        if stats:
            all_stats.append({"ruche": ruche, "stats": stats, "data": data_points})

    if not all_stats:
        elements.append(Paragraph("Aucune donnée disponible pour cette période.",
                                  ParagraphStyle(name='NoData', fontSize=12, textColor=GRAY)))
        doc.build(elements)
        buffer.seek(0)
        return buffer.read()

    # === SUMMARY CARDS (Colorful) ===
    total_ruches = len(all_stats)
    total_hornets = sum(s["stats"]["hornets_total"] for s in all_stats)
    total_bees = sum(s["stats"]["bees_total"] for s in all_stats)
    avg_temp = sum(s["stats"]["temp_avg"] for s in all_stats) / len(all_stats)
    avg_hum = sum(s["stats"]["hum_avg"] for s in all_stats) / len(all_stats)
    total_measures = sum(s["stats"]["data_points"] for s in all_stats)

    def stat_card(label, value, color, icon=""):
        return Table(
            [[Paragraph(f"{icon}", ParagraphStyle(name='Icon', fontSize=14, alignment=1))],
             [Paragraph(f"{value}", ParagraphStyle(name='Val', fontSize=18, textColor=WHITE, fontName='Helvetica-Bold', alignment=1))],
             [Paragraph(label, ParagraphStyle(name='Lbl', fontSize=7, textColor=colors.Color(1,1,1,0.8), alignment=1))]],
            colWidths=[page_width/6 - 3]
        )

    # Create colored stat boxes
    card_data = [
        [Paragraph(f"<b>{total_ruches}</b>", ParagraphStyle(name='V1', fontSize=20, textColor=WHITE, alignment=1)),
         Paragraph(f"<b>{int(total_hornets)}</b>", ParagraphStyle(name='V2', fontSize=20, textColor=WHITE, alignment=1)),
         Paragraph(f"<b>{int(total_bees)}</b>", ParagraphStyle(name='V3', fontSize=20, textColor=WHITE, alignment=1)),
         Paragraph(f"<b>{avg_temp:.1f}°</b>", ParagraphStyle(name='V4', fontSize=20, textColor=WHITE, alignment=1)),
         Paragraph(f"<b>{avg_hum:.0f}%</b>", ParagraphStyle(name='V5', fontSize=20, textColor=WHITE, alignment=1)),
         Paragraph(f"<b>{total_measures}</b>", ParagraphStyle(name='V6', fontSize=20, textColor=WHITE, alignment=1))],
        [Paragraph("Ruches", ParagraphStyle(name='L1', fontSize=7, textColor=colors.Color(1,1,1,0.85), alignment=1)),
         Paragraph("Frelons", ParagraphStyle(name='L2', fontSize=7, textColor=colors.Color(1,1,1,0.85), alignment=1)),
         Paragraph("Abeilles", ParagraphStyle(name='L3', fontSize=7, textColor=colors.Color(1,1,1,0.85), alignment=1)),
         Paragraph("Temp moy", ParagraphStyle(name='L4', fontSize=7, textColor=colors.Color(1,1,1,0.85), alignment=1)),
         Paragraph("Humidité", ParagraphStyle(name='L5', fontSize=7, textColor=colors.Color(1,1,1,0.85), alignment=1)),
         Paragraph("Mesures", ParagraphStyle(name='L6', fontSize=7, textColor=colors.Color(1,1,1,0.85), alignment=1))]
    ]

    card_width = page_width / 6
    cards = Table(card_data, colWidths=[card_width]*6)
    cards.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), HONEY),
        ('BACKGROUND', (1, 0), (1, -1), RED),
        ('BACKGROUND', (2, 0), (2, -1), GREEN),
        ('BACKGROUND', (3, 0), (3, -1), BLUE),
        ('BACKGROUND', (4, 0), (4, -1), PURPLE),
        ('BACKGROUND', (5, 0), (5, -1), GRAY),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
        ('TOPPADDING', (0, 1), (-1, 1), 2),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(cards)
    elements.append(Spacer(1, 10*mm))

    # === GLOBAL HOURLY CHARTS ===
    elements.append(Paragraph("Activité par heure (toutes ruches)",
                              ParagraphStyle(name='ChartTitle', fontSize=12, textColor=DARK, fontName='Helvetica-Bold')))
    elements.append(Spacer(1, 3*mm))

    # Aggregate hourly data
    global_hourly_temp = defaultdict(list)
    global_hourly_hornets = defaultdict(list)
    global_hourly_bees = defaultdict(list)

    for d in all_data_points:
        h = d["hour"]
        if d["temperature"]:
            global_hourly_temp[h].append(d["temperature"])
        if d["nombre_frelons"] is not None:
            global_hourly_hornets[h].append(d["nombre_frelons"])
        if d["nombre_abeilles"] is not None:
            global_hourly_bees[h].append(d["nombre_abeilles"])

    global_temp_avg = {h: sum(v)/len(v) for h, v in global_hourly_temp.items() if v}
    global_hornets_avg = {h: sum(v)/len(v) for h, v in global_hourly_hornets.items() if v}
    global_bees_avg = {h: sum(v)/len(v) for h, v in global_hourly_bees.items() if v}

    chart_width = page_width / 3 - 5
    charts_data = [[
        create_hourly_chart(global_temp_avg, "Température (°C)", BLUE, chart_width, 70),
        create_hourly_chart(global_bees_avg, "Abeilles (moy/h)", GREEN, chart_width, 70),
        create_hourly_chart(global_hornets_avg, "Frelons (moy/h)", RED, chart_width, 70),
    ]]
    charts_table = Table(charts_data, colWidths=[chart_width + 5]*3)
    charts_table.setStyle(TableStyle([
        ('BOX', (0, 0), (0, 0), 0.5, colors.HexColor("#e2e8f0")),
        ('BOX', (1, 0), (1, 0), 0.5, colors.HexColor("#e2e8f0")),
        ('BOX', (2, 0), (2, 0), 0.5, colors.HexColor("#e2e8f0")),
        ('BACKGROUND', (0, 0), (-1, -1), WHITE),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(charts_table)
    elements.append(Spacer(1, 10*mm))

    # === DETAIL PER RUCHE ===
    elements.append(Paragraph("Détail par ruche",
                              ParagraphStyle(name='Section', fontSize=14, textColor=DARK, fontName='Helvetica-Bold')))
    elements.append(Spacer(1, 5*mm))

    for item in all_stats:
        ruche = item["ruche"]
        stats = item["stats"]

        is_alert = stats['hornets_total'] > 0
        status_color = RED if is_alert else GREEN
        status_text = "ALERTE" if is_alert else "OK"

        # Ruche header with status badge
        ruche_header = Table([
            [Paragraph(f"<b>{ruche['nom']}</b>", ParagraphStyle(name='RN', fontSize=11, textColor=DARK)),
             Paragraph(f"<font color='{status_color.hexval()}'><b>{status_text}</b></font>",
                       ParagraphStyle(name='ST', fontSize=9, alignment=2))]
        ], colWidths=[page_width - 50, 50])
        ruche_header.setStyle(TableStyle([
            ('BACKGROUND', (1, 0), (1, 0), colors.Color(status_color.red, status_color.green, status_color.blue, 0.15)),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(ruche_header)

        elements.append(Paragraph(f"<font color='#64748b' size=8>{ruche['rucher_nom'] or 'Sans rucher'} | {stats['data_points']} mesures</font>",
                                  ParagraphStyle(name='Loc', fontSize=8)))
        elements.append(Spacer(1, 2*mm))

        # Stats grid
        stat_style = ParagraphStyle(name='StatV', fontSize=10, textColor=DARK, fontName='Helvetica-Bold')
        range_style = ParagraphStyle(name='Range', fontSize=7, textColor=GRAY)
        label_style = ParagraphStyle(name='Lbl', fontSize=7, textColor=GRAY)

        stats_data = [
            [Paragraph("Température", label_style), Paragraph("Humidité", label_style),
             Paragraph("Abeilles", label_style), Paragraph("Frelons", label_style)],
            [Paragraph(f"<font color='#3b82f6'>{stats['temp_avg']:.1f}°C</font>", stat_style),
             Paragraph(f"<font color='#8b5cf6'>{stats['hum_avg']:.0f}%</font>", stat_style),
             Paragraph(f"<font color='#22c55e'>{stats['bees_avg']:.0f}</font>", stat_style),
             Paragraph(f"<font color='#ef4444'>{int(stats['hornets_total'])}</font>", stat_style)],
            [Paragraph(f"{stats['temp_min']:.1f}° - {stats['temp_max']:.1f}°", range_style),
             Paragraph(f"{stats['hum_min']:.0f}% - {stats['hum_max']:.0f}%", range_style),
             Paragraph(f"min {stats['bees_min']} / max {stats['bees_max']}", range_style),
             Paragraph(f"max: {stats['hornets_max']} | moy: {stats['hornets_avg']:.1f}", range_style)],
        ]

        col_width = page_width / 4
        stats_table = Table(stats_data, colWidths=[col_width]*4)
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), LIGHT_GRAY),
            ('BACKGROUND', (0, 1), (-1, -1), WHITE),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(stats_table)
        elements.append(Spacer(1, 6*mm))

    # === FOOTER ===
    elements.append(Spacer(1, 5*mm))
    footer_line = Drawing(page_width, 1)
    footer_line.add(Line(0, 0, page_width, 0, strokeColor=colors.HexColor("#e2e8f0"), strokeWidth=0.5))
    elements.append(footer_line)
    elements.append(Spacer(1, 3*mm))

    footer_data = [[
        draw_logo(0, 0, 20),
        Paragraph(f"Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} | BeeGuardAI",
                  ParagraphStyle(name='Footer', fontSize=8, textColor=GRAY))
    ]]
    footer = Table(footer_data, colWidths=[25, page_width - 25])
    footer.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
    elements.append(footer)

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()


def send_report(user_id: int, email: str, frequency: str):
    """Generate and send a report to a user"""
    period_label = "hebdomadaire" if frequency == "weekly" else "quotidien"

    try:
        pdf_data = generate_report(user_id, frequency)

        subject = f"Rapport {period_label} BeeGuardAI - {datetime.now().strftime('%d/%m/%Y')}"

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
                    <h1>BeeGuardAI</h1>
                    <p>Rapport {period_label}</p>
                </div>
                <div class="content">
                    <p>Bonjour,</p>
                    <p>Veuillez trouver ci-joint votre rapport {period_label} BeeGuardAI.</p>
                    <p>Ce rapport contient:</p>
                    <ul>
                        <li>Statistiques globales de toutes vos ruches</li>
                        <li>Graphiques d'activité par heure</li>
                        <li>Détail par ruche (température, humidité, abeilles, frelons)</li>
                        <li>Valeurs min/max et moyennes</li>
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
        print(f"Failed to generate/send report for user {user_id}: {e}")
        return False


def check_and_send_reports():
    """Check if any reports need to be sent and send them"""
    now = datetime.now()
    current_hour = now.hour
    current_day = now.weekday()

    print(f"Checking reports to send (hour: {current_hour}, day: {current_day})")

    conn = get_db()
    cursor = conn.cursor()

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

        if current_hour != hour_of_day:
            continue

        if frequency == "weekly" and current_day != day_of_week:
            continue

        print(f"Sending {frequency} report to {report_email}")
        send_report(user_id, report_email, frequency)


def report_scheduler_loop():
    """Background loop that checks for reports to send every hour"""
    while True:
        try:
            check_and_send_reports()
        except Exception as e:
            print(f"Report scheduler error: {e}")

        time.sleep(3600)


def start_report_scheduler():
    """Start the background report scheduler thread"""
    thread = threading.Thread(target=report_scheduler_loop, daemon=True)
    thread.start()
    print("Report scheduler started (checking every hour)")
