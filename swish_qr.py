# coding=utf-8

"""Generate pre-filled Swish QR codes through the official Swish QR API."""

import json
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Response, current_app, jsonify, request
from flask_login import current_user, login_required

from payment_records import create_pending_payment, remember_pending_payment


SWISH_QR_URL = 'https://mpc.getswish.net/qrg-swish/api/v1/prefilled'


def _parse_items(payload):
    items = payload.get('items') if isinstance(payload, dict) else None
    if not isinstance(items, list) or not items:
        raise ValueError('Inga poster angavs.')

    normalized_items = []
    total = Decimal('0')
    seen = set()

    for item in items:
        if not isinstance(item, dict):
            raise ValueError('Ogiltig postinformation.')

        post_id = str(item.get('post_id', '')).strip()
        if not post_id.isdigit():
            raise ValueError('Ogiltigt postnummer.')
        post_id = str(int(post_id))
        if post_id in seen:
            raise ValueError('Samma postnummer kan inte förekomma flera gånger.')
        seen.add(post_id)

        try:
            price = Decimal(str(item.get('price', '')).strip()).quantize(Decimal('0.01'))
        except (InvalidOperation, ValueError):
            raise ValueError('Alla poster måste ha ett giltigt pris.')

        if not price.is_finite() or price <= 0:
            raise ValueError('Alla poster måste ha ett pris större än noll.')

        normalized_items.append((post_id, price))
        total += price

    return normalized_items, total.quantize(Decimal('0.01'))


@login_required
def swish_qr_image():
    if not current_user.is_admin:
        return jsonify({'error': 'Endast administratörer kan skapa Swish-QR.'}), 403

    configured_number = current_app.config.get('SWISH_NUMBER', '')
    swish_number = ''.join(ch for ch in str(configured_number) if ch.isdigit())
    if not swish_number:
        return jsonify({'error': 'Swishnummer är inte konfigurerat.'}), 503

    try:
        items, amount = _parse_items(request.get_json(silent=True) or {})
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    try:
        payment_id, reference = create_pending_payment(amount)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 500

    message = 'Referens: {}'.format(reference)
    swish_payload = {
        'format': 'png',
        'payee': {
            'value': swish_number,
            'editable': False,
        },
        'amount': {
            'value': float(amount),
            'editable': False,
        },
        'message': {
            'value': message,
            'editable': False,
        },
        'size': 500,
        'border': 2,
        'transparent': False,
    }

    swish_request = Request(
        SWISH_QR_URL,
        data=json.dumps(swish_payload).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    try:
        with urlopen(swish_request, timeout=10) as swish_response:
            qr_image = swish_response.read()
    except HTTPError as exc:
        current_app.logger.warning('Swish QR API returned HTTP %s', exc.code)
        return jsonify({'error': 'Swish kunde inte skapa QR-koden.'}), 502
    except URLError as exc:
        current_app.logger.warning('Swish QR API could not be reached: %s', exc.reason)
        return jsonify({'error': 'Det gick inte att nå Swish QR-tjänst.'}), 502

    remember_pending_payment(payment_id, items)

    response = Response(qr_image, mimetype='image/png')
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Swish-Amount'] = format(amount, 'f')
    response.headers['X-Swish-Message'] = message
    response.headers['X-Payment-Id'] = str(payment_id)
    response.headers['X-Payment-Reference'] = reference
    return response


def register_routes(app):
    """Register the Swish QR endpoint on an existing Flask app."""
    if 'swish_qr_image' in app.view_functions:
        return

    app.add_url_rule(
        '/swish_qr',
        endpoint='swish_qr_image',
        view_func=swish_qr_image,
        methods=['POST'],
    )
