# coding=utf-8

"""Shared SMTP email delivery helpers."""

import smtplib
from email.mime.text import MIMEText

from flask import current_app


def send_plain_text_email(recipient, subject, body):
    """Send a UTF-8 plain-text email using the application's SMTP settings."""
    host = current_app.config.get("SMTP_HOST", "")
    port = int(current_app.config.get("SMTP_PORT", 25))
    use_ssl = bool(current_app.config.get("SMTP_USE_SSL", False))
    use_starttls = bool(current_app.config.get("SMTP_USE_STARTTLS", False))
    username = current_app.config.get("SMTP_USERNAME", "")
    password = current_app.config.get("SMTP_PASSWORD", "")
    sender = current_app.config.get("SMTP_FROM", "") or username

    if not host:
        raise RuntimeError("SMTP_HOST saknas")
    if not sender:
        raise RuntimeError("SMTP_FROM eller SMTP_USERNAME måste anges")
    if use_ssl and use_starttls:
        raise RuntimeError("SMTP_USE_SSL och SMTP_USE_STARTTLS kan inte båda vara True")
    if username and not password:
        raise RuntimeError("SMTP_PASSWORD saknas för angivet SMTP_USERNAME")

    message = MIMEText(body, "plain", "utf-8")
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient

    server = smtplib.SMTP_SSL(host, port) if use_ssl else smtplib.SMTP(host, port)
    try:
        server.ehlo()
        if use_starttls:
            server.starttls()
            server.ehlo()
        if username:
            server.login(username, password)
        server.sendmail(sender, recipient, message.as_bytes())
    finally:
        server.quit()
