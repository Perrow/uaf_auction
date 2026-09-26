# coding=utf-8

"""Shared state for the post currently shown on the auction display."""

import sqlite3
import time
from functools import wraps

from flask import current_app, jsonify, request

import uaf


def _database_path():
    return current_app.config["DATABASE"]


def _ensure_schema(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS display_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            post_id INTEGER,
            updated_at TEXT
        )
        """
    )


def _set_current_post(post_id):
    conn = sqlite3.connect(_database_path())
    with conn:
        _ensure_schema(conn)
        conn.execute(
            """
            INSERT INTO display_state (id, post_id, updated_at)
            VALUES (1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                post_id = excluded.post_id,
                updated_at = excluded.updated_at
            """,
            [post_id, time.strftime("%Y-%m-%d %H:%M:%S")],
        )


def _get_current_post():
    conn = sqlite3.connect(_database_path())
    with conn:
        _ensure_schema(conn)
        row = conn.execute(
            "SELECT post_id, updated_at FROM display_state WHERE id = 1"
        ).fetchone()

    if row is None:
        return None, None
    return row[0], row[1]


def _wrap_create_event(original_view):
    @wraps(original_view)
    def wrapped(*args, **kwargs):
        response = original_view(*args, **kwargs)

        if request.method == "POST":
            _set_current_post(None)

        return response

    return wrapped


def register_routes(app):
    conn = sqlite3.connect(app.config["DATABASE"])
    with conn:
        _ensure_schema(conn)

    if "display_state_api" not in app.view_functions:
        @app.route("/json_display_state", methods=["GET", "POST"])
        @uaf.admin_required
        def display_state_api():
            if request.method == "POST":
                payload = request.get_json(silent=True) or {}
                post_id = payload.get("post_id")

                if post_id in ("", None):
                    _set_current_post(None)
                    return jsonify({"post_id": None})

                try:
                    post_id = int(post_id)
                except (TypeError, ValueError):
                    _set_current_post(None)
                    return jsonify({"post_id": None}), 400

                conn = sqlite3.connect(_database_path())
                with conn:
                    exists = conn.execute(
                        "SELECT 1 FROM posts WHERE obj_id = ?",
                        [post_id],
                    ).fetchone()

                if exists is None:
                    _set_current_post(None)
                    return jsonify({"post_id": None}), 404

                _set_current_post(post_id)
                return jsonify({"post_id": post_id})

            post_id, updated_at = _get_current_post()
            return jsonify({
                "post_id": post_id,
                "updated_at": updated_at,
            })

    if not app.config.get("_DISPLAY_STATE_CREATE_EVENT_WRAPPED"):
        if "create_event" in app.view_functions:
            app.view_functions["create_event"] = _wrap_create_event(
                app.view_functions["create_event"]
            )
        app.config["_DISPLAY_STATE_CREATE_EVENT_WRAPPED"] = True
