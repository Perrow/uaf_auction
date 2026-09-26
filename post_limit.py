# coding=utf-8

"""Configurable maximum number of registered auction posts."""

import sqlite3
from functools import wraps

from flask import current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required


LIMIT_COLUMN = 'max_registered_posts'
AUCTION_FLAG_COLUMN = 'is_auction'
TRIGGER_NAME = 'enforce_max_registered_auction_posts'
OLD_TRIGGER_NAME = 'enforce_max_registered_posts'
TRIGGER_ERROR = 'MAX_REGISTERED_POSTS_REACHED'


def _database_path():
    return current_app.config['DATABASE']


def _table_exists(cur, table_name):
    cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        [table_name],
    )
    return cur.fetchone() is not None


def _table_columns(cur, table_name):
    cur.execute('PRAGMA table_info({})'.format(table_name))
    return [row[1] for row in cur.fetchall()]


def _ensure_auction_type_flags(cur):
    """Add/backfill is_auction on the category tables when needed."""
    if _table_exists(cur, 'all_types'):
        all_type_columns = _table_columns(cur, 'all_types')
        if AUCTION_FLAG_COLUMN not in all_type_columns:
            cur.execute(
                'ALTER TABLE all_types ADD COLUMN is_auction INTEGER NOT NULL DEFAULT 0'
            )
            cur.execute(
                '''
                UPDATE all_types
                SET is_auction = CASE
                    WHEN LOWER(COALESCE(description, '')) LIKE '%auktionen%' THEN 1
                    ELSE 0
                END
                '''
            )

    if _table_exists(cur, 'used_types'):
        used_type_columns = _table_columns(cur, 'used_types')
        if AUCTION_FLAG_COLUMN not in used_type_columns:
            cur.execute(
                'ALTER TABLE used_types ADD COLUMN is_auction INTEGER NOT NULL DEFAULT 0'
            )

        if _table_exists(cur, 'all_types') and AUCTION_FLAG_COLUMN in _table_columns(cur, 'all_types'):
            cur.execute(
                '''
                UPDATE used_types
                SET is_auction = COALESCE(
                    (SELECT all_types.is_auction
                     FROM all_types
                     WHERE all_types.type_id = used_types.type_id),
                    0
                )
                '''
            )


