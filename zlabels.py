# coding=utf-8

import math
import os
import sqlite3

from flask import after_this_request, current_app, has_request_context, request
from reportlab.graphics import shapes
from reportlab.graphics.barcode import code128
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm


class ZLabels(object):

    with_margins_24 = "with_margins_24"  # 24 labels with margin around, and between label columns, labels ~ 64 * 34 mm
    with_margins_24_typ_2 = "with_margins_24_typ_2"  # 24 labels with margins around not between label columns, labels ~ 65 * 34 mm
    without_margins_24 = "without_margins_24"  # 24 labels without margins, labels 70 * 37 mm, but printers can not print all the way to the edge but leave ca 5 mm
    with_top_margin_24 = "with_topmargin_24"  # 24 labels wit top and bottom marging, labels 70 * 36 mm, but printers can not print all the way to the edge but leave ca 5 mm

    def __init__(self, pdf_name, event_name, event_date, label_type, border):
        """
        Class for generating labels in the size 70*37 mm in a 3 by 8 grid on A4 paper
        :param pdf_name: Name of pdf file without extension
        :param event_name: Name of the event
        :param event_date: Date for the event
        """
        self.event_name = event_name
        self.event_date = event_date
        self.pdf_name = pdf_name
        self.label_type = label_type
        self.border = border

        # Label setup
        # https://www.officedepot.se/ecommerce/sortiment/etiketter--markning-c2477/etiketter-till-skrivare-c2431/etikett-l4773-63-5x33-9-480-fp-5922080/
        self.paper_width, self.paper_height = A4

        if label_type == ZLabels.with_margins_24:
            self.label_width = mm * 64  # mm
            self.label_height = mm * 33.9  # mm
            self.paper_left_right_margin = mm * 7  # mm
            self.paper_top_bottom_margin = mm * 12  # mm
            self.label_spacing = mm * 2.5  # mm
            self.printer_margin = mm * 0  # mm Not used if paper has enough margins round the labels
            self.label_columns = int(self.paper_width / self.label_width)  # nr of columns
            self.label_rows = int(self.paper_height / self.label_height)  # nr of rows
            self.left_margin = 13 * mm
            self.font_size = 9
            self.font = 'Helvetica'
            self.bold_font = 'Helvetica-Bold'
            self.row_height = mm * 4
            self.text_width = self.label_width - self.left_margin - 1.5 * mm - 1.5 * mm  # label width - left margin - left text margin - right text margin

        elif label_type == ZLabels.with_margins_24_typ_2:
            self.label_width = mm * 64.6  # mm
            self.label_height = mm * 33.8  # mm
            self.paper_left_right_margin = mm * 8  # mm
            self.paper_top_bottom_margin = mm * 13  # mm
            self.label_spacing = mm * 0  # mm
            self.printer_margin = mm * 0  # mm Not used if paper has enough margins round the labels
            self.label_columns = int(self.paper_width / self.label_width)  # nr of columns
            self.label_rows = int(self.paper_height / self.label_height)  # nr of rows
            self.left_margin = 13 * mm
            self.font_size = 9
            self.font = 'Helvetica'
            self.bold_font = 'Helvetica-Bold'
            self.row_height = mm * 4
            self.text_width = self.label_width - self.left_margin - 1.5 * mm - 1.5 * mm  # label width - left margin - left text margin - right text margin
            print("text width", self.text_width)

        elif label_type == ZLabels.without_margins_24:
            self.label_width = mm * 70  # mm
            self.label_height = mm * 37  # mm
            self.paper_left_right_margin = mm * 0  # mm
            self.paper_top_bottom_margin = mm * 0  # mm
            self.label_spacing = mm * 0  # mm
            self.printer_margin = mm * 5  # mm
            self.label_columns = int(self.paper_width / self.label_width)  # nr of columns
            self.label_rows = int(self.paper_height / self.label_height)  # nr of rows
            self.left_margin = 13 * mm
            self.font_size = 9
            self.font = 'Helvetica'
            self.bold_font = 'Helvetica-Bold'
            self.row_height = mm * 3.5
            self.text_width = mm * 45

        elif label_type == ZLabels.with_top_margin_24:
            self.label_width = mm * 70  # mm
            self.label_height = mm * 36  # mm
            self.paper_left_right_margin = mm * 0  # mm
            self.paper_top_bottom_margin = mm * 5  # mm
            self.label_spacing = mm * 0  # mm
            self.printer_margin = mm * 5  # mm
            self.label_columns = int(self.paper_width / self.label_width)  # nr of columns
            self.label_rows = int(self.paper_height / self.label_height)  # nr of rows
            self.left_margin = 13 * mm
            self.font_size = 9
            self.font = 'Helvetica'
            self.bold_font = 'Helvetica-Bold'
            self.row_height = mm * 3.5
            self.text_width = mm * 45

        print(self.label_columns, self.label_rows, self.paper_height / mm)

    @staticmethod
    def _post_ids(data):
        post_ids = []
        for seller in data:
            for post in seller[4]:
                try:
                    post_ids.append(int(post[0]))
                except (TypeError, ValueError):
                    pass
        return post_ids

    @staticmethod
    def _handle_label_download_request(data):
        """Expose the highest label id and handle explicit mark-as-printed requests."""
        if not has_request_context():
            return False

        post_ids = ZLabels._post_ids(data)
        if post_ids:
            max_post_id = max(post_ids)

            @after_this_request
            def add_label_metadata(response):
                response.headers['X-Label-Max-Id'] = str(max_post_id)
                return response

        mark_printed_through = request.args.get('mark_printed_through')
        if mark_printed_through is None:
            return False

        try:
            max_post_id = int(mark_printed_through)
        except (TypeError, ValueError):
            return True

        conn = sqlite3.connect(current_app.config['DATABASE'])
        with conn:
            cur = conn.cursor()
            cur.execute("UPDATE posts SET label_printed='yes' WHERE obj_id <= ?", [max_post_id])
            conn.commit()

        return True

    def make_multiline(self, text, max_length, font, font_size):
        """
        Takes a line of text and constructs a list of line fragments where each fragment do not exceed the maximum length of a line
        :param text: Text to split into lines
        :param max_length: max length of a line
        :param font: font name
        :param font_size: font size
        :return: list of strings
        """
        if text is None:
            return [""]
        parts = text.split(" ")
        lines = []  # Resulting list of lines
        line = []  # current line
        for word in parts:
            # Test width of line including spaces
            tmp_line = line.copy()
            tmp_line.append(word)
            tmp_line = " ".join(tmp_line)
            total_width = shapes.stringWidth(tmp_line, font, font_size)
            if total_width < max_length:
                line.append(word)
            else:
                lines.append(" ".join(line))
                line = [word]
        lines.append(" ".join(line))
        return lines

    def truncate_str(self, text, max_length, font, font_size):
        """
        Caluculates the length of a string when rendered with the font and size for the label and truncates it to fit in a given length
        :param text: text string to truncate
        :param max_length: max length of string
        :return: truncated string
        """
        truncated = False
        name_width = shapes.stringWidth(text, font, font_size)
        while name_width > max_length:
            text = text[:-1]
            name_width = shapes.stringWidth(text + "...", font, font_size)
            truncated = True
        if truncated:
            return text + "..."
        else:
            return text

    def make_pdf(self, data, debug=False):
        """
        Make the label pdf
        :param data: the data to generate labels from
        :param border: Draw border around labels or not
        """
        # [4, 'Bengt Bengtsson', '018-0123456', 'UAF', [
        #   [8, 'Ancistrus', 'Ancistrus sp Super Red', 180.0, '', 'fixed_price', 2, 'Troligen 2 honor'],
        #   [9, 'Cryptocoryne', 'Cryptocoryne aponogetifolia', '', '', 'auction', 1, ''],
        # [seller_id, seller_name, seller_phone, seller_society, [
        #   [post_id, pop_name, sci_name, post_fixed_price, post_min_price, post_type, quantity, comment

        if self._handle_label_download_request(data):
            return b''

        # import cStringIO
        # output = cStringIO.StringIO()
        from io import BytesIO
        output = BytesIO()
        canvas = Canvas(output)
        canvas.setLineWidth(.3)
        canvas.setTitle("Labels")
        canvas.setAuthor(self.event_name)

        start_y = self.paper_height
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
                post_quantity = post[6]
                post_description = post[7]

                # 24 labels on a sheet, if more start a new sheet
                if count >= 24:
                    canvas.showPage()
                    count = 0
                column = count % 3
                row = math.floor(count / 3)

                x = column * self.label_width + self.paper_left_right_margin
                y = start_y - row * self.label_height - self.paper_top_bottom_margin
                print(y / mm)
                label_space = self.label_spacing * column
                label_x_left = x + self.printer_margin + label_space
                label_x_right = x - self.printer_margin + label_space + self.label_width
                label_y_top = y - self.printer_margin
                label_y_bottom = y - self.label_height + self.printer_margin
                label_text_x = label_x_left + self.left_margin + 1.5 * mm
                upper_text_offset = 1 * mm
                lower_text_offset = 1 * mm
                right_side_offset = 0.5 * mm

                # Border
                if self.border == "yes":
                    canvas.setLineWidth(.3)
                    canvas.line(x + label_space, y, x + label_space + self.label_width, y)  # upper line
                    canvas.line(x + label_space + self.label_width, y, x + label_space + self.label_width, y - self.label_height)  # right line
                    canvas.line(x + label_space, y - self.label_height, x + label_space + self.label_width, y - self.label_height)  # bottom line
                    canvas.line(x + label_space, y - self.label_height, x + label_space, y)  # Left line

                    # inner bounding box for label so that nothing should end up outside of where the printer prints
                    # upper line
                if debug == True:
                    canvas.line(label_x_left,
                                label_y_top,
                                label_x_right,
                                label_y_top)
                    # right line
                    canvas.line(label_x_right,
                                label_y_bottom,
                                label_x_right,
                                label_y_top)
                    # bottom line
                    canvas.line(label_x_left,
                                label_y_bottom,
                                label_x_right,
                                label_y_bottom)
                    # Left line
                    canvas.line(label_x_left,
                                label_y_bottom,
                                label_x_left,
                                label_y_top)

                # Add logo
                center = (self.left_margin - 25) / 2

                basedir = os.path.abspath(os.path.dirname(__file__))
                img_file = os.path.join(basedir, "static/img/logo_250.jpg")
                canvas.drawInlineImage(img_file, label_x_left + center, label_y_top - 30, 25, 25)

                canvas.setLineWidth(1)
                canvas.line(label_x_left + self.left_margin, label_y_bottom, label_x_left + self.left_margin, label_y_top)  # Left line
                canvas.setLineWidth(.3)

                # Post id
                canvas.setFont(self.font, 20)
                str_width = shapes.stringWidth(str(post_id), self.font, 20)
                center = (self.left_margin - str_width) / 2
                canvas.drawString(label_x_left + center, label_y_top - self.row_height * 5, str(post_id))          # Post id

                # Sale type and price below the post id in the left column
                left_column_center = label_x_left + self.left_margin / 2
                canvas.setFont(self.font, 7)
                if post_type == "fixed_price":
                    canvas.drawCentredString(left_column_center, label_y_top - self.row_height * 6, u"Fastpris")
                    if post_fixed_price is not None and len(str(post_fixed_price)) > 0:
                        canvas.setFont(self.bold_font, 7)
                        canvas.drawCentredString(left_column_center, label_y_top - self.row_height * 6 - 2.5 * mm, "{} kr".format(int(post_fixed_price)))
                if post_type == "auction":
                    canvas.drawCentredString(left_column_center, label_y_top - self.row_height * 6, u"Auktion")
                    if post_min_price is not None and len(str(post_min_price)) > 0:
                        canvas.setFont(self.font, 6)
                        canvas.drawCentredString(left_column_center, label_y_top - self.row_height * 6 - 2.2 * mm, u"Minimipris")
                        canvas.setFont(self.bold_font, 7)
                        canvas.drawCentredString(left_column_center, label_y_top - self.row_height * 6 - 4.8 * mm, "{} kr".format(int(post_min_price)))

                # Event name and date
                canvas.setFont(self.font, self.font_size - 2)
                canvas.drawString(label_text_x, label_y_top - self.row_height * 1 + upper_text_offset + right_side_offset, "{} - {}".format(self.event_name, self.event_date))

                # popular and scientific names; moved up one row now that sale type
                # is displayed in the left column.
                if sci_name != "" and pop_name != "":
                    names = self.make_multiline("{} - {}".format(sci_name, pop_name), self.text_width, self.bold_font, self.font_size)
                elif sci_name != "":
                    names = self.make_multiline(sci_name, self.text_width, self.bold_font, self.font_size)
                elif pop_name != "":
                    names = self.make_multiline(pop_name, self.text_width, self.bold_font, self.font_size)
                else:
                    names = []
                canvas.setFont(self.bold_font, self.font_size)
                if len(names) > 0:
                    canvas.drawString(label_text_x, label_y_top - self.row_height * 2 + upper_text_offset + right_side_offset, names[0])
                if len(names) > 1:
                    canvas.drawString(label_text_x, label_y_top - self.row_height * 3 + upper_text_offset + right_side_offset, names[1])
                canvas.setFont(self.font, self.font_size)

                # Barcode for the zero-padded four digit post id. Keep it in the
                # gap between the name and description rows so the existing text
                # layout does not need to move.
                barcode_value = str(post_id).zfill(4)
                post_barcode = code128.Code128(
                    barcode_value,
                    barWidth=0.65 * mm,
                    barHeight=3.9 * mm,
                    humanReadable=False
                )
                barcode_x = label_text_x - 3 * mm
                barcode_y = label_y_top - self.row_height * 5 + 5.2 * mm + right_side_offset
                post_barcode.drawOn(canvas, barcode_x, barcode_y)

                # Description
                comments = self.make_multiline(post_description, self.text_width, self.font, self.font_size)
                description_offset = self.row_height * 0.5
                for idx, comment in enumerate(comments):
                    if idx < 3:
                        canvas.drawString(
                            label_text_x,
                            label_y_top - self.row_height * (5 + idx) - lower_text_offset + description_offset + right_side_offset,
                            comment
                        )

                #Seller name and phone
                if self.label_type == ZLabels.with_margins_24 or self.label_type == ZLabels.with_margins_24_typ_2:
                    row = 8
                else:
                    row = 7
                canvas.setFont(self.font, 7)
                seller_offset = self.row_height * 0.5
                canvas.drawString(label_text_x, label_y_top - self.row_height * row - lower_text_offset - seller_offset + right_side_offset, "{}".format(self.truncate_str("Nr {}: {}  {}".format(seller_id, seller_phone, seller_name), self.text_width, self.font, 7)))  # Seller Name



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
    # MK = ZLabels("test", "UAF Storauktion", "2016-11-27", "Uppsala Akvarierförening", ZLabels.with_margins_24)
    # MK = ZLabels("test", "UAF Storauktion", "2016-11-27", "Uppsala Akvarierförening", ZLabels.without_margins_24)
    MK = ZLabels("test", "UAF Storauktion", "2016-11-27", ZLabels.with_top_margin_24)



    test_data = [
        [4, 'Bengt Bengtsson', '018-0123456', 'UAF', [
            [888, 'Ancistrus', 'Ancistrus sp Super Red', 180.0, '', 'fixed_price', 2, 'Troligen 2 honor'],
            [9, 'Cryptocoryne', 'Cryptocoryne aponogetifolia', 80, '', 'fixed_price', 1, ''],
            [111, "Labidochromis caeruleus", u"Golden labidochromis", 888, '', 'fixed_price', 5, 'Mycket Lång kommentar, hur ska det gå? Det här kan aldrig fungera'],
            [222, "Crossocheilus oblongus", u"Siamesisk algätare, algätare", '', '', 'auction', 20, ''],
            [223, 'Crystal red räka', 'Caridina cf. cantonensis ”Crystal Red”', '', 130, 'auction', 20, ''],
            [88, "Ciklidgräs", u"Ophiopogon japonicus", 80.0, '', 'fixed_price', 1, ''],
            [223, 'Crystal red räka', 'Caridina cf. cantonensis ”Crystal Red”', '', 130, 'auction', 20, ''],
            [88, "Ciklidgräs", u"Ophiopogon japonicus", 80.0, '', 'fixed_price', 1, ''],
            [223, 'Crystal red räka', 'Caridina cf. cantonensis ”Crystal Red”', '', 130, 'auction', 20, ''],
            [88, "Ciklidgräs", u"Ophiopogon japonicus", 80.0, '', 'fixed_price', 1, ''],
            [888, 'Ancistrus', 'Ancistrus sp Super Red', 180.0, '', 'fixed_price', 2, 'Troligen 2 honor'],
            [9, 'Cryptocoryne', 'Cryptocoryne aponogetifolia', 80, '', 'fixed_price', 1, ''],
            [111, "Labidochromis caeruleus", u"Golden labidochromis", 888, '', 'fixed_price', 5,
             'Mycket Lång kommentar, hur ska det gå? Det här kan aldrig fungera'],
            [222, "Crossocheilus oblongus", u"Siamesisk algätare, algätare", '', '', 'auction', 20, ''],
            [223, 'Crystal red räka', 'Caridina cf. cantonensis ”Crystal Red”', '', 130, 'auction', 20, ''],
            [9, 'Cryptocoryne', 'Cryptocoryne aponogetifolia', 80, '', 'fixed_price', 1, ''],
            [111, "Labidochromis caeruleus", u"Golden labidochromis", 888, '', 'fixed_price', 5,
             'Mycket Lång kommentar, hur ska det gå? Det här kan aldrig fungera'],
            [222, "Crossocheilus oblongus", u"Siamesisk algätare, algätare", '', '', 'auction', 20, ''],
            [223, 'Crystal red räka', 'Caridina cf. cantonensis ”Crystal Red”', '', 130, 'auction', 20, ''],
            [9, 'Cryptocoryne', 'Cryptocoryne aponogetifolia', 80, '', 'fixed_price', 1, ''],
            [111, "Labidochromis caeruleus", u"Golden labidochromis", 888, '', 'fixed_price', 5,
             'Mycket Lång kommentar, hur ska det gå? Det här kan aldrig fungera'],
            [222, "Crossocheilus oblongus", u"Siamesisk algätare, algätare", '', '', 'auction', 20, ''],
            [223, 'Crystal red räka', 'Caridina cf. cantonensis ”Crystal Red”', '', 130, 'auction', 20, ''],
            [88, "Ciklidgräs", u"Ophiopogon japonicus", 80.0, '', 'fixed_price', 1, '']
        ]]
    ]


    pdf = MK.make_pdf(test_data, True)
    pdf_temp = "temp_pdf.pdf"
    f = open(pdf_temp, "wb")
    f.write(pdf)
    f.close()