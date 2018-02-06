# coding=utf-8

import math

from reportlab.graphics import shapes
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm


class ZLabels(object):
    def __init__(self, pdf_name, event_name, event_date):
        """
        Class for generating labels in the size 70*37 mm in a 3 by 8 grid on A4 paper
        :param pdf_name: Name of pdf file without extension
        :param event_name: Name of the event
        :param event_date: Date for the event
        """
        self.event_name = event_name
        self.event_date = event_date
        self.pdf_name = pdf_name
        self.paper_width, self.paper_height = A4
        self.label_width = mm * 70  # mm
        self.label_height = mm * 37  # mm
        self.label_columns = int(self.paper_width / self.label_width)  # nr of columns
        self.label_rows = int(self.paper_height / self.label_height)  # nr of rows

        self.font_size = 9
        self.font = 'Helvetica'
        self.row_height = mm * 4
        print(self.label_columns, self.label_rows, self.paper_height)

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
            name_width = shapes.stringWidth(text + "...", self.font, self.font_size)
            truncated = True
        if truncated:
            return text + "..."
        else:
            return text

    def make_pdf(self, data, border=True):
        """
        Make the label pdf
        :param data: the data to generate labels from
        :param border: Draw border around labels or not
        """

        # import cStringIO
        # output = cStringIO.StringIO()
        from io import BytesIO
        output = BytesIO()
        canvas = Canvas(output)
        canvas.setLineWidth(.3)
        canvas.setTitle("Labels")
        canvas.setAuthor(self.event_name)

        start_y = self.paper_height
        left_margin = 20

        saved = False
        count = 0
        # Loop over sellers in data
        for seller in data:

            saved = False
            seller_id = seller[0]
            seller_name = seller[1]
            seller_phone = seller[2]
            seller_society = seller[3]
            # Loop over the sellers items
            for post in seller[4]:
                post_id = post[0]
                pop_name = post[1]
                sci_name = post[2]
                post_fixed_price = post[3]
                post_min_price = post[4]
                post_type = post[5]
                post_quantity_description = "{},{}".format(post[6], post[7]).strip(",")

                # 24 labels on a sheet, if more start a new sheet
                if count >= 24:
                    canvas.showPage()
                    count = 0
                column = count % 3
                row = math.floor(count / 3)

                x = column * self.label_width
                y = start_y - row * self.label_height

                # Border
                if border:
                    canvas.line(x, y, x + self.label_width, y)  # upper line
                    canvas.line(x + self.label_width, y, x + self.label_width, y - self.label_height)  # right line
                    canvas.line(x, y - self.label_height, x + self.label_width, y - self.label_height)  # bottom line
                    canvas.line(x, y - self.label_height, x, y)  # Left line

                # Add logo
                canvas.drawInlineImage("static/img/logo_64.jpg", x + left_margin, y - self.row_height * 3, 20, 20)                # Logo image

                canvas.setFont(self.font, self.font_size)
                canvas.drawString(x + left_margin + 25, y - self.row_height * 2, self.event_name)                                 # Event name
                str_width = shapes.stringWidth(self.event_date, self.font, self.font_size)
                canvas.drawString(x + self.label_width - str_width - left_margin, y - self.row_height * 2, self.event_date)       # Event date

                canvas.setFont(self.font, 25)
                str_width = shapes.stringWidth(str(post_id), self.font, 25)
                canvas.drawString(x + self.label_width - str_width - left_margin, y - self.row_height * 4, str(post_id))          # Post id

                canvas.setFont(self.font, self.font_size)
                canvas.drawString(x + left_margin, y - self.row_height * 4, "{}".format(self.truncate_str("{}: {}".format(seller_id, seller_name), 40 * mm)))  # Seller Name
                canvas.drawString(x + left_margin + 25, y - self.row_height * 3, self.truncate_str(seller_society, 30 * mm))      # Seller society
                canvas.drawString(x + left_margin, y - self.row_height * 5, "Tel: {}".format(seller_phone))                       # Seller phone number
                if post_type == "fixed_price":
                    msg = u"Fastpris: "
                    if post_fixed_price is not None:
                        if len(str(post_fixed_price)) > 0:
                            msg += "{} kr".format(post_fixed_price)
                    str_width = shapes.stringWidth(msg, self.font, self.font_size)
                    canvas.drawString(x + self.label_width - str_width - left_margin, y - self.row_height * 5, msg)               # Fleamarket price
                if post_type == "auction":
                    msg = u"Auktion"
                    if post_min_price is not None:
                        if len(str(post_min_price)) > 0:
                            msg += ": {} kr".format(post_min_price)
                    str_width = shapes.stringWidth(msg, self.font, self.font_size)
                    canvas.drawString(x + self.label_width - str_width - left_margin, y - self.row_height * 5, msg)               # Auction price

                canvas.drawString(x + left_margin, y - self.row_height * 6, "{}".format(self.truncate_str(sci_name, 150)))        # Scientific name
                canvas.drawString(x + left_margin, y - self.row_height * 7, "{}".format(self.truncate_str(pop_name, 150)))        # Popular name
                canvas.drawString(x + left_margin, y - self.row_height * 8, "{}".format(self.truncate_str(post_quantity_description, 55 * mm)))  # Quantity and description
                count += 1

            # if new seller add an empty row and empty labels on current row
            tot_row = math.floor(count / 3)
            column = count % 3
            if column > 0:  # one or two labels on current row add to rows to make an empty row
                tot_row += 2
            else:
                tot_row += 1  # three labels on current row only add one empty row
            count = tot_row * 3

        if not saved:
            canvas.save()
            pdf_out = output.getvalue()
            output.close()
            return pdf_out


if __name__ == "__main__":
    MK = ZLabels("test", "Uppsala Storauktion", "2016-11-27")
    test_data = [[1, u'Kristian Persson', u'0733-505932', u'UAF',
                  [[1, u'Afrikansk bandbarb Barbus fasciolatus', u'5', None], [3, u'Neontetra Paracheirodon innesi', u'10', None], [5, u'Vinkeltetra Thayeria boehlkei', u'5', None], [9, u'Guppy Poecilia reticulata', u'25', None],
                   [10, u'Tigerbarb Puntigrus tetrazona', u'5', None], [11, u'Pump ', u'1', 70.0]]], [2, u'Olle Karlsson', u'0730-421587', u'\xd6rebro',
                                                                                                      [[2, u'Kuhlii-\xe5l Pangio kuhlii', u'4', None], [4, u'Odessabarb Pethia padamya', u'5', None], [7, u'Skalar Pterophyllum scalare', u'5', None],
                                                                                                       [12, u'Ledramp ', u'1', 100.0], [13, u'Vattenpest Egeria densa', u'5', 20.0]]],
                 [3, u'Lena Svensson', u'0733-954321', u'Haninge AF', [[8, u'Kilfl\xe4cksrasbora Trigonostigma heteromorpha', u'7', None]]],
                 [4, u'Pia Larsson', u'0733-987632', u'Malm\xf6 AF', [[6, u'Kilfl\xe4cksrasbora Trigonostigma heteromorpha', u'3', None]]]]

    MK.make_pdf(test_data)
