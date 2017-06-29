# coding=utf-8
from reportlab.platypus import PageBreak
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import red, blueviolet, yellowgreen, lawngreen, black, grey, lightgrey
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle

from PdfLine import LeftLine, CenterLine


class MakeWallList(object):

    def __init__(self, hosting_association, event_name, event_date, event_city):
        """
        Generates a pdf with all posts that are to be sold on auction.
        This list could be displayed to event visitors so they can see the final list of posts.
        :param hosting_association: Organising club name
        :param event_name: Name of the event
        :param event_date: Date for the event
        :param event_city: Name of location for event
        """
        self.hosting_association = hosting_association
        self.event_name = event_name
        self.event_date = event_date
        self.event_city = event_city

        self.paper_width, self.paper_height = A4

    def make_pdf(self, auction_data):
        """
        Generate the pdf
        :param auction_data: list of lists with 4 posts.
        [[objid, scientific name, popular name, reserved price],
        [objid, scientific name, popular name, reserved price],
        [objid, scientific name, popular name, reserved price]]
        :return: a pdf
        """
        import cStringIO
        output = cStringIO.StringIO()
        styles = getSampleStyleSheet()
        doc = SimpleDocTemplate(output, pagesize=A4, topMargin=15 * mm, bottomMargin=20 * mm)
        # doc = BaseDocTemplate("pdf_file", showBoundary=1, leftMargin=0, rightMargin=0, topMargin=0, bottomMargin=0, pagesize=A4)

        story = []
        normal = styles["Normal"]
        h1 = styles["h1"]
        h2 = styles["h2"]
        h3 = styles["h3"]
        title = styles["title"]

        # Make a right aligned paragraph style
        styles.add(ParagraphStyle(name='RightAlign', alignment=TA_RIGHT))
        normal_right = styles['RightAlign']
        # Make a centered paragraph style
        styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
        normal_center = styles['Center']

        p = Paragraph("Anmälda auktionsposter", title)
        story.append(p)
        p = Paragraph("{} - {}".format(self.event_name, self.event_date), title)
        story.append(p)

        t = Table(auction_data, colWidths=(13 * mm, 80 * mm, 80 * mm, 18 * mm), repeatRows=1)  # column width
        # t.setStyle(TableStyle([
        #                        # ('BACKGROUND', (0, 0), (0, -1), blueviolet),
        #                        # ('BACKGROUND', (1, 0), (1, -1), yellowgreen),
        #                        # ('BACKGROUND', (2, 0), (2, -1), blueviolet),
        #                        # ('BACKGROUND', (3, 0), (3, -1), yellowgreen),
        #                        ]))
        t.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, grey),
                               ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
                               ('ROWBACKGROUNDS', (0, 0), (-1, -1), (lightgrey, None)),
                               # ('BACKGROUND', (0, 0), (-1, 0), blueviolet)
                              ]))

        story.append(t)
        story.append(PageBreak())

        doc.build(story)

        pdf_out = output.getvalue()

        output.close()
        return pdf_out

if __name__ == "__main__":
    import sqlite3
    conn = sqlite3.connect("auktion.db3")

    with conn:
        cur = conn.cursor()
        sql = """Select posts.obj_id, posts.scientific_name, posts.plain_name, posts.minimum_price from posts
                 join types on types.type_id=posts.type
                 where types.sale_type='auction' """
        cur.execute(sql)
        my_data = cur.fetchall()

        C = MakeWallList("Uppsala akvarieförening", "Uppsala storauktion", "2016-11-27", "Uppsala")

        pdf = C.make_pdf(my_data)
        pdf_temp = "temp_pdf.pdf"
        f = open(pdf_temp, "w")
        f.write(pdf)
        f.close()