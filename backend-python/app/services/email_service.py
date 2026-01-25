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


def send_hornet_alert(to_email: str, ruche_name: str, rucher_name: str, hornet_count: int, bee_count: int, ratio: float):
    """Send hornet alert email"""

    subject = f"🚨 Alerte Frelons - {ruche_name}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; padding: 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 24px; }}
            .header p {{ margin: 10px 0 0; opacity: 0.9; }}
            .content {{ padding: 30px; }}
            .alert-box {{ background: #fef2f2; border: 2px solid #fecaca; border-radius: 12px; padding: 20px; margin-bottom: 20px; }}
            .alert-box h2 {{ color: #dc2626; margin: 0 0 10px; font-size: 18px; }}
            .stats {{ display: flex; gap: 15px; margin: 20px 0; }}
            .stat {{ flex: 1; background: #f8fafc; border-radius: 10px; padding: 15px; text-align: center; }}
            .stat-value {{ font-size: 28px; font-weight: 700; color: #1e293b; }}
            .stat-label {{ font-size: 12px; color: #64748b; margin-top: 5px; }}
            .ratio {{ background: #ef4444; color: white; padding: 15px 20px; border-radius: 10px; text-align: center; font-size: 18px; font-weight: 600; }}
            .footer {{ background: #f8fafc; padding: 20px; text-align: center; color: #64748b; font-size: 13px; }}
            .btn {{ display: inline-block; background: #f59e0b; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; margin-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🐝 BeeGuardAI</h1>
                <p>Alerte de surveillance</p>
            </div>
            <div class="content">
                <div class="alert-box">
                    <h2>⚠️ Présence de frelons détectée!</h2>
                    <p>Un taux anormal de frelons a été détecté sur votre ruche. Une intervention peut être nécessaire.</p>
                </div>

                <p><strong>Ruche:</strong> {ruche_name}</p>
                <p><strong>Rucher:</strong> {rucher_name}</p>

                <div class="stats">
                    <div class="stat">
                        <div class="stat-value" style="color: #ef4444;">{hornet_count}</div>
                        <div class="stat-label">Frelons détectés</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value" style="color: #22c55e;">{bee_count}</div>
                        <div class="stat-label">Abeilles détectées</div>
                    </div>
                </div>

                <div class="ratio">
                    Ratio frelons/abeilles: {ratio:.1f}%
                </div>

                <p style="margin-top: 20px; color: #64748b;">
                    Cette alerte a été déclenchée car le ratio de frelons par rapport aux abeilles a dépassé votre seuil configuré sur la dernière heure.
                </p>
            </div>
            <div class="footer">
                <p>BeeGuardAI - Surveillance intelligente des ruches</p>
                <p>Vous recevez cet email car les alertes sont activées dans vos paramètres.</p>
            </div>
        </div>
    </body>
    </html>
    """

    return send_email(to_email, subject, html_content)
