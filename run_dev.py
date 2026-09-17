# coding=utf-8

"""Start the development server with optional feature routes registered."""

from uaf import app
import label_preview
import post_limit
import printed_post_lock
import swish_qr


label_preview.register_routes(app)
post_limit.register_routes(app)
printed_post_lock.register_routes(app)
swish_qr.register_routes(app)


if __name__ == '__main__':
    app.run(debug=True)