def _ensure_schema(conn):
    cur = conn.cursor()

    if _table_exists(cur, 'auction_info'):
        auction_info_columns = _table_columns(cur, 'auction_info')
        if LIMIT_COLUMN not in auction_info_columns:
            cur.execute('ALTER TABLE auction_info ADD COLUMN max_registered_posts INTEGER')

    _ensure_auction_type_flags(cur)

    cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'trigger' AND name = ?",
        [OLD_TRIGGER_NAME],
    )
    if cur.fetchone() is not None:
        cur.execute('DROP TRIGGER {}'.format(OLD_TRIGGER_NAME))

    if (_table_exists(cur, 'posts') and _table_exists(cur, 'used_types')
            and _table_exists(cur, 'auction_info')):
        cur.execute(
            '''
            CREATE TRIGGER IF NOT EXISTS {trigger_name}
            BEFORE INSERT ON posts
            WHEN (SELECT max_registered_posts FROM auction_info LIMIT 1) IS NOT NULL
             AND EXISTS (
                 SELECT 1
                 FROM used_types
                 WHERE used_types.type_id = NEW.type
                   AND used_types.is_auction = 1
             )
             AND (
                 SELECT COUNT(*)
                 FROM posts
                 INNER JOIN used_types ON used_types.type_id = posts.type
                 WHERE used_types.is_auction = 1
             ) >= (SELECT max_registered_posts FROM auction_info LIMIT 1)
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
        cur.execute(
            '''
            SELECT COUNT(*)
            FROM posts
            INNER JOIN used_types ON used_types.type_id = posts.type
            WHERE used_types.is_auction = 1
            '''
        )
        current_count = cur.fetchone()[0]
        cur.execute('SELECT max_registered_posts FROM auction_info LIMIT 1')
        row = cur.fetchone()
        max_posts = row[0] if row else None
    return current_count, max_posts


def _get_auction_type_ids():
    conn = sqlite3.connect(_database_path(), timeout=30)
    with conn:
        _ensure_schema(conn)
        cur = conn.cursor()
        cur.execute('SELECT type_id FROM used_types WHERE is_auction = 1 ORDER BY type_id')
        return [row[0] for row in cur.fetchall()]


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
                    flash('Maxantal auktionsposter måste vara ett heltal.')
                    return redirect(url_for('post_limit_settings'))

                if max_posts <= 0:
                    flash('Maxantal auktionsposter måste vara större än noll, eller lämnas tomt för obegränsat.')
                    return redirect(url_for('post_limit_settings'))

            cur = conn.cursor()
            cur.execute('UPDATE auction_info SET max_registered_posts = ?', [max_posts])
            if max_posts is None:
                flash('Maxgränsen är borttagen. Antalet auktionsposter är obegränsat.')
            else:
                flash('Maxgränsen är satt till {} auktionsposter.'.format(max_posts))
            return redirect(url_for('post_limit_settings'))

    current_count, max_posts = _get_limit_status()
    return render_template(
        'post_limit.html',
        current_count=current_count,
        max_posts=max_posts,
    )


@_admin_required
def auction_post_limit_status():
    current_count, max_posts = _get_limit_status()
    return jsonify({
        'current_count': current_count,
        'max_posts': max_posts,
        'is_full': max_posts is not None and current_count >= max_posts,
        'auction_type_ids': _get_auction_type_ids(),
    })


def _handle_limit_error(error, fallback_endpoint):
    if TRIGGER_ERROR not in str(error):
        raise error

    current_count, max_posts = _get_limit_status()
    if max_posts is None:
        flash('Posten kunde inte registreras på grund av ett databasfel.')
    else:
        flash(
            'Det finns inte plats för alla nya auktionsposter. Auktionen har {} av {} registrerade auktionsposter.'.format(
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


def _wrap_event_view(original_view, preserve_limit):
    @wraps(original_view)
    def wrapped(*args, **kwargs):
        max_posts = None
        conn = sqlite3.connect(_database_path(), timeout=30)
        with conn:
            _ensure_schema(conn)
            if preserve_limit and _table_exists(conn.cursor(), 'auction_info'):
                cur = conn.cursor()
                cur.execute('SELECT max_registered_posts FROM auction_info LIMIT 1')
                row = cur.fetchone()
                max_posts = row[0] if row else None

        response = original_view(*args, **kwargs)

        # create_event recreates used_types without the new flag. edit_event also
        # repopulates it from all_types. Synchronize the derived table afterwards.
        conn = sqlite3.connect(_database_path(), timeout=30)
        with conn:
            _ensure_schema(conn)
            if preserve_limit and request.method == 'POST':
                conn.execute('UPDATE auction_info SET max_registered_posts = ?', [max_posts])

        return response

    return wrapped


def register_routes(app):
    """Register settings route and enforce the auction-post limit."""
    if 'post_limit_settings' not in app.view_functions:
        app.add_url_rule(
            '/post_limit',
            endpoint='post_limit_settings',
            view_func=post_limit_settings,
            methods=['GET', 'POST'],
        )

    if 'auction_post_limit_status' not in app.view_functions:
        app.add_url_rule(
            '/json_auction_post_limit_status',
            endpoint='auction_post_limit_status',
            view_func=auction_post_limit_status,
            methods=['GET'],
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
        if 'create_event' in app.view_functions:
            app.view_functions['create_event'] = _wrap_event_view(
                app.view_functions['create_event'],
                preserve_limit=False,
            )
        if 'edit_event' in app.view_functions:
            app.view_functions['edit_event'] = _wrap_event_view(
                app.view_functions['edit_event'],
                preserve_limit=True,
            )

        app.config['_POST_LIMIT_VIEWS_WRAPPED'] = True
