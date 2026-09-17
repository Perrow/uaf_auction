# coding=utf-8

"""Generate high-fidelity PNG previews from the existing label PDF renderer."""

import sqlite3

from flask import Response, abort
from flask_login import current_user, login_required

import zlabels


def make_label_preview_png(label_generator, seller, post, dpi=200):
    """Render one auction post as a PNG label preview.

    The preview deliberately uses ``ZLabels.make_pdf`` instead of maintaining a
    second label layout. A temporary one-label PDF is generated with the same
    ReportLab code used for printed labels, after which the first physical label
    rectangle is rasterized to PNG.

    ``seller`` uses the same structure as ZLabels input data:
        [seller_id, seller_name, seller_phone, seller_society, ...]

    ``post`` uses the existing post structure:
        [post_id, pop_name, sci_name, fixed_price, min_price, type,
         quantity, description]

    Args:
        label_generator: Configured ``zlabels.ZLabels`` instance.
        seller: Seller sequence containing at least the first four seller fields.
        post: Post sequence in the format expected by ``ZLabels.make_pdf``.
        dpi: Raster resolution. 200 DPI gives a preview around 500 px wide for
             the current label formats and is a useful compromise for web use.

    Returns:
        PNG image as ``bytes``.

    Raises:
        ValueError: If seller data is incomplete or dpi is invalid.
        RuntimeError: If PyMuPDF is not installed.
    """
    if len(seller) < 4:
        raise ValueError("seller must contain id, name, phone and society")
    if dpi <= 0:
        raise ValueError("dpi must be greater than zero")

    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise RuntimeError(
            "PyMuPDF is required for label previews. Install it with: pip install PyMuPDF"
        ) from exc

    preview_data = [[seller[0], seller[1], seller[2], seller[3], [post]]]
    pdf_bytes = label_generator.make_pdf(preview_data)
    if not pdf_bytes:
        raise RuntimeError("Label renderer did not return a PDF")

    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        page = document.load_page(0)

        # PyMuPDF uses a top-left origin for page rectangles. The first label
        # starts at the configured paper margins and has the exact dimensions
        # used by ZLabels when producing the PDF sheet.
        left = label_generator.paper_left_right_margin
        top = label_generator.paper_top_bottom_margin
        clip = fitz.Rect(
            left,
            top,
            left + label_generator.label_width,
            top + label_generator.label_height,
        )

        scale = float(dpi) / 72.0
        pixmap = page.get_pixmap(
            matrix=fitz.Matrix(scale, scale),
            clip=clip,
            alpha=False,
        )
        return pixmap.tobytes("png")
    finally:
        document.close()


def register_routes(app):
    """Register the label-preview endpoint on an existing Flask application."""
    if "label_preview_image" in app.view_functions:
        return

    @app.route("/label_preview/<int:post_id>.png", endpoint="label_preview_image")
    @login_required
    def label_preview_image(post_id):
        conn = sqlite3.connect(app.config["DATABASE"])
        with conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT sellers.seller_id,
                       sellers.name,
                       sellers.phone,
                       sellers.aquarium_club,
                       posts.obj_id,
                       posts.plain_name,
                       posts.scientific_name,
                       posts.fixed_price,
                       posts.minimum_price,
                       all_types.sale_type,
                       posts.quantity,
                       posts.description
                FROM posts
                INNER JOIN sellers ON posts.seller_id = sellers.seller_id
                INNER JOIN all_types ON posts.type = all_types.type_id
                WHERE posts.obj_id = ?
                """,
                [post_id],
            )
            row = cur.fetchone()

            if row is None:
                abort(404)

            owner_id = str(row[0])
            if str(current_user.get_id()) != owner_id and not current_user.is_admin:
                abort(403)

            cur.execute("SELECT event_name, date FROM auction_info")
            auction_info = cur.fetchone()
            if auction_info is None:
                abort(500)

            cur.execute("SELECT label_type, border FROM label_type")
            label_setup = cur.fetchone()

        label_type = zlabels.ZLabels.without_margins_24
        border = "no"
        if label_setup is not None:
            label_type = label_setup[0]
            border = label_setup[1]

        label_generator = zlabels.ZLabels(
            "preview",
            auction_info[0],
            auction_info[1],
            label_type,
            border,
        )
        seller = [row[0], row[1], row[2], row[3]]
        post = [
            row[4],
            row[5],
            row[6],
            row[7],
            row[8],
            row[9],
            row[10],
            row[11],
        ]

        png = make_label_preview_png(label_generator, seller, post)
        response = Response(png, mimetype="image/png")
        response.headers["Cache-Control"] = "no-store"
        return response
