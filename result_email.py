# coding=utf-8

"""Send each seller's result report as a PDF attachment."""

import smtplib
import sqlite3
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app, render_template

import uaf


def _database_path():
    return current_app.config["DATABASE"]


def _send_pdf(recipient, subject, body, pdf_bytes):
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

    message = MIMEMultipart()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient
    message.attach(MIMEText(body, "plain", "utf-8"))

    attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
    attachment.add_header(
        "Content-Disposition",
        "attachment",
        filename="resultat.pdf",
    )
    message.attach(attachment)

    if use_ssl:
        server = smtplib.SMTP_SSL(host, port)
    else:
        server = smtplib.SMTP(host, port)

    try:
        server.ehlo()
        if use_starttls:
            server.starttls()
            server.ehlo()
        if username:
            server.login(username, password)
        server.sendmail(sender, [recipient], message.as_bytes())
    finally:
        server.quit()


def _eligible_sellers():
    conn = sqlite3.connect(_database_path())
    with conn:
        return conn.execute(
            """
            SELECT sellers.seller_id, sellers.name, sellers.email
            FROM sellers
            WHERE EXISTS (
                SELECT 1
                FROM posts
                WHERE posts.seller_id = sellers.seller_id
                  AND posts.sold_price > 0
            )
            ORDER BY sellers.seller_id
            """
        ).fetchall()


def _event_name():
    conn = sqlite3.connect(_database_path())
    with conn:
        row = conn.execute("SELECT event_name FROM auction_info").fetchone()
    return row[0] if row else "eventet"


def register_routes(app):
    if "email_result_reports" in app.view_functions:
        return

    @app.route("/reports/email_results", methods=["POST"])
    @uaf.admin_required
    def email_result_reports():
        event_name = _event_name()
        sent = []
        skipped = []
        failed = []

        for seller_id, seller_name, email in _eligible_sellers():
            email = (email or "").strip()
            if not email:
                skipped.append({
                    "seller_id": seller_id,
                    "name": seller_name,
                    "reason": "E-postadress saknas",
                })
                continue

            try:
                pdf = uaf.get_compilation_pdf(
                    selected_id=seller_id,
                    include_receipt=False,
                )
                _send_pdf(
                    email,
                    "Resultat från {}".format(event_name),
                    (
                        "Hej {}!\n\n"
                        "Bifogat finns din resultatsammanställning från {}.\n\n"
                        "Vänliga hälsningar"
                    ).format(seller_name, event_name),
                    pdf,
                )
                sent.append({
                    "seller_id": seller_id,
                    "name": seller_name,
                    "email": email,
                })
            except Exception as error:
                current_app.logger.exception(
                    "Kunde inte skicka resultat till säljare %s",
                    seller_id,
                )
                failed.append({
                    "seller_id": seller_id,
                    "name": seller_name,
                    "email": email,
                    "reason": str(error),
                })

        return render_template(
            "email_results_result.html",
            sent=sent,
            skipped=skipped,
            failed=failed,
        )
