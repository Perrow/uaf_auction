# coding=utf-8

"""Prevent editing posts after their labels have been printed."""

import sqlite3
from functools import wraps

from flask import current_app, flash, g, redirect, request, url_for
from flask_login import current_user


def _database_path():
    return current_app.config['DATABASE']


def _is_printed(post_id):
    """Return True when the post exists and its label has been printed."""
    if not post_id:
        return False

    cache = getattr(g, '_printed_post_cache', None)
    if cache is None:
        cache = {}
        g._printed_post_cache = cache

    key = str(post_id)
    if key not in cache:
        conn = sqlite3.connect(_database_path())
        with conn:
            row = conn.execute(
                'SELECT label_printed FROM posts WHERE obj_id = ?',
                [post_id],
            ).fetchone()
        cache[key] = bool(row and row[0] == 'yes')

    return cache[key]


def post_is_editable(post_id):
    """Jinja helper used by post lists."""
    return not _is_printed(post_id)


def _redirect_after_block():
    if request.referrer:
        return redirect(request.referrer)
    if current_user.is_admin:
        return redirect(url_for('list_posts'))
    return redirect(url_for('list_my_posts'))


def _wrap_edit_post(original_view):
    @wraps(original_view)
    def wrapped(post_id=None, *args, **kwargs):
        requested_post_id = request.form.get('post_id') if request.method == 'POST' else post_id

        if requested_post_id and _is_printed(requested_post_id):
            flash('Posten kan inte ändras eftersom etiketten redan är utskriven.')
            return _redirect_after_block()

        return original_view(post_id=post_id, *args, **kwargs)

    return wrapped


def register_routes(app):
    """Install edit protection and template helper."""
    app.jinja_env.globals['post_is_editable'] = post_is_editable

    if not app.config.get('_PRINTED_POST_LOCK_INSTALLED'):
        if 'edit_post' in app.view_functions:
            app.view_functions['edit_post'] = _wrap_edit_post(app.view_functions['edit_post'])
        app.config['_PRINTED_POST_LOCK_INSTALLED'] = True
