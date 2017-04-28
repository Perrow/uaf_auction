# coding=utf-8
from reportlab.platypus import PageBreak
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import red, blueviolet, yellowgreen, lawngreen, black
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle

from PdfLine import LeftLine, CenterLine

class Compilation(object):

    def __init__(self, hosting_association, event_name, event_date, event_city, commision):
        """
        :param hosting_association: Organising club name
        :param event_name: Name of the event
        :param event_date: Date for the event
        :param event_city: Name of location for event
        :param commision: Commision the club takes
        """
        self.hosting_association = hosting_association
        self.event_name = event_name
        self.event_date = event_date
        self.event_city = event_city
        self.commision = commision
        self.paper_width, self.paper_height = A4


    def make_pdf(self, compilation_data):
        import cStringIO
        output = cStringIO.StringIO()
        styles = getSampleStyleSheet()
        doc = SimpleDocTemplate(output)
        story = [Spacer(1, 25 * mm)]
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

        for seller in compilation_data:
            seller_id = seller[0]
            seller_name = seller[1]
            p = Paragraph(self.event_name, title)
            story.append(p)
            p = Paragraph(self.event_date, title)
            story.append(p)
            story.append(Spacer(1, 10 * mm))
            p = Paragraph("Sammanställning för {}".format(seller_name), h2)
            story.append(p)
            p = Paragraph("Inlämningsnummer {}".format(seller_id), h3)
            story.append(p)

            data = seller[3]

            print(data)

            # # Table
            # data = [['Post', 'Typ', 'Namn', 'Pris', 'Såld'],
            #         ['10', '', 'Tigerbarb', '30', 'Auktion'],
            #         ['11', '', 'Platy', '20', 'Auktion'],
            #         ['12', 'växt', 'Anubias', '50', 'Loppis']]
            t = Table(data, colWidths=(10 * mm, 50 * mm, 80 * mm, 15 * mm, 25 * mm))  # column width
            t.setStyle(TableStyle([
                ("LINEBELOW", (0, 0), (-1, 0), 1, black)
                # (start cell x, y), slut cell x, y) räknat med 0,0 i övre vänstra hörnet på tabellen. (-1,-1) är nedre högra hörnet
                # ("GRID", (0, 0), (-1, -1), 0.5, lawngreen)
            ]))
            story.append(t)

            tot_sum = seller[2]
            to_society = tot_sum * self.commision
            to_society = int(to_society + 0.5)
            to_seller = int(tot_sum - to_society)
            print(tot_sum, to_society, to_seller)

            data2 = [['', '', '', 'summa', int(tot_sum)],
                     ['', '', '', 'provision', to_society],
                     ['', '', '', 'till säljaren', to_seller]]
            t2 = Table(data2, colWidths=(20 * mm, 20 * mm, 90 * mm, 20 * mm, 30 * mm))  # column width
            t2.setStyle(TableStyle([("LINEABOVE", (0, 0), (4, 0), 1, black),
                                    ("LINEBELOW", (3, 2), (4, 2), 1, black),
                                    ('ALIGN', (3, 0), (3, 2), "RIGHT"),
                                    ('ALIGN', (4, 0), (4, 2), "RIGHT")]))
            # t2.setStyle(TableStyle([('BACKGROUND', (3, 0), (3, 2), blueviolet),
            #                         ('BACKGROUND', (4, 0), (4, 2), yellowgreen)]))

            story.append(t2)

            story.append(PageBreak())

            p = Paragraph(self.event_name, title)
            story.append(p)
            p = Paragraph(self.event_date, title)
            story.append(p)
            p = Paragraph("Kvittens", title)
            story.append(p)
            story.append(Spacer(1, 10 * mm))
            p = Paragraph("Av {} har jag mottagit kr {} utgörande ersättning för inlämnade och försålda poster.".format(self.hosting_association, to_seller), normal)
            story.append(p)
            story.append(Spacer(1, 10 * mm))
            p = Paragraph(u"{} {}".format(self.event_city, self.event_date), normal_center)
            story.append(p)
            story.append(Spacer(1, 20 * mm))
            line = CenterLine(200, doc.width / 2)
            story.append(line)
            p = Paragraph(u"{}".format(seller_name), normal_center)
            story.append(p)

            story.append(PageBreak())

        doc.build(story) #, onFirstPage=self.my_first_page) #, onLaterPages=my_later_pages)

        pdf_out = output.getvalue()
        output.close()
        return pdf_out

if __name__ == "__main__":
    my_data = [
    [1, u'Kristian Persson', 160.0, [
        [1, u'1', u'Afrikansk bandbarb', u'', u'fasta bordet'],
        [3, u'1', u'Neontetra', 60.0, u'auction'],
        [5, u'1', u'Vinkeltetra', 30.0, u'auction'],
        [11, u'8', u'Pump', 70.0, u'fasta bordet']]
    ],
    [2, u'Olle Karlsson', 240.0, [
        [2, u'1', u'Kuhlii-\xe5l', 50.0, u'auction'],
        [4, u'1', u'Odessabarb', 40.0, u'auction'],
        [7, u'1', u'Skalar', 30.0, u'auction'],
        [12, u'8', u'Ledramp', 100.0, u'fasta bordet'],
        [13, u'10', u'Vattenpest', 20.0, u'fasta bordet']]
    ],
    [4, u'Pia Larsson', 80.0, [
        [6, u'1', u'Kilfl\xe4cksrasbora', 80.0, u'auction']]
    ]
]

    C = Compilation("test.pdf", "Uppsala storauktion", "2016-11-27", 0.15)
    C.make_pdf(my_data)