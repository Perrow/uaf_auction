# coding=utf-8

"""Payment records for flea-market sales."""

import datetime
import hashlib
import sqlite3
from decimal import Decimal, InvalidOperation
from functools import wraps

from flask import current_app, flash, redirect, request, session, url_for
from flask_login import current_user, login_required


PAYMENT_TABLE = 'payments'
PAYMENT_ID_COLUMN = 'payment_id'
SESSION_KEY = 'pending_flea_market_payment'


def _database_path():
    return current_app.config['DATABASE']


def _table_columns(cur, table_name):
    cur.execute('PRAGMA table_info({})'.format(table_name))
    return [row[1] for row in cur.fetchall()]


def ensure_schema(conn):
    """Create the payment schema and migrate an existing posts table."""
    cur = conn.cursor()
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference TEXT NOT NULL UNIQUE,
            amount NUMERIC NOT NULL,
            created_at TEXT NOT NULL,
            confirmed_at TEXT
        )
        '''
    )

    cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'posts'"
    )
    if cur.fetchone() is not None:
        if PAYMENT_ID_COLUMN not in _table_columns(cur, 'posts'):
            cur.execute('ALTER TABLE posts ADD COLUMN payment_id INTEGER')
        cur.execute(
            'CREATE INDEX IF NOT EXISTS idx_posts_payment_id ON posts(payment_id)'
        )


def _timestamp(now=None):
    value = now or datetime.datetime.now()
    return value.strftime('%Y-%m-%d %H:%M:%S')


def normalize_items(items):
    """Normalize (post_id, price) pairs for stable comparison and hashing."""
    normalized = []
    seen = set()

    for post_id, price_value in items:
        post_id = str(post_id).strip()
        if not post_id.isdigit():
            raise ValueError('Ogiltigt postnummer.')
        post_id = str(int(post_id))
        if post_id in seen:
            raise ValueError('Samma postnummer kan inte registreras flera gånger.')
        seen.add(post_id)

        try:
            price = Decimal(str(price_value).strip()).quantize(Decimal('0.01'))
        except (InvalidOperation, ValueError):
            raise ValueError('Alla poster måste ha ett giltigt pris.')
        if not price.is_finite() or price <= 0:
            raise ValueError('Alla poster måste ha ett pris större än noll.')

        normalized.append((post_id, price))

    if not normalized:
        raise ValueError('Inga poster angavs för betalningen.')

    return normalized


def items_signature(items):
    normalized = normalize_items(items)
    canonical = '|'.join(
        '{}:{}'.format(post_id, format(price, '.2f'))
        for post_id, price in normalized
    )
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def remember_pending_payment(payment_id, items):
    session[SESSION_KEY] = {
        'payment_id': int(payment_id),
        'items_signature': items_signature(items),
    }


def create_pending_payment(amount):
    """Create a payment and allocate a concurrency-safe YYYYNNNN reference."""
    try:
        amount = Decimal(str(amount)).quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError):
        raise ValueError('Ogiltigt betalningsbelopp.')

    if not amount.is_finite() or amount <= 0:
        raise ValueError('Betalningsbeloppet måste vara större än noll.')

    now = datetime.datetime.now()
    year = now.strftime('%Y')
    conn = sqlite3.connect(_database_path(), timeout=30, isolation_level=None)
    try:
        conn.execute('BEGIN IMMEDIATE')
        ensure_schema(conn)
        cur = conn.cursor()
        cur.execute(
            '''
            SELECT MAX(CAST(SUBSTR(reference, 5, 4) AS INTEGER))
            FROM payments
            WHERE LENGTH(reference) = 8
              AND SUBSTR(reference, 1, 4) = ?
            ''',
            [year],
        )
        row = cur.fetchone()
        sequence = (row[0] or 0) + 1
        if sequence > 9999:
            raise ValueError('Det finns inga fler betalningsreferenser kvar för {}.'.format(year))

        reference = '{}{:04d}'.format(year, sequence)
        cur.execute(
            '''
            INSERT INTO payments (reference, amount, created_at, confirmed_at)
            VALUES (?, ?, ?, NULL)
            ''',
            [reference, format(amount, 'f'), _timestamp(now)],
        )
        payment_id = cur.lastrowid
        conn.commit()
        return payment_id, reference
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _parse_sale_items():
    pairs = zip(
        request.form.getlist('post_id'),
        request.form.getlist('price'),
    )
    return normalize_items(
        (post_id, price)
        for post_id, price in pairs
        if str(post_id).strip()
    )


def _confirm_flea_market_payment(payment_id, expected_signature):
    try:
        payment_id = int(payment_id)
    except (TypeError, ValueError):
        raise ValueError('Ogiltig betalningsreferens.')

    items = _parse_sale_items()
    if items_signature(items) != expected_signature:
        raise ValueError(
            'Posterna eller priserna har ändrats sedan QR-koden skapades. Skapa en ny QR-kod.'
        )

    total = sum((price for _, price in items), Decimal('0')).quantize(Decimal('0.01'))
    sold_at = _timestamp()

    conn = sqlite3.connect(_database_path(), timeout=30, isolation_level=None)
    try:
        conn.execute('BEGIN IMMEDIATE')
        ensure_schema(conn)
        cur = conn.cursor()
        cur.execute(
            'SELECT reference, amount, confirmed_at FROM payments WHERE payment_id = ?',
            [payment_id],
        )
        payment = cur.fetchone()
        if payment is None:
            raise ValueError('Betalningen finns inte i databasen.')
        if payment[2] is not None:
            raise ValueError('Betalningen är redan bekräftad.')

        stored_amount = Decimal(str(payment[1])).quantize(Decimal('0.01'))
        if stored_amount != total:
            raise ValueError(
                'Betalningsbeloppet {} kr stämmer inte med posternas summa {} kr.'.format(
                    format(stored_amount, 'f'),
                    format(total, 'f'),
                )
            )

        for post_id, price in items:
            cur.execute('SELECT sold_on FROM posts WHERE obj_id = ?', [post_id])
            post = cur.fetchone()
            if post is None:
                raise ValueError('Post {} finns inte i databasen.'.format(post_id))
            if post[0] is not None:
                raise ValueError('Post {} är redan såld.'.format(post_id))

            cur.execute(
                '''
                UPDATE posts
                SET sold_price = ?,
                    sold_on = ?,
                    time_stamp_sold = ?,
                    sold_by = NULL,
                    payment_id = ?
                WHERE obj_id = ?
                ''',
                [format(price, 'f'), 'fasta bordet', sold_at, payment_id, post_id],
            )

        cur.execute(
            'UPDATE payments SET confirmed_at = ? WHERE payment_id = ?',
            [sold_at, payment_id],
        )
        conn.commit()
        return payment[0], len(items)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _wrap_flea_market(original_view):
    @wraps(original_view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            flash('Du måste vara administratör för att komma åt sidan.')
            return redirect(url_for('index'))

        if request.method != 'POST':
            return original_view(*args, **kwargs)

        pending = session.get(SESSION_KEY)
        if not isinstance(pending, dict) or not pending.get('payment_id'):
            flash('Skapa en Swish-QR innan betalningen bekräftas.')
            return redirect(url_for('flea_market'))

        try:
            reference, item_count = _confirm_flea_market_payment(
                pending.get('payment_id'),
                pending.get('items_signature', ''),
            )
        except ValueError as exc:
            flash(str(exc))
            return redirect(url_for('flea_market'))

        session.pop(SESSION_KEY, None)
        flash(
            'Betalning {} bekräftad. {} poster registrerades som sålda.'.format(
                reference,
                item_count,
            )
        )
        return redirect(url_for('flea_market'))

    return wrapped


def _wrap_create_event(original_view):
    @wraps(original_view)
    def wrapped(*args, **kwargs):
        response = original_view(*args, **kwargs)

        if request.method == 'POST' and current_user.is_authenticated and current_user.is_admin:
            conn = sqlite3.connect(_database_path(), timeout=30)
            with conn:
                ensure_schema(conn)
                conn.execute('DELETE FROM payments')
            session.pop(SESSION_KEY, None)

        return response

    return wrapped


def register_routes(app):
    """Migrate the database and attach payment handling to existing routes."""
    with app.app_context():
        conn = sqlite3.connect(app.config['DATABASE'], timeout=30)
        with conn:
            ensure_schema(conn)

    if app.config.get('_PAYMENT_RECORDS_VIEWS_WRAPPED'):
        return

    if 'flea_market' in app.view_functions:
        app.view_functions['flea_market'] = _wrap_flea_market(
            app.view_functions['flea_market']
        )
    if 'create_event' in app.view_functions:
        app.view_functions['create_event'] = _wrap_create_event(
            app.view_functions['create_event']
        )

    app.config['_PAYMENT_RECORDS_VIEWS_WRAPPED'] = True
