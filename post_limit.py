# coding=utf-8

"""Configurable maximum number of registered auction posts."""

import sqlite3
from functools import wraps

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required


LIMIT_COLUMN = 'max_registered_posts'
TRIGGER_NAME = 'enforce_max_registered_posts'
TRIGGER_ERROR = 'MAX_REGISTERED_POSTS_REACHED'


def _database_path():
    return current_app.config['DATABASE']


def _ensure_schema(conn):
    cur = conn.cursor()
    cur.execute('PRAGMA table_info(auction_info)')
    columns = [row[1] for row in cur.fetchall()]
    if LIMIT_COLUMN not in columns:
        cur.execute('ALTER TABLE auction_info ADD COLUMN max_registered_posts INTEGER')

    cur.execute('DROP TRIGGER IF EXISTS {}'.format(TRIGGER_NAME))
    cur.execute(
        '''
        CREATE TRIGGER {trigger_name}
        BEFORE INSERT ON posts
        WHEN (SELECT max_registered_posts FROM auction_info LIMIT 1) IS NOT NULL
         AND (SELECT COUNT(*) FROM posts) >= (SELECT max_registered_posts FROM auction_info LIMIT 1)
        BEGIN
            SELECT RAISE(ABORT, '{trigger_error}');
        END
        '''.format(trigger_name=TRIGGER_NAME, trigger_error=TRIGGER_ERROR)
    )


def _get_limit_status():
    conn = sqlite3.connect(_database_path(), timeout=30)
    with conn:
        _ensure_schema(conn)
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM posts')
        current_count = cur.fetchone()[0]
        cur.execute('SELECT max_registered_posts FROM auction_info LIMIT 1')
        row = cur.fetchone()
        max_posts = row[0] if row else None
    return current_count, max_posts


def _admin_required(func):
    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        if current_user.is_admin:
            return func(*args, **kwargs)
        flash('Du måste vara administratör för att komma åt sidan.')
        return redirect(url_for('index'))

    return wrapper


@_admin_required
def post_limit_settings():
    conn = sqlite3.connect(_database_path(), timeout=30)
    with conn:
        _ensure_schema(conn)

        if request.method == 'POST':
            raw_value = request.form.get('max_registered_posts', '').strip()
            if raw_value == '':
                max_posts = None
            else:
                try:
                    max_posts = int(raw_value)
                except ValueError:
                    flash('Maxantal poster måste vara ett heltal.')
                    return redirect(url_for('post_limit_settings'))

                if max_posts <= 0:
                    flash('Maxantal poster måste vara större än noll, eller lämnas tomt för obegränsat.')
                    return redirect(url_for('post_limit_settings'))

            cur = conn.cursor()
            cur.execute('UPDATE auction_info SET max_registered_posts = ?', [max_posts])
            if max_posts is None:
                flash('Maxgränsen är borttagen. Antalet poster är obegränsat.')
            else:
                flash('Maxgränsen är satt till {} poster.'.format(max_posts))
            return redirect(url_for('post_limit_settings'))

    current_count, max_posts = _get_limit_status()
    return render_template(
        'post_limit.html',
        current_count=current_count,
        max_posts=max_posts,
    )


def _handle_limit_error(error, fallback_endpoint):
    if TRIGGER_ERROR not in str(error):
        raise error

    current_count, max_posts = _get_limit_status()
    if max_posts is None:
        flash('Posten kunde inte registreras på grund av ett databasfel.')
    else:
        flash(
            'Det finns inte plats för fler poster. Auktionen har {} av {} registrerade poster.'.format(
                current_count,
                max_posts,
            )
        )

    return redirect(request.referrer or url_for(fallback_endpoint))


def _wrap_registration_view(original_view, fallback_endpoint):
    @wraps(original_view)
    def wrapped(*args, **kwargs):
        conn = sqlite3.connect(_database_path(), timeout=30)
        with conn:
            _ensure_schema(conn)

        try:
            return original_view(*args, **kwargs)
        except sqlite3.IntegrityError as error:
            return _handle_limit_error(error, fallback_endpoint)

    return wrapped


def _wrap_edit_event(original_view):
    @wraps(original_view)
    def wrapped(*args, **kwargs):
        conn = sqlite3.connect(_database_path(), timeout=30)
        with conn:
            _ensure_schema(conn)
            cur = conn.cursor()
            cur.execute('SELECT max_registered_posts FROM auction_info LIMIT 1')
            row = cur.fetchone()
            max_posts = row[0] if row else None

        response = original_view(*args, **kwargs)

        if request.method == 'POST':
            conn = sqlite3.connect(_database_path(), timeout=30)
            with conn:
                _ensure_schema(conn)
                conn.execute('UPDATE auction_info SET max_registered_posts = ?', [max_posts])

        return response

    return wrapped


def register_routes(app):
    """Register settings route and enforce the post limit on registration routes."""
    if 'post_limit_settings' not in app.view_functions:
        app.add_url_rule(
            '/post_limit',
            endpoint='post_limit_settings',
            view_func=post_limit_settings,
            methods=['GET', 'POST'],
        )

    if not app.config.get('_POST_LIMIT_VIEWS_WRAPPED'):
        if 'register_many_posts' in app.view_functions:
            app.view_functions['register_many_posts'] = _wrap_registration_view(
                app.view_functions['register_many_posts'],
                'register_many_posts',
            )
        if 'admin_register_many_posts' in app.view_functions:
            app.view_functions['admin_register_many_posts'] = _wrap_registration_view(
                app.view_functions['admin_register_many_posts'],
                'admin_register_many_posts',
            )
        if 'edit_event' in app.view_functions:
            app.view_functions['edit_event'] = _wrap_edit_event(app.view_functions['edit_event'])

        app.config['_POST_LIMIT_VIEWS_WRAPPED'] = True
