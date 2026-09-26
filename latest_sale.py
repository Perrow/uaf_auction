# coding=utf-8

"""Expose the latest completed auction sale for the display screen."""

import sqlite3

from flask import current_app, jsonify

import uaf


def _database_path():
    return current_app.config["DATABASE"]


def register_routes(app):
    if "latest_auction_sale" in app.view_functions:
        return

    @app.route("/json_latest_auction_sale")
    @uaf.admin_required
    def latest_auction_sale():
        conn = sqlite3.connect(_database_path())
        with conn:
            row = conn.execute(
                """
                SELECT
                    obj_id,
                    plain_name,
                    scientific_name,
                    sold_price,
                    time_stamp_sold
                FROM posts
                WHERE sold_on = 'auktion'
                  AND sold_price IS NOT NULL
                ORDER BY time_stamp_sold DESC, obj_id DESC
                LIMIT 1
                """
            ).fetchone()

        if row is None:
            return jsonify({"sale": None})

        obj_id, plain_name, scientific_name, sold_price, time_stamp_sold = row
        display_name = (plain_name or "").strip() or (scientific_name or "").strip()

        return jsonify({
            "sale": {
                "obj_id": obj_id,
                "name": display_name,
                "sold_price": sold_price,
                "time_stamp_sold": time_stamp_sold,
            }
        })
