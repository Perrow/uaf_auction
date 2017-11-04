# coding=utf-8

import os

# lpstat -d gives the deafult printer as the last word on the row
default_printer = os.popen('lpstat -d').read().split()[-1]
# lpstat -a gives one printer per line, starting with the printer name followed by status message
all_printers_str = os.popen('lpstat -a').read().strip()
# Split lines
all_printers_lst = all_printers_str.split("\n")
printer_names = []
# Split words in each row and save the printer name
for row in all_printers_lst:
    words = row.split()
    printer_names.append(words[0].strip())

print(default_printer)
print(printer_names)