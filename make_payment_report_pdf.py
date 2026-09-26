# coding=utf-8

"""PDF report for flea-market payments."""

from io import BytesIO
from decimal import Decimal, InvalidOperation

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class PaymentReport(object):
    def __init__(self, event_name, event_date):
        self.event_name = event_name
        self.event_date = event_date

    @staticmethod
    def _format_amount(value):
        try:
            amount = Decimal(str(value)).quantize(Decimal('0.01'))
            return '{} kr'.format(format(amount, '.2f').replace('.', ','))
        except (InvalidOperation, ValueError):
            return '{} kr'.format(value)

    def make_pdf(self, payments):
        output = BytesIO()
        doc = SimpleDocTemplate(
            output,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        styles = getSampleStyleSheet()
        story = [Paragraph('Betalningar', styles['Title'])]
        if self.event_name:
            story.append(Paragraph(str(self.event_name), styles['Heading2']))
        if self.event_date:
            story.append(Paragraph(str(self.event_date), styles['Normal']))
        story.append(Spacer(1, 8 * mm))

        data = [['Referens', 'Belopp', 'Godkänd']]
        for reference, amount, confirmed_at in payments:
            data.append([
                str(reference),
                self._format_amount(amount),
                confirmed_at if confirmed_at else 'Ej godkänd',
            ])

        if len(data) == 1:
            data.append(['-', '-', 'Inga betalningar'])

        table = Table(
            data,
            colWidths=(45 * mm, 40 * mm, doc.width - 85 * mm),
            repeatRows=1,
        )
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.whitesmoke]),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(table)

        doc.build(story)
        pdf = output.getvalue()
        output.close()
        return pdf
