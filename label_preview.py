# coding=utf-8

"""Generate high-fidelity PNG previews from the existing label PDF renderer."""


def make_label_preview_png(label_generator, seller, post, dpi=200):
    """Render one auction post as a PNG label preview.

    The preview deliberately uses ``ZLabels.make_pdf`` instead of maintaining a
    second label layout.  A temporary one-label PDF is generated with the same
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
