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

sellers = [[u"Kalle Persson", u"Tallmon 1, 54878 Näppeby", u"kalle.persson@mail.com".lower(), u"051-25468", u"UAF", u"yes", u"password", time.strftime("%Y-%m-%d %H:%M:%S"), u"yes", u"yes"]]
for n in range(15):
    sellers.append(F.generate_seller())

print(sellers)

posts = []
for seller_id in range(1, len(sellers) + 1):
    for i in range(0, random.randint(0, 20)):
        posts.append(F.generate_fish_auction_post(seller_id))
 
    for i in range(0, random.randint(0, 20)):
        posts.append(F.generate_plant_fleamarket_post(seller_id))

    for i in range(0, random.randint(0, 20)):
        posts.append(F.generate_shrimp_fleamarket_post(seller_id))

print(posts)

auction_info = (
    (u"Uppsala Akvarieförening", u"UAF", u"Uppsala", u"Uppsala storauktion", u"2017", u"2017-11-19", 0.20, u"Uppsala akvarieförening anordnar en storauktion bla bla..."),
)

# sellers = (
#     (u"Kalle Persson", u"Tallmon 1, 54878 Näppeby", u"kalle.persson@mail.com".lower(), u"051-25468", u"UAF", u"yes", u"password", time.strftime("%Y-%m-%d %H:%M:%S"), u"yes", u"yes"),
#     (u"Olle Karlsson", u"Vägen 5, 84520 Frippo", u"olle.karlsson@mail.com".lower(), u"0730-421587", u"UAF", u"yes", u"123456", time.strftime("%Y-%m-%d %H:%M:%S"), u"yes", u"yes"),
#     (u"Lena Svensson", u"Skogen 65, 51242 Skogsbyn", u"Lena.svensson@mail.com".lower(), u"0733-954321", u"Haninge AF", u"no", u"lösenord", time.strftime("%Y-%m-%d %H:%M:%S"), u"yes", u"yes"),
#     (u"Pia Larsson", u"Fälgtvägen 54, 85241 Byn", u"Pia.Larsson@mail.com".lower(), u"0733-987632", u"Malmö AF", u"no", u"secret", time.strftime("%Y-%m-%d %H:%M:%S"), u"yes", u"yes"),
#     (u"Sören Ås", u"Tvärgatan 1, 46578 Småstad", u"SÖREN.Ås@mail.com".lower(), u"0733-987632", u"SAF", u"no", u"secret", time.strftime("%Y-%m-%d %H:%M:%S"), u"yes", u"yes"),
#     (u"Test", u"Tvärgatan 1, 46578 Småstad", u"åäöÅÄÖéÉèÈ.üÜ@mail.com".lower(), u"0733-987632", u"SAF", u"no", u"secret", time.strftime("%Y-%m-%d %H:%M:%S"), u"yes", u"yes")
# )
# 
# posts = (
#     (1, u"Barbus fasciolatus", u"Afrikansk bandbarb", u"Temperatur: 20 - 26 °C  Längd: 6 cm  Ursprunglig världsdel: Afrika  pH: 6-7  Minsta akvarie storlek: 80 cm & 100 liter", 1, time.strftime("%Y-%m-%d %H:%M:%S")),
#     (2, u"Pangio kuhlii", u"Kuhlii-ål", u"", 1, time.strftime("%Y-%m-%d %H:%M:%S")),
#     (1, u"Paracheirodon innesi", u"Neontetra", u"", 1, time.strftime("%Y-%m-%d %H:%M:%S")),
#     (2, u"Pethia padamya", u"Odessabarb", u"", 1, time.strftime("%Y-%m-%d %H:%M:%S")),
#     (1, u"Thayeria boehlkei", u"Vinkeltetra", u"Temperatur: 23 - 28 °C  Längd: 6 cm  Ursprunglig världsdel: Sydamerika  pH: 6-7.5  Minsta akvarie storlek: 80 cm & 90 liter", 1, time.strftime("%Y-%m-%d %H:%M:%S")),
#     (4, u"Trigonostigma heteromorpha", u"Kilfläcksrasbora", u"", 1, time.strftime("%Y-%m-%d %H:%M:%S")),
#     (2, u"Pterophyllum scalare", u"Skalar", u"Temperatur: 24 - 26 °C  Längd: 16 cm  Ursprunglig världsdel: Sydamerika  pH: 6-7.5  Minsta akvarie storlek: 90 cm & 200 liter", 1, time.strftime("%Y-%m-%d %H:%M:%S")),
#     (3, u"Trigonostigma heteromorpha", u"Kilfläcksrasbora", u"", 1, time.strftime("%Y-%m-%d %H:%M:%S")),
# )

