# coding=utf-8

"""PDF endpoint for the flea-market payment report."""

import sqlite3

from flask import Response, current_app, redirect, url_for, flash
from flask_login import current_user, login_required

from make_payment_report_pdf import PaymentReport
from payment_records import ensure_schema


@login_required
def payment_report_view():
    if not current_user.is_admin:
        flash('Du måste vara administratör för att komma åt sidan.')
        return redirect(url_for('index'))

    conn = sqlite3.connect(current_app.config['DATABASE'], timeout=30)
    with conn:
        ensure_schema(conn)
        cur = conn.cursor()
        cur.execute(
            '''
            SELECT reference, amount, confirmed_at
            FROM payments
            ORDER BY payment_id DESC
            '''
        )
        payments = cur.fetchall()

        cur.execute('SELECT event_name, date FROM auction_info')
        event = cur.fetchone()

    event_name = event[0] if event else ''
    event_date = event[1] if event else ''
    pdf = PaymentReport(event_name, event_date).make_pdf(payments)

    response = Response(pdf, mimetype='application/pdf')
    response.headers['Content-Disposition'] = 'inline; filename="betalningar.pdf"'
    response.headers['Cache-Control'] = 'no-store'
    return response


def register_routes(app):
    if 'payment_report_view' in app.view_functions:
        return

    app.add_url_rule(
        '/payment_report_view',
        endpoint='payment_report_view',
        view_func=payment_report_view,
        methods=['GET'],
    )
