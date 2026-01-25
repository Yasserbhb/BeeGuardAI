"""
BeeGuardAI - Email Service
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from app.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_EMAIL, SMTP_FROM_NAME


def send_email(to_email: str, subject: str, html_content: str, attachment: bytes = None, attachment_name: str = None):
    """Send an email with optional PDF attachment"""

    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"⚠️  SMTP not configured - would send email to {to_email}: {subject}")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        msg['To'] = to_email

        # HTML content
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)

        # PDF attachment if provided
        if attachment and attachment_name:
            pdf_part = MIMEApplication(attachment, _subtype='pdf')
            pdf_part.add_header('Content-Disposition', 'attachment', filename=attachment_name)
            msg.attach(pdf_part)

        # Send email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"✅ Email sent to {to_email}: {subject}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {e}")
        return False


def send_grouped_hornet_alert(to_email, alerts):
    """
    Sends a single email containing all hives that triggered an alert.
    'alerts' is a list of dicts: [{'name': '...', 'ratio': 15.2, 'h_avg': 5.2, 'b_avg': 34.1}, ...]
    """
    subject = f"🚨 BeeGuardAI : {len(alerts)} alerte{'s' if len(alerts) > 1 else ''} frelons détectée{'s' if len(alerts) > 1 else ''}"

    # Generate rows for the table
    rows_html = ""
    for a in alerts:
        # Determine status color based on ratio
        color = "#dc2626" if a['ratio'] > 10 else "#f59e0b"
        
        rows_html += f"""
        <tr style="border-bottom: 1px solid #e5e7eb;">
            <td style="padding: 12px; font-weight: 600; color: #1f2937;">{a['name']}</td>
            <td style="padding: 12px; text-align: center; color: #ef4444; font-weight: bold;">{a['h_avg']}</td>
            <td style="padding: 12px; text-align: center; color: #10b981;">{a['b_avg']}</td>
            <td style="padding: 12px; text-align: right;">
                <span style="background: {color}; color: white; padding: 4px 8px; border-radius: 6px; font-size: 13px;">
                    {a['ratio']}%
                </span>
            </td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: 'Segoe UI', sans-serif; background-color: #f9fafb; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; border: 1px solid #e5e7eb; overflow: hidden;">
            <div style="background: #111827; padding: 20px; text-align: center;">
                <h1 style="color: #f59e0b; margin: 0; font-size: 24px;">BeeGuardAI</h1>
                <p style="color: #9ca3af; margin: 5px 0 0;">Alerte de surveillance intelligente</p>
            </div>
            
            <div style="padding: 30px;">
                <h2 style="color: #111827; font-size: 18px; margin-top: 0;">Attention, présence de frelons détectée</h2>
                <p style="color: #4b5563;">Les ruches suivantes ont dépassé votre seuil d'alerte durant la dernière heure :</p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <thead>
                        <tr style="background: #f3f4f6; text-align: left; font-size: 12px; text-transform: uppercase; color: #6b7280;">
                            <th style="padding: 12px;">Ruche</th>
                            <th style="padding: 12px; text-align: center;">Frelons (moy)</th>
                            <th style="padding: 12px; text-align: center;">Abeilles (moy)</th>
                            <th style="padding: 12px; text-align: right;">Ratio</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
                
                <div style="background: #fffbeb; border-left: 4px solid #f59e0b; padding: 15px; margin-top: 20px;">
                    <p style="margin: 0; font-size: 13px; color: #92400e;">
                        <strong>Conseil :</strong> Une intervention physique est recommandée pour vérifier l'état des muselières ou poser des pièges.
                    </p>
                </div>
                
                <div style="text-align: center; margin-top: 30px;">
                    <a href="http://localhost:80" style="background: #f59e0b; color: white; padding: 12px 25px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Accéder au Tableau de Bord</a>
                </div>
            </div>
            
            <div style="background: #f3f4f6; padding: 20px; text-align: center; font-size: 12px; color: #9ca3af;">
                Ce rapport a été généré automatiquement car vous avez activé les alertes dans vos paramètres.
            </div>
        </div>
    </body>
    </html>
    """
    return send_email(to_email, subject, html_content)
