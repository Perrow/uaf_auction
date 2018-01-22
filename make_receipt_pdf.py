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


class Receipt(object):

    def __init__(self, event_name, Association, Association_short_name, event_date, event_city ):
        """
        Class for generating labels in the size 70*37 mm in a 3 by 8 grid on A4 paper
        :param event_name: Name of the event
        :param Association: Name of hosting association
        :param Association_short_name: Short form of the hosting associations name
        :param event_date: Date for the event
        :param event_city: location of the event
        """
        self.event_name = event_name
        self.Association = Association
        self.Association_short_name = Association_short_name
        self.event_date = event_date
        self.event_city = event_city

        self.paper_width, self.paper_height = A4

    def make_pdf(self, data):
        """
        Generate pdf with the data in the data argument
        :param data: data to render in the pdf
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

        logo = "static/img/logo_for_pdf.jpg"
        im = Image(logo, 30 * mm, 30 * mm)
        im.hAlign = "LEFT"
        #Start document
        # story = [Spacer(1, 25 * mm)]
        story = []


        for seller in data:
            seller_id = seller[0]
            seller_name = seller[1]
            seller_association = seller[2]
            seller_phone = seller[3]
            nr_posts = seller[4]
            # posts = ", ".join(map(str, seller[5]))
            posts = seller[5]
            data2 = [[u'Inlämningsnummer:', str(seller_id[0])],
                     [u'Namn:', seller_name],
                     [u'Förening:', seller_association],
                     [u'Telefon:', seller_phone],
                     [u'Antal poster:', str(nr_posts)],
                     [u'Nummer', str(posts)]
                     ]

            # Start page 1 sellers receipt

            story.append(im)
            p = Paragraph(u"Inlämningskvitto", title)
            story.append(p)
            p = Paragraph(self.event_name, title)
            story.append(p)
            p = Paragraph(self.event_date, title)
            story.append(p)
            line = LeftLine(doc.width)
            story.append(line)
            story.append(Spacer(1, 10 * mm))

            t2 = Table(data2) #, colWidths=(20 * mm, 20 * mm, 100 * mm, 20 * mm, 20 * mm))  # column width
            t2.setStyle(TableStyle([('ALIGN', (0, 0), (0, 5), "RIGHT")]))
            story.append(t2)
            story.append(Spacer(1, 10 * mm))

            p = Paragraph(u"Spara detta inlämningskvitto. Du måste kunna visa upp det för att få ut dina pengar efter auktionens slut.", normal)
            story.append(p)

            story.append(PageBreak())

            # Start page 2 association receipt
            story.append(im)
            p = Paragraph(u"{}:s kopia".format(self.Association_short_name), normal_right)
            story.append(p)
            story.append(Spacer(1, 10 * mm))
            p = Paragraph(u"Inlämningskvitto", title)
            story.append(p)
            p = Paragraph(self.event_name, title)
            story.append(p)
            p = Paragraph(self.event_date, title)
            story.append(p)
            line = LeftLine(doc.width)
            story.append(line)
            story.append(Spacer(1, 10 * mm))

            t2 = Table(data2) #, colWidths=(20 * mm, 20 * mm, 100 * mm, 20 * mm, 20 * mm))  # column width
            t2.setStyle(TableStyle([('ALIGN', (0, 0), (0, 5), "RIGHT")]))
            story.append(t2)
            story.append(Spacer(1, 10 * mm))

            p = Paragraph(u"Med min underskrift nedan erkänner jag som säljare fullt ansvar för att inlämnade djur och växter är de jag har angett och att de är i god kondition. Jag är ansvarig för att  tillbehör är i det skick som anges och jag har angett de brister som inte omedelbart framgår.", normal)
            story.append(p)
            story.append(Spacer(1, 10 * mm))
            p = Paragraph(u"Om köparen upptäcker att oärlighet i ovanstående har skett riktas ersättningskrav mot säljaren och inte mot förmedlaren {}. {} är efter förmåga behjälpliga vid oenighet.".format(self.Association, self.Association), normal)
            story.append(p)

            story.append(Spacer(1, 10 * mm))
            p = Paragraph(u"Undertecknad accepterar ovanstående.", normal)
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
    test_data = [
    [1, u'Kristian Persson', u'UAF', u'0123-456789', 7, "1, 2, 47, 48, 49, 50-51"],
    [2, u'Olle Karlsson', u'Haninge', u'0258-468751', 5, "3, 4, 5, 6, 7"],

    [4, u'Pia Larsson', u'Malmö', u'06543-987654', 3, "8, 9, 10"]
    ]


    C = Receipt("Uppsala storauktion", "Uppsala Akvarieförening", "UAF", "2016-11-27", "Uppsala")
    C.make_pdf(test_data)