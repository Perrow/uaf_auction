# coding=utf-8

"""Prefill the new-event form with current event and administrator data."""

import sqlite3
from functools import wraps

from flask import current_app, render_template, request
from flask_login import current_user


def _database_path():
    return current_app.config['DATABASE']


def _wrap_create_event(original_view):
    @wraps(original_view)
    def wrapped(*args, **kwargs):
        if request.method != 'GET':
            return original_view(*args, **kwargs)

        if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
            return original_view(*args, **kwargs)

        conn = sqlite3.connect(_database_path())
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT type_id, description FROM all_types')
            all_types = cur.fetchall()

            cur.execute('SELECT type_id FROM used_types')
            selected_types = {row[0] for row in cur.fetchall()}

            cur.execute(
                '''
                SELECT hosting_association, hosting_association_abrv, city,
                       event_name, commission, description
                FROM auction_info
                '''
            )
            association_info = cur.fetchone()

            cur.execute(
                '''
                SELECT name, address, email, phone, aquarium_club
                FROM sellers
                WHERE seller_id = ?
                ''',
                [current_user.get_id()],
            )
            admin_info = cur.fetchone()

        if association_info:
            hosting_association = association_info[0]
            hosting_association_abrv = association_info[1]
            city = association_info[2]
            event_name = association_info[3]
            commission = association_info[4] * 100
            event_description = association_info[5]
        else:
            hosting_association = None
            hosting_association_abrv = None
            city = None
            event_name = None
            commission = 20
            event_description = None

        admin_info = admin_info or ('', '', '', '', '')

        return render_template(
            'create_event.html',
            all_types=all_types,
            selected_types=selected_types,
            hosting_association=hosting_association,
            hosting_association_abrv=hosting_association_abrv,
            city=city,
            event_name=event_name,
            commission=commission,
            event_description=event_description,
            admin_name=admin_info[0] or '',
            admin_address=admin_info[1] or '',
            admin_email=admin_info[2] or '',
            admin_phone=admin_info[3] or '',
            admin_aquarium_club=admin_info[4] or '',
        )

    return wrapped


def register_routes(app):
    """Attach GET prefilling to the existing create_event endpoint."""
    if app.config.get('_EVENT_PREFILL_INSTALLED'):
        return

    if 'create_event' in app.view_functions:
        app.view_functions['create_event'] = _wrap_create_event(
            app.view_functions['create_event']
        )

    app.config['_EVENT_PREFILL_INSTALLED'] = True
