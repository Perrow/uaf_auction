# coding=utf-8


from reportlab.platypus import (Flowable, Paragraph,
                                SimpleDocTemplate, Spacer)

class LeftLine(Flowable):
    """
    Line flowable --- draws a line in a flowable
    http://two.pairlist.net/pipermail/reportlab-users/2005-February/003695.html
    """

    # ----------------------------------------------------------------------
    def __init__(self, width, height=0):
        """
        Draws a line with a given length from position 0 (left)
        :param width: Length of line
        :param height: height of line
        """
        Flowable.__init__(self)
        self.width = width
        self.height = height

    # ----------------------------------------------------------------------
    def __repr__(self):
        return "Line(w=%s)" % self.width

    # ----------------------------------------------------------------------
    def draw(self):
        """
        draw the line
        """
        self.canv.line(0, self.height, self.width, self.height)


class CenterLine(Flowable):
    """
    Line flowable --- draws a line in a flowable
    http://two.pairlist.net/pipermail/reportlab-users/2005-February/003695.html
    """

    # ----------------------------------------------------------------------
    def __init__(self, width, center):
        """
        Draws a centered line with a specified length around a given position
        :param width: Length of line
        :param center: center of line
        """
        Flowable.__init__(self)
        self.width = width
        self.height = 0
        self.center = center

    # ----------------------------------------------------------------------
    def __repr__(self):
        return "Line(w=%s)" % self.width

    # ----------------------------------------------------------------------
    def draw(self):
        """
        draw the line
        """
        self.canv.line(self.center - self.width / 2, self.height, self.center + self.width / 2, self.height)


class LineBetween(Flowable):
    """
    Line flowable --- draws a line in a flowable
    http://two.pairlist.net/pipermail/reportlab-users/2005-February/003695.html
    """

    # ----------------------------------------------------------------------
    def __init__(self, start, end):
        """
        Draws a line between a start and end position
        :param start: start position
        :param end: end position
        """
        Flowable.__init__(self)
        self.start = start
        self.height = 0
        self.end = end

    # ----------------------------------------------------------------------
    def __repr__(self):
        return "Line(w=%s)" % self.width

    # ----------------------------------------------------------------------
    def draw(self):
        """
        draw the line
        """
        self.canv.line(self.start, self.height, self.end, self.height)
