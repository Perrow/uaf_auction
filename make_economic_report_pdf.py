# coding=utf-8
from reportlab.platypus import PageBreak
from reportlab.graphics import shapes
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import red, blueviolet, yellowgreen, lawngreen, black, grey
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle

from PdfLine import LeftLine, CenterLine


class EconomicReport(object):

    def __init__(self, event_name, club_name, club_short_name, event_date, event_city):
        """
        Class for generating labels in the size 70*37 mm in a 3 by 8 grid on A4 paper
        :param event_name: Name of the event
        :param club_name: Name of hosting club
        :param club_short_name: Short form of the hosting club name
        :param event_date: Date for the event
        :param event_city: location of the event
        """
        self.event_name = event_name
        self.club_name = club_name
        self.club_short_name = club_short_name
        self.event_date = event_date
        self.event_city = event_city

        self.paper_width, self.paper_height = A4
        self.font_size = 12  # Reprotlab default
        self.font = 'Helvetica'  # Reprotlab default
        self.debug = False  # Turns on colored tablecells

    def truncate_str(self, text, length):
        """
        Caluculates the length of a string when rendered with the font and size for the label and truncates it to fit in a given length
        :param text: text string to truncate
        :param length: max length of string
        :return: truncated string
        """
        truncated = False
        name_width = shapes.stringWidth(text, self.font, self.font_size)
        while name_width > length:
            text = text[:-1]
            name_width = shapes.stringWidth(text, self.font, self.font_size)
            truncated = True
        if truncated:
            return text + "..."
        else:
            return text

    def make_pdf(self, data, tot_data):
        """
        Generate pdf with the data in the data argument
        :param tot_data: data for the total result of the auction
        :param data: data for each individual seller
        :return: a pdf document
        """
        #import cStringIO
        #output = cStringIO.StringIO()
        from io import BytesIO
        output = BytesIO()
        doc = SimpleDocTemplate(output)

        # Set up styles
        styles = getSampleStyleSheet()
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

        # Start document
        story = [Spacer(1, 25 * mm)]

        # Start page
        p = Paragraph(u"Ekonomisk sammanställning", title)
        story.append(p)
        p = Paragraph(self.event_name, title)
        story.append(p)
        p = Paragraph(self.event_date, title)
        story.append(p)
        line = LeftLine(doc.width)
        # story.append(line)
        story.append(Spacer(1, 10 * mm))

        # *** Result per seller *** #

        for seller in data:
            # [seller_id, seller_name, club, tot_sold, to_society, to_seller, tot_posts, count_sold, sold_stat_data]
            seller_id = seller[0]
            seller_name = seller[1]
            club = seller[2]
            tot_sold = seller[3]
            to_society = seller[4]
            to_seller = seller[5]
            tot_posts = seller[6]
            count_sold = seller[7]
            data2 = seller[8]

            data1 = [['Säljare nr:', seller_id, self.truncate_str(seller_name, 60 * mm), self.truncate_str(club, 70 * mm), ""]]

            t1 = Table(data1, colWidths=(20 * mm, 10 * mm, 60 * mm, 70 * mm, doc.width - (20 + 10 + 60 + 70)*mm))  # column width
            t1.setStyle(TableStyle([("LINEABOVE", (0, 0), (4, 0), 1, black),
                                    ("LINEBELOW", (0, -1), (4, -1), 0.5, black),
                                    ('ALIGN', (0, 0), (0, 0), "RIGHT"),
                                    ('ALIGN', (1, 0), (1, 0), "LEFT")
                                    ]))
            if self.debug:
                t1.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, -1), grey),
                                    ('BACKGROUND', (1, 0), (1, -1), blueviolet),
                                    ('BACKGROUND', (2, 0), (2, -1), yellowgreen),
                                    ('BACKGROUND', (3, 0), (3, -1), lawngreen),
                                    ]))
            # t1.setStyle(TableStyle([('BACKGROUND', (0, 0), (4, 2), grey)]))
            story.append(t1)
            print(doc.width)
            t2 = Table(data2, colWidths=(60 * mm, 30 * mm, 70*mm, doc.width - (60 + 30 + 70)*mm ))  # column width
            if self.debug:
                t2.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, -1), grey),
                                    ('BACKGROUND', (1, 0), (1, -1), blueviolet),
                                    ('BACKGROUND', (2, 0), (2, -1), yellowgreen),
                                    ('BACKGROUND', (3, 0), (3, -1), lawngreen),
                                    ]))

            story.append(t2)

            data3 = [['Sålt:', tot_sold, 'Avgår provision:', to_society, 'Netto:', to_seller, ""],
                     ['Inlämnade poster:', tot_posts, 'Sålda poster:', count_sold, 'Osålda poster:', tot_posts - count_sold, ""]]
            t3 = Table(data3, colWidths=(30 * mm, 20 * mm, 30 * mm, 20 * mm, 30 * mm, 20 * mm,  doc.width - (30 + 20 + 30 + 20 + 30 + 20)*mm ))  # column width
            t3.setStyle(TableStyle([('ALIGN', (0, 0), (0, 1), "RIGHT"),
                                    ('ALIGN', (2, 0), (2, 1), "RIGHT"),
                                    ('ALIGN', (4, 0), (4, 1), "RIGHT"),
                                    ]))
            t3.setStyle(TableStyle([("LINEABOVE", (0, 0), (6, 0), 0.5, black),
                                    ("LINEBELOW", (0, -1), (6, -1), 1, black)
                                    # ('BACKGROUND', (0, 0), (0, 1), grey),
                                    # ('BACKGROUND', (1, 0), (1, 1), blueviolet),
                                    # ('BACKGROUND', (2, 0), (2, 1), yellowgreen),
                                    # ('BACKGROUND', (3, 0), (3, 1), lawngreen),
                                    # ('BACKGROUND', (4, 0), (4, 1), yellowgreen),
                                    # ('BACKGROUND', (5, 0), (5, 1), lawngreen),
                                    # ('BACKGROUND', (6, 0), (6, 1), yellowgreen),
                                    ]))
            story.append(t3)
            story.append(Spacer(1, 10 * mm))

        # *** Total result *** #

        p = Paragraph(u"Totalt resultat", title)
        story.append(p)

        data5 = tot_data[5]
        t5 = Table(data5, colWidths=(40 * mm, 40 * mm, 40 * mm,  doc.width - (40 + 40 + 40)*mm ))
        t5.setStyle(TableStyle([("LINEABOVE", (0, 0), (3, 0), 1, black),
                                ("LINEBELOW", (0, -1), (3, -1), 0.5, black)
                                # ('BACKGROUND', (0, 0), (0, -1), grey),
        #                         ('BACKGROUND', (1, 0), (1, -1), blueviolet),
        #                         ('BACKGROUND', (2, 0), (2, -1), yellowgreen),
        #                         ('BACKGROUND', (3, 0), (3, -1), lawngreen),
                                ]))
        story.append(t5)

        data4 = [["Total försäljningssumma", tot_data[0], "Avgår provision", tot_data[1], "Netto", tot_data[2]],
                 ["Antal inlämnade poster", tot_data[3], "Antal sålda", tot_data[4], "Antal osålda", tot_data[3] - tot_data[4]]]
        t4 = Table(data4, colWidths=(45 * mm, 20 * mm, 30 * mm, 20 * mm, 30 * mm, doc.width - (45+20+30+20+30)*mm))
        t4.setStyle(TableStyle([("LINEABOVE", (0, 0), (6, 0), 0.5, black),
                                ("LINEBELOW", (0, -1), (6, -1), 1, black)
        #                         ('BACKGROUND', (0, 0), (0, 1), grey),
        #                         ('BACKGROUND', (1, 0), (1, 1), blueviolet),
        #                         ('BACKGROUND', (2, 0), (2, 1), yellowgreen),
        #                         ('BACKGROUND', (3, 0), (3, 1), lawngreen),
        #                         ('BACKGROUND', (4, 0), (4, 1), yellowgreen),
        #                         ('BACKGROUND', (5, 0), (5, 1), lawngreen),
        #                         # ('BACKGROUND', (6, 0), (6, 1), yellowgreen),
                                ]))
        story.append(t4)

        # data6 = [["Antal inlämnade poster", tot_data[3], "Antal sålda poster", tot_data[4], "Antal osålda poster", tot_data[3] - tot_data[4]]]
        # t6 = Table(data6, colWidths=(30 * mm, 20 * mm, 30 * mm, 20 * mm, 30 * mm, doc.width - (30 + 20 + 30 + 20 + 30 + 20)*mm))
        # story.append(t6)


        doc.build(story) #, onFirstPage=self.my_first_page) #, onLaterPages=my_later_pages)

        pdf_out = output.getvalue()
        output.close()
        return pdf_out

