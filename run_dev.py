# coding=utf-8

"""Start the development server with optional feature routes registered."""

from uaf import app
import display_state
import email_confirmation
import event_prefill
import extra_labels
import label_preview
import latest_sale
import payment_records
import payment_report_pdf
import password_reset
import post_limit
import result_email
import swish_qr


display_state.register_routes(app)
email_confirmation.register_routes(app)
label_preview.register_routes(app)
latest_sale.register_routes(app)
post_limit.register_routes(app)
result_email.register_routes(app)
extra_labels.register_routes(app)
payment_records.register_routes(app)
payment_report_pdf.register_routes(app)
password_reset.register_routes(app)
event_prefill.register_routes(app)
swish_qr.register_routes(app)


if __name__ == '__main__':
    app.run(debug=True)