all_types = (
    (1, u"Fisk till auktionen", u"auction"),
    (2, u"Fisk till fasta bordet", u"fixed_price"),
    (3, u"Räkor till auktionen", u"auction"),
    (4, u"Räkor till fasta bordet", u"fixed_price"),
    (5, u"Övriga djur till auktionen", u"auction"),
    (6, u"Övriga djur till fasta bordet", u"fixed_price"),
    (7, u"Växter till auktionen", u"auction"),
    (8, u"Växter till fasta bordet", u"fixed_price"),
    (9, u"Tillbehör till auktionen", u"auction"),
    (10, u"Tillbehör till fasta bordet", u"fixed_price"),
    (11, u"Övrigt till auktionen", u"auction"),
    (12, u"Övrigt till fasta bordet", u"fixed_price"))

used_types = (
    (1, u"Fisk till auktionen", u"auction"),
    (4, u"Räkor till fasta bordet", u"fixed_price"),
    (6, u"Övriga djur till fasta bordet", u"fixed_price"),
    (8, u"Växter till fasta bordet", u"fixed_price"),
    (10, u"Tillbehör till fasta bordet", u"fixed_price"),
    (12, u"Övrigt till fasta bordet", u"fixed_price"))

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

    cur.execute('CREATE TABLE sellers (seller_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT TEXT, address TEXT, email TEXT, phone TEXT, aquarium_club TEXT, password TEXT, isAdmin TEXT, time_stamp TEXT, accepts_cookies TEXT, accepts_database TEXT)')
    cur.execute('CREATE TABLE posts (obj_id INTEGER PRIMARY KEY AUTOINCREMENT, seller_id INTEGER, scientific_name TEXT, plain_name TEXT, description TEXT, type TEXT, minimum_price FLOAT, fixed_price FLOAT, sold_price FLOAT, sold_on TEXT, time_stamp_registration TEXT, time_stamp_sold TEXT, label_printed TEXT)')
    cur.execute('CREATE TABLE used_types (type_id INTEGER PRIMARY KEY, description TEXT, sale_type TEXT)')
    cur.execute('CREATE TABLE all_types (type_id INTEGER PRIMARY KEY, description TEXT, sale_type TEXT)')
    cur.execute('CREATE TABLE auction_info (type_id INTEGER PRIMARY KEY, hosting_association TEXT, hosting_association_abrv TEXT, city TEXT, event_name TEXT, year TEXT, date TEXT, commission INT, description TEXT)')
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
        cur.execute("INSERT INTO sellers (name, address, email, phone, aquarium_club, isAdmin, password, time_stamp, accepts_cookies, accepts_database) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", seller_data)
    password_file.close()

    cur.executemany("INSERT INTO posts (seller_id, scientific_name, plain_name, description, type, time_stamp_registration, minimum_price, fixed_price, label_printed) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", posts)
    cur.executemany("INSERT INTO used_types (type_id, description, sale_type) VALUES(?, ?, ?)", used_types)
    cur.executemany("INSERT INTO all_types (type_id, description, sale_type) VALUES(?, ?, ?)", all_types)
    cur.executemany("INSERT INTO auction_info (hosting_association, hosting_association_abrv, city, event_name, year, date, commission, description) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", auction_info)
    cur.executemany("INSERT INTO printers (purpose, cups_name) VALUES (?, ?)", printers)



