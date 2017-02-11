# coding=utf-8
__author__ = 'kristian'


import barcode
from barcode.writer import ImageWriter

ean = barcode.get('ean13', '000000000001', writer=ImageWriter())
filename = ean.save('ean13')
