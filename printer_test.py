# coding=utf-8

# os.popen gives no exception when the command to run isn't found. Just prints a message to the console.
# subprocess.run gives a FileNotFoundError exception.

# import os
# 
# # lpstat -d gives the deafult printer as the last word on the row
# default_printer = os.popen('lpstat -d').read().split()[-1]
# # lpstat -a gives one printer per line, starting with the printer name followed by status message
# all_printers_str = os.popen('lpstat -a').read().strip()
# # Split lines
# all_printers_lst = all_printers_str.split("\n")
# printer_names = []
# # Split words in each row and save the printer name
# for row in all_printers_lst:
#     words = row.split()
#     printer_names.append(words[0].strip())
# 
# print(default_printer)
# print(printer_names)
print("*******************")

#This works with cups and printers installed
#This works with cups and no printers
#This works when cups is not installed
import subprocess
try:
    result = subprocess.run(['lpstat', '-a'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    all_printer_str = result.stdout.decode("utf-8")
    err_msg = result.stderr.decode("utf-8")

    print("stdout: {}".format(all_printer_str))
    print("error: {}".format(err_msg))

    all_printers_lst = str(all_printer_str).strip().split("\n")
    print(all_printers_lst)
    printer_names = []
    # Split words in each row and save the printer name
    if err_msg == "":
        for row in all_printers_lst:
            words = row.split()
            printer_names.append(words[0].strip())
except FileNotFoundError:
    print("Skrivar sytem CUPS är inte installerat. Inga skrivare hittades")
    printer_names = []
# print(default_printer)
print("Found printers: {}".format(printer_names))