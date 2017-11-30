# coding=utf-8
import time

from reportlab.platypus import PageBreak
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import red, blueviolet, yellowgreen, lawngreen, black
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle

from PdfLine import LeftLine, CenterLine


class make_clerk_receipt_pdf(object):

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
        story = []
        story.append(im)
        p = Paragraph(u"Kassör-kvitto", title)
        story.append(p)
        p = Paragraph(self.event_name, title)
        story.append(p)
        p = Paragraph(self.event_date, title)
        story.append(p)
        line = LeftLine(doc.width)
        story.append(line)
        story.append(Spacer(1, 10 * mm))
        print(data)
        p = Paragraph(u"{} har hanterat försälning av poster för {} på fastabordet.".format(data[0], data[1]), normal)
        story.append(p)
        story.append(Spacer(1, 10 * mm))
        p = Paragraph(u"{}".format(time.strftime("%Y-%m-%d %H:%M:%S")), normal)
        story.append(p)
        
        doc.build(story) #, onFirstPage=self.my_first_page) #, onLaterPages=my_later_pages)

        pdf_out = output.getvalue()
        output.close()
        return pdf_out

