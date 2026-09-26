# coding=utf-8

"""Password reset by time-limited, single-use email token."""

import hashlib
import secrets
import smtplib
import sqlite3
import time
from email.mime.text import MIMEText
from functools import wraps

import bcrypt
from flask import current_app, flash, redirect, render_template, request, url_for


TOKEN_LIFETIME_SECONDS = 60 * 60


def _database_path():
    return current_app.config["DATABASE"]


def _ensure_schema(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            token_hash TEXT PRIMARY KEY,
            seller_id INTEGER NOT NULL,
            created_at INTEGER NOT NULL,
            expires_at INTEGER NOT NULL,
            used_at INTEGER
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_seller
        ON password_reset_tokens (seller_id)
        """
    )


def _token_hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _send_reset_email(recipient, reset_url):
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

    message = MIMEText(
        "Du har begärt att återställa lösenordet till ditt konto.\n\n"
        "Öppna länken nedan för att välja ett nytt lösenord. "
        "Länken gäller i en timme och kan bara användas en gång.\n\n"
        "{}\n\n"
        "Om du inte begärde återställningen kan du ignorera detta meddelande."
        .format(reset_url)
    )
    message["Subject"] = "Återställ lösenord"
    message["From"] = sender
    message["To"] = recipient

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
        server.sendmail(sender, recipient, message.as_bytes())
    finally:
        server.quit()


def _create_reset_token(seller_id):
    token = secrets.token_urlsafe(32)
    now = int(time.time())

    conn = sqlite3.connect(_database_path())
    with conn:
        _ensure_schema(conn)
        conn.execute(
            """
            INSERT INTO password_reset_tokens
                (token_hash, seller_id, created_at, expires_at, used_at)
            VALUES (?, ?, ?, ?, NULL)
            """,
            [_token_hash(token), seller_id, now, now + TOKEN_LIFETIME_SECONDS],
        )

        # Old unused tokens for the same account should no longer work.
        conn.execute(
            """
            UPDATE password_reset_tokens
            SET used_at = ?
            WHERE seller_id = ?
              AND token_hash <> ?
              AND used_at IS NULL
            """,
            [now, seller_id, _token_hash(token)],
        )

    return token


def _get_valid_token(token):
    now = int(time.time())
    conn = sqlite3.connect(_database_path())
    with conn:
        _ensure_schema(conn)
        return conn.execute(
            """
            SELECT token_hash, seller_id
            FROM password_reset_tokens
            WHERE token_hash = ?
              AND used_at IS NULL
              AND expires_at >= ?
            """,
            [_token_hash(token), now],
        ).fetchone()


def _reset_password(token, password):
    token_hash = _token_hash(token)
    now = int(time.time())
    encrypted_password = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    )

    conn = sqlite3.connect(_database_path(), timeout=30)
    try:
        conn.execute("BEGIN IMMEDIATE")
        _ensure_schema(conn)
        row = conn.execute(
            """
            SELECT seller_id
            FROM password_reset_tokens
            WHERE token_hash = ?
              AND used_at IS NULL
              AND expires_at >= ?
            """,
            [token_hash, now],
        ).fetchone()

        if row is None:
            conn.rollback()
            return False

        seller_id = row[0]
        updated = conn.execute(
            "UPDATE sellers SET password = ? WHERE seller_id = ?",
            [encrypted_password, seller_id],
        )
        if updated.rowcount != 1:
            conn.rollback()
            return False

        conn.execute(
            """
            UPDATE password_reset_tokens
            SET used_at = ?
            WHERE seller_id = ?
              AND used_at IS NULL
            """,
            [now, seller_id],
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _wrap_create_event(original_view):
    @wraps(original_view)
    def wrapped(*args, **kwargs):
        response = original_view(*args, **kwargs)

        if request.method == "POST":
            conn = sqlite3.connect(_database_path())
            with conn:
                _ensure_schema(conn)
                conn.execute("DELETE FROM password_reset_tokens")

        return response

    return wrapped


def register_routes(app):
    """Register password-reset routes and token storage."""
    conn = sqlite3.connect(app.config["DATABASE"])
    with conn:
        _ensure_schema(conn)

    if "forgot_password" not in app.view_functions:
        @app.route("/forgot_password", methods=["GET", "POST"])
        def forgot_password():
            if request.method == "POST":
                email = request.form.get("email", "").strip().lower()

                conn = sqlite3.connect(_database_path())
                with conn:
                    row = conn.execute(
                        "SELECT seller_id, email FROM sellers WHERE lower(email) = ?",
                        [email],
                    ).fetchone()

                if row is not None:
                    token = _create_reset_token(row[0])
                    reset_url = url_for(
                        "reset_password",
                        token=token,
                        _external=True,
                    )
                    try:
                        _send_reset_email(row[1], reset_url)
                    except Exception as error:
                        # Keep the public response identical whether the account
                        # exists or email delivery succeeds.
                        current_app.logger.error(
                            "Kunde inte skicka lösenordsåterställning: %s",
                            error,
                        )

                return render_template("forgot_password_sent.html")

            return render_template("forgot_password.html")

    if "reset_password" not in app.view_functions:
        @app.route("/reset_password/<token>", methods=["GET", "POST"])
        def reset_password(token):
            if _get_valid_token(token) is None:
                return render_template("reset_password_invalid.html"), 400

            if request.method == "POST":
                password = request.form.get("password", "")
                password_confirm = request.form.get("password_confirm", "")

                if not password:
                    flash("Ange ett nytt lösenord.")
                    return render_template("reset_password.html", token=token)

                if password != password_confirm:
                    flash("Lösenorden är inte lika.")
                    return render_template("reset_password.html", token=token)

                if not _reset_password(token, password):
                    return render_template("reset_password_invalid.html"), 400

                flash("Lösenordet är ändrat. Du kan nu logga in.")
                return redirect(url_for("login"))

            return render_template("reset_password.html", token=token)

    if not app.config.get("_PASSWORD_RESET_CREATE_EVENT_WRAPPED"):
        if "create_event" in app.view_functions:
            app.view_functions["create_event"] = _wrap_create_event(
                app.view_functions["create_event"]
            )
        app.config["_PASSWORD_RESET_CREATE_EVENT_WRAPPED"] = True
