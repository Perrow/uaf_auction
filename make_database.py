# coding=utf-8
__author__ = 'kristian'

import faker
import random
import sqlite3
import bcrypt
import time
import sys
# reload(sys)
# sys.setdefaultencoding('utf-8')

conn = sqlite3.connect("auktion.db3")
# conn.text_factory = str

F = faker.Faker()

sellers = [[u"Kalle Persson", u"Tallmon 1, 54878 Näppeby", u"kalle.persson@mail.com".lower(), u"051-25468", u"UAF", u"yes", u"password", time.strftime("%Y-%m-%d %H:%M:%S"), u"yes", u"yes", u"no"]]
for n in range(5):
    sellers.append(F.generate_seller())

print(sellers)

posts = []
for seller_id in range(1, len(sellers) + 1):
    for i in range(0, random.randint(0, 10)):
        posts.append(F.generate_fish_auction_post(seller_id))
 
    for i in range(0, random.randint(0, 10)):
        posts.append(F.generate_plant_fleamarket_post(seller_id))

    for i in range(0, random.randint(0, 10)):
        posts.append(F.generate_shrimp_fleamarket_post(seller_id))

print(posts)

auction_info = (
    (u"Uppsala Akvarieförening", u"UAF", u"Uppsala", u"Uppsala Test", u"2018", u"2018-05-20", 0.20, u"Uppsala akvarieförening ordnar ett test av auktionsprogrammet.", "yes"),
)

all_types = (
    (1, u"Fisk till auktionen", u"auction", "yes", "yes"),
    (2, u"Fisk till fasta bordet", u"fixed_price", "yes", "yes"),
    (3, u"Räkor till auktionen", u"auction", "no", "yes"),
    (4, u"Räkor till fasta bordet", u"fixed_price", "no", "yes"),
    (5, u"Övriga djur till auktionen", u"auction", "no", "yes"),
    (6, u"Övriga djur till fasta bordet", u"fixed_price", "no", "yes"),
    (7, u"Växter till auktionen", u"auction", "no", "yes"),
    (8, u"Växter till fasta bordet", u"fixed_price", "no", "yes"),
    (9, u"Tillbehör till auktionen", u"auction", "no", "no"),
    (10, u"Tillbehör till fasta bordet", u"fixed_price", "no", "no"),
    (11, u"Övrigt till auktionen", u"auction", "no", "no"),
    (12, u"Övrigt till fasta bordet", u"fixed_price", "no", "no"))

used_types = (
    (1, u"Fisk till auktionen", u"auction", "yes", "yes"),
    (4, u"Räkor till fasta bordet", u"fixed_price", "no", "yes"),
    (6, u"Övriga djur till fasta bordet", u"fixed_price", "no", "yes"),
    (8, u"Växter till fasta bordet", u"fixed_price", "no", "yes"),
    (10, u"Tillbehör till fasta bordet", u"fixed_price", "no", "no"),
    (12, u"Övrigt till fasta bordet", u"fixed_price", "no", "no"))

printers = (
    ("label", ""),
    ("paper", "")
)

with conn:
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS sellers")
    cur.execute("DROP TABLE IF EXISTS posts")
    cur.execute("DROP TABLE IF EXISTS used_types")
    cur.execute("DROP TABLE IF EXISTS all_types")
    cur.execute("DROP TABLE IF EXISTS auction_info")
    cur.execute("DROP TABLE IF EXISTS printers")

    cur.execute('CREATE TABLE sellers (seller_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT TEXT, address TEXT, email TEXT, phone TEXT, aquarium_club TEXT, password TEXT, isAdmin TEXT, time_stamp TEXT, accepts_cookies TEXT, accepts_database TEXT, has_checked_in TEXT)')
    cur.execute('CREATE TABLE posts (obj_id INTEGER PRIMARY KEY AUTOINCREMENT, seller_id INTEGER, scientific_name TEXT, plain_name TEXT, quantity INTEGER, description TEXT, type TEXT, minimum_price FLOAT, fixed_price FLOAT, sold_price FLOAT, sold_on TEXT, sold_by TEXT, time_stamp_registration TEXT, time_stamp_sold TEXT, label_printed TEXT, is_checked_in TEXT)')
    cur.execute('CREATE TABLE used_types (type_id INTEGER PRIMARY KEY, description TEXT, sale_type TEXT, scientific_name_obligatory TEXT, display_scientific_name_input TEXT)')
    cur.execute('CREATE TABLE all_types (type_id INTEGER PRIMARY KEY, description TEXT, sale_type TEXT, scientific_name_obligatory TEXT, display_scientific_name_input TEXT)')
    cur.execute('CREATE TABLE auction_info (type_id INTEGER PRIMARY KEY, hosting_association TEXT, hosting_association_abrv TEXT, city TEXT, event_name TEXT, year TEXT, date TEXT, commission INT, description TEXT, registration_open TEXT)')
    cur.execute('CREATE TABLE printers (purpose TEXT, cups_name TEXT)')

    password_file = open("sellers.txt", "w")  # Textfile to be able to log in with the passwords.
    for seller in sellers:
        password_file.write("{} - {}\n".format(seller[2], seller[6]))
        salt = bcrypt.gensalt()
        password = bcrypt.hashpw(seller[6].encode("utf-8"), salt)
        print(seller[6], salt, password)
        seller_data = list(seller)
        seller_data[6] = password
        print(seller_data)
        cur.execute("INSERT INTO sellers (name, address, email, phone, aquarium_club, isAdmin, password, time_stamp, accepts_cookies, accepts_database, has_checked_in) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", seller_data)
    password_file.close()

    cur.executemany("INSERT INTO posts (seller_id, scientific_name, plain_name, quantity, description, type, time_stamp_registration, minimum_price, fixed_price, label_printed, is_checked_in) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", posts)
    cur.executemany("INSERT INTO used_types (type_id, description, sale_type, scientific_name_obligatory, display_scientific_name_input) VALUES(?, ?, ?, ?, ?)", used_types)
    cur.executemany("INSERT INTO all_types (type_id, description, sale_type, scientific_name_obligatory, display_scientific_name_input) VALUES(?, ?, ?, ?, ?)", all_types)
    cur.executemany("INSERT INTO auction_info (hosting_association, hosting_association_abrv, city, event_name, year, date, commission, description, registration_open) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", auction_info)
    cur.executemany("INSERT INTO printers (purpose, cups_name) VALUES (?, ?)", printers)
    
    # To add new column to existing database table:
    # ALTER TABLE auction_info ADD COLUMN registration_open TEXT;
    # UPDATE auction_info SET registration_open = "yes";

