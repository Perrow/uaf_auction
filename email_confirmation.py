# coding=utf-8

"""Email confirmation for newly registered seller accounts."""

import hashlib
import secrets
import sqlite3
import time
from functools import wraps

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

import uaf
from smtp_email import send_plain_text_email


TOKEN_LIFETIME_SECONDS = 24 * 60 * 60


def _database_path():
    return current_app.config["DATABASE"]


def _ensure_schema(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS seller_email_confirmation (
            seller_id INTEGER PRIMARY KEY,
            email TEXT NOT NULL,
            confirmed_at INTEGER
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS email_confirmation_tokens (
            token_hash TEXT PRIMARY KEY,
            seller_id INTEGER NOT NULL,
            email TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            expires_at INTEGER NOT NULL,
            used_at INTEGER
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_email_confirmation_tokens_seller
        ON email_confirmation_tokens (seller_id)
        """
    )


def _token_hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _send_confirmation_email(recipient, confirmation_url):
    body = (
        "Bekräfta din e-postadress genom att öppna länken nedan.\n\n"
        "{}\n\n"
        "Länken gäller i 24 timmar och kan bara användas en gång."
        .format(confirmation_url)
    )
    send_plain_text_email(recipient, "Bekräfta din e-postadress", body)


def _create_token(seller_id, email):
    token = secrets.token_urlsafe(32)
    now = int(time.time())

    conn = sqlite3.connect(_database_path())
    with conn:
        _ensure_schema(conn)
        conn.execute(
            """
            INSERT INTO seller_email_confirmation (seller_id, email, confirmed_at)
            VALUES (?, ?, NULL)
            ON CONFLICT(seller_id) DO UPDATE SET
                email = excluded.email,
                confirmed_at = NULL
            """,
            [seller_id, email],
        )
        conn.execute(
            """
            UPDATE email_confirmation_tokens
            SET used_at = ?
            WHERE seller_id = ?
              AND used_at IS NULL
            """,
            [now, seller_id],
        )
        conn.execute(
            """
            INSERT INTO email_confirmation_tokens
                (token_hash, seller_id, email, created_at, expires_at, used_at)
            VALUES (?, ?, ?, ?, ?, NULL)
            """,
            [_token_hash(token), seller_id, email, now, now + TOKEN_LIFETIME_SECONDS],
        )

    return token


def _send_new_confirmation(seller_id, email):
    token = _create_token(seller_id, email)
    confirmation_url = url_for(
        "confirm_email",
        token=token,
        _external=True,
    )
    _send_confirmation_email(email, confirmation_url)


def _confirm_token(token):
    token_hash = _token_hash(token)
    now = int(time.time())
    conn = sqlite3.connect(_database_path(), timeout=30)
    try:
        conn.execute("BEGIN IMMEDIATE")
        _ensure_schema(conn)
        row = conn.execute(
            """
            SELECT seller_id, email
            FROM email_confirmation_tokens
            WHERE token_hash = ?
              AND used_at IS NULL
              AND expires_at >= ?
            """,
            [token_hash, now],
        ).fetchone()

        if row is None:
            conn.rollback()
            return False

        seller_id, email = row
        seller = conn.execute(
            "SELECT email FROM sellers WHERE seller_id = ?",
            [seller_id],
        ).fetchone()

        if seller is None or (seller[0] or "").strip().lower() != email.strip().lower():
            conn.rollback()
            return False

        conn.execute(
            """
            UPDATE seller_email_confirmation
            SET email = ?, confirmed_at = ?
            WHERE seller_id = ?
            """,
            [email, now, seller_id],
        )
        conn.execute(
            """
            UPDATE email_confirmation_tokens
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


def _is_pending(seller_id):
    conn = sqlite3.connect(_database_path())
    with conn:
        _ensure_schema(conn)
        row = conn.execute(
            """
            SELECT confirmed_at
            FROM seller_email_confirmation
            WHERE seller_id = ?
            """,
            [seller_id],
        ).fetchone()
    return row is not None and row[0] is None


def _wrap_register_seller(original_view):
    @wraps(original_view)
    def wrapped(*args, **kwargs):
        if request.method != "POST":
            return original_view(*args, **kwargs)

        email = request.form.get("email", "").strip().lower()
        conn = sqlite3.connect(_database_path())
        with conn:
            existing = conn.execute(
                "SELECT seller_id FROM sellers WHERE email = ?",
                [email],
            ).fetchone()

        response = original_view(*args, **kwargs)

        if existing is None and email:
            conn = sqlite3.connect(_database_path())
            with conn:
                seller = conn.execute(
                    "SELECT seller_id FROM sellers WHERE email = ?",
                    [email],
                ).fetchone()

            if seller is not None:
                try:
                    _send_new_confirmation(seller[0], email)
                    flash("Vi har skickat en bekräftelselänk till din e-postadress.")
                except Exception as error:
                    current_app.logger.exception(
                        "Kunde inte skicka e-postbekräftelse till säljare %s",
                        seller[0],
                    )
                    flash(
                        "Kontot skapades, men bekräftelsemeddelandet kunde inte skickas. "
                        "Du kan begära ett nytt från startsidan."
                    )

        return response

    return wrapped


def _wrap_create_event(original_view):
    @wraps(original_view)
    def wrapped(*args, **kwargs):
        response = original_view(*args, **kwargs)

        if request.method == "POST":
            conn = sqlite3.connect(_database_path())
            with conn:
                _ensure_schema(conn)
                conn.execute("DELETE FROM email_confirmation_tokens")
                conn.execute("DELETE FROM seller_email_confirmation")

        return response

    return wrapped


def register_routes(app):
    conn = sqlite3.connect(app.config["DATABASE"])
    with conn:
        _ensure_schema(conn)

    if "confirm_email" not in app.view_functions:
        @app.route("/confirm_email/<token>")
        def confirm_email(token):
            if _confirm_token(token):
                return render_template("email_confirmation_success.html")
            return render_template("email_confirmation_invalid.html"), 400

    if "resend_email_confirmation" not in app.view_functions:
        @app.route("/email_confirmation/resend", methods=["POST"])
        @login_required
        def resend_email_confirmation():
            seller_id = int(current_user.get_id())
            conn = sqlite3.connect(_database_path())
            with conn:
                row = conn.execute(
                    "SELECT email FROM sellers WHERE seller_id = ?",
                    [seller_id],
                ).fetchone()

            if row is None or not (row[0] or "").strip():
                flash("Det finns ingen e-postadress att bekräfta.")
                return redirect(url_for("index"))

            if not _is_pending(seller_id):
                flash("Din e-postadress är redan bekräftad.")
                return redirect(url_for("index"))

            try:
                _send_new_confirmation(seller_id, row[0].strip().lower())
                flash("En ny bekräftelselänk har skickats.")
            except Exception:
                current_app.logger.exception(
                    "Kunde inte skicka ny e-postbekräftelse till säljare %s",
                    seller_id,
                )
                flash("Bekräftelsemeddelandet kunde inte skickas.")

            return redirect(url_for("index"))

    @app.context_processor
    def email_confirmation_context():
        pending = False
        if current_user.is_authenticated:
            try:
                pending = _is_pending(int(current_user.get_id()))
            except Exception:
                current_app.logger.exception("Kunde inte läsa e-postbekräftelsestatus")
        return {"email_confirmation_pending": pending}

    if not app.config.get("_EMAIL_CONFIRMATION_REGISTER_WRAPPED"):
        if "register_seller" in app.view_functions:
            app.view_functions["register_seller"] = _wrap_register_seller(
                app.view_functions["register_seller"]
            )
        app.config["_EMAIL_CONFIRMATION_REGISTER_WRAPPED"] = True

    if not app.config.get("_EMAIL_CONFIRMATION_CREATE_EVENT_WRAPPED"):
        if "create_event" in app.view_functions:
            app.view_functions["create_event"] = _wrap_create_event(
                app.view_functions["create_event"]
            )
        app.config["_EMAIL_CONFIRMATION_CREATE_EVENT_WRAPPED"] = True
