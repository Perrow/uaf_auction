# coding=utf-8

"""Start the development server with optional feature routes registered."""

from uaf import app
import label_preview


label_preview.register_routes(app)


if __name__ == '__main__':
    app.run(debug=True)
