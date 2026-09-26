# coding=utf-8

"""Support optional extra labels containing description text that does not fit."""

import sqlite3
from functools import wraps

from flask import current_app, g, redirect, request, url_for
from flask_login import current_user

import uaf
import zlabels


def _database_path():
    return current_app.config["DATABASE"]


def _ensure_schema(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS extra_labels (
            post_id INTEGER PRIMARY KEY,
            text TEXT NOT NULL
        )
        """
    )


def _label_generator():
    generator = getattr(g, "_extra_label_generator", None)
    if generator is not None:
        return generator

    conn = sqlite3.connect(_database_path())
    with conn:
        _ensure_schema(conn)
        row = conn.execute("SELECT label_type, border FROM label_type").fetchone()

    label_type = zlabels.ZLabels.without_margins_24
    border = "no"
    if row is not None:
        label_type = row[0]
        border = row[1]

    generator = zlabels.ZLabels("extra-label", "", "", label_type, border)
    g._extra_label_generator = generator
    return generator


def _overflow_text(scientific_name, plain_name, description):
    return _label_generator().description_overflow_text(
        scientific_name,
        plain_name,
        description,
    )


def _save_extra_label(conn, post_id, text):
    if text:
        conn.execute(
            """
            INSERT INTO extra_labels (post_id, text)
            VALUES (?, ?)
            ON CONFLICT(post_id) DO UPDATE SET text = excluded.text
            """,
            [post_id, text],
        )
    else:
        conn.execute("DELETE FROM extra_labels WHERE post_id = ?", [post_id])


def _post_ids_with_extra_labels():
    cached = getattr(g, "_extra_label_post_ids", None)
    if cached is not None:
        return cached

    conn = sqlite3.connect(_database_path())
    with conn:
        _ensure_schema(conn)
        cached = {row[0] for row in conn.execute("SELECT post_id FROM extra_labels")}

    g._extra_label_post_ids = cached
    return cached


def _extra_label_fits(post_id):
    """Return True when an existing extra label can print all of its text."""
    cache = getattr(g, "_extra_label_fits", None)
    if cache is None:
        cache = {}
        g._extra_label_fits = cache

    post_id = int(post_id)
    if post_id in cache:
        return cache[post_id]

    conn = sqlite3.connect(_database_path())
    with conn:
        _ensure_schema(conn)
        row = conn.execute(
            "SELECT text FROM extra_labels WHERE post_id = ?",
            [post_id],
        ).fetchone()

    fits = bool(row and row[0]) and not _label_generator().extra_label_overflows(row[0])
    cache[post_id] = fits
    return fits


def _wrap_registration_view(original_view, is_admin):
    @wraps(original_view)
    def wrapped(*args, **kwargs):
        if request.method != "POST":
            return original_view(*args, **kwargs)

        seller_id = request.form.get("seller_select") if is_admin else current_user.get_id()
        conn = sqlite3.connect(_database_path())
        with conn:
            _ensure_schema(conn)
            row = conn.execute(
                "SELECT COALESCE(MAX(obj_id), 0) FROM posts WHERE seller_id = ?",
                [seller_id],
            ).fetchone()
            previous_max_id = row[0] if row else 0

        scientific_names = request.form.getlist("sciname")
        plain_names = request.form.getlist("popname")
        descriptions = request.form.getlist("description")

        response = original_view(*args, **kwargs)

        conn = sqlite3.connect(_database_path())
        with conn:
            _ensure_schema(conn)
            created_ids = [
                row[0]
                for row in conn.execute(
                    """
                    SELECT obj_id
                    FROM posts
                    WHERE seller_id = ? AND obj_id > ?
                    ORDER BY obj_id
                    """,
                    [seller_id, previous_max_id],
                )
            ]

            submitted_indexes = []
            for index, (scientific_name, plain_name) in enumerate(
                zip(scientific_names, plain_names)
            ):
                if is_admin or scientific_name or plain_name:
                    submitted_indexes.append(index)

            for post_id, index in zip(created_ids, submitted_indexes):
                if request.form.get("extra_label_{}".format(index)):
                    text = _overflow_text(
                        scientific_names[index],
                        plain_names[index],
                        descriptions[index],
                    )
                    _save_extra_label(conn, post_id, text)

        return response

    return wrapped


def _wrap_edit_view(original_view):
    @wraps(original_view)
    def wrapped(*args, **kwargs):
        if request.method != "POST":
            return original_view(*args, **kwargs)

        post_id = request.form.get("post_id")
        own_post = False
        if post_id:
            conn = sqlite3.connect(_database_path())
            with conn:
                row = conn.execute(
                    "SELECT seller_id FROM posts WHERE obj_id = ?",
                    [post_id],
                ).fetchone()
                own_post = bool(
                    row and str(row[0]) == str(current_user.get_id())
                )

        response = original_view(*args, **kwargs)

        if post_id:
            conn = sqlite3.connect(_database_path())
            with conn:
                _ensure_schema(conn)
                if request.form.get("extra_label"):
                    text = _overflow_text(
                        request.form.get("sciname", ""),
                        request.form.get("popname", ""),
                        request.form.get("description", ""),
                    )
                    _save_extra_label(conn, post_id, text)
                else:
                    _save_extra_label(conn, post_id, "")

        if own_post:
            return redirect(url_for("list_my_posts"))

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
                conn.execute("DELETE FROM extra_labels")

        return response

    return wrapped


def _get_labels_pdf(selected_id=None, only_printed=False, mark_printed=False):
    conn = sqlite3.connect(_database_path())
    with conn:
        _ensure_schema(conn)
        cur = conn.cursor()

        cur.execute("SELECT event_name, date FROM auction_info")
        auction_info = cur.fetchone()
        auction_name = auction_info[0]
        auction_date = auction_info[1]

        cur.execute("SELECT label_type, border FROM label_type")
        label_setup = cur.fetchone()
        label_type = zlabels.ZLabels.without_margins_24
        border = "no"
        if label_setup is not None:
            label_type = label_setup[0]
            border = label_setup[1]

        labels = zlabels.ZLabels("mypdf", auction_name, auction_date, label_type, border)

        if selected_id:
            cur.execute(
                "SELECT seller_id, name, phone, aquarium_club FROM sellers WHERE seller_id = ?",
                [selected_id],
            )
        else:
            cur.execute("SELECT seller_id, name, phone, aquarium_club FROM sellers")
        sellers = cur.fetchall()

        data = []
        printed_labels = []

        for seller in sellers:
            seller_id = seller[0]
            sql = """
                SELECT posts.obj_id,
                       posts.plain_name,
                       posts.scientific_name,
                       posts.fixed_price,
                       posts.minimum_price,
                       all_types.sale_type,
                       posts.quantity,
                       posts.description,
                       extra_labels.text
                FROM posts
                INNER JOIN all_types ON posts.type = all_types.type_id
                LEFT JOIN extra_labels ON extra_labels.post_id = posts.obj_id
                WHERE posts.seller_id = ?
            """
            parameters = [seller_id]
            if only_printed:
                sql += " AND posts.label_printed = 'no'"

            cur.execute(sql, parameters)
            posts = cur.fetchall()

            post_data = []
            for post in posts:
                printed_labels.append(str(post[0]))
                ordinary = [
                    post[0],
                    post[1],
                    post[2],
                    post[3],
                    post[4],
                    post[5],
                    post[6],
                    post[7],
                ]
                post_data.append(ordinary)

                if post[8]:
                    post_data.append(ordinary + [post[8]])

            data.append([seller[0], seller[1], seller[2], seller[3], post_data])

        if mark_printed and printed_labels:
            placeholders = ", ".join(["?"] * len(printed_labels))
            cur.execute(
                "UPDATE posts SET label_printed = 'yes' WHERE obj_id IN ({})".format(placeholders),
                printed_labels,
            )

    return labels.make_pdf(data)


def register_routes(app):
    """Register storage, form hooks and PDF support for extra labels."""
    conn = sqlite3.connect(app.config["DATABASE"])
    with conn:
        _ensure_schema(conn)

    app.jinja_env.globals["post_has_extra_label"] = (
        lambda post_id: int(post_id) in _post_ids_with_extra_labels()
    )
    app.jinja_env.globals["post_extra_label_fits"] = _extra_label_fits

    if not app.config.get("_EXTRA_LABEL_VIEWS_WRAPPED"):
        if "register_many_posts" in app.view_functions:
            app.view_functions["register_many_posts"] = _wrap_registration_view(
                app.view_functions["register_many_posts"],
                is_admin=False,
            )

        if "admin_register_many_posts" in app.view_functions:
            app.view_functions["admin_register_many_posts"] = _wrap_registration_view(
                app.view_functions["admin_register_many_posts"],
                is_admin=True,
            )

        if "edit_post" in app.view_functions:
            app.view_functions["edit_post"] = _wrap_edit_view(
                app.view_functions["edit_post"]
            )

        if "create_event" in app.view_functions:
            app.view_functions["create_event"] = _wrap_create_event(
                app.view_functions["create_event"]
            )

        app.config["_EXTRA_LABEL_VIEWS_WRAPPED"] = True

    uaf.get_labels_pdf = _get_labels_pdf
