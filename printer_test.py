# coding=utf-8


import os

default_printer = os.popen('lpstat -d').read().split()[0]
all_printers = os.popen('lpstat -a').read()
print("Default: {}".format(default_printer))
print("All installed printers:")

for printer in all_printers:
    print("{}".format(printer))