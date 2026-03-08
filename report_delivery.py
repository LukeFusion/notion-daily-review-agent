from __future__ import annotations

import smtplib
from email.message import EmailMessage

from config import settings


def send_report_email(subject: str, body: str) -> bool:
    required = [
        settings.report_email_to,
        settings.report_email_from,
        settings.smtp_host,
        settings.smtp_username,
        settings.smtp_password,
    ]
    if not all(required):
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.report_email_from
    msg["To"] = settings.report_email_to
    msg.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            if settings.smtp_use_tls:
                server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
    except Exception as exc:
        print(f"Failed to send report email: {exc}")
        return False

    return True
