# coding=utf-8
__author__ = 'kristian'

import sqlite3
import bcrypt

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

conn = sqlite3.connect("auktion.db3")
conn.text_factory = str

auction_info = (
    ("Uppsala Akvarieförening", "UAF", "Uppsala", "Uppsala storauktion", "2017", "2017-11-19", 0.15),
)

sellers = (
    ("Kalle Persson", "Tallmon 1, 54878 Näppeby", "kalle.persson@mail.com", "051-25468", "UAF", "yes", "password"),
    ("Olle Karlsson", "Vägen 5, 84520 Frippo", "olle.karlsson@mail.com", "0730-421587", "UAF", "yes", "123456"),
    ("Lena Svensson", "Skogen 65, 51242 Skogsbyn", "Lena.svensson@mail.com", "0733-954321", "Haninge AF", "no", "lösenord"),
    ("Pia Larsson", "Fälgtvägen 54, 85241 Byn", "Pia.Larsson@mail.com", "0733-987632", "Malmö AF", "no", "secret")
)

posts = (
    (1, "Barbus fasciolatus", "Afrikansk bandbarb", "Temperatur: 20 - 26 °C  Längd: 6 cm  Ursprunglig världsdel: Afrika  pH: 6-7  Minsta akvarie storlek: 80 cm & 100 liter  Svårighetsgrad: 3/5", 5, 1),
    (2, "Pangio kuhlii", "Kuhlii-ål", "", 4, 1),
    (1, "Paracheirodon innesi", "Neontetra", "", 10, 1),
    (2, "Pethia padamya", "Odessabarb", "", 5, 1),
    (1, "Thayeria boehlkei", "Vinkeltetra", "Temperatur: 23 - 28 °C  Längd: 6 cm  Ursprunglig världsdel: Sydamerika  pH: 6-7.5  Minsta akvarie storlek: 80 cm & 90 liter  Svårighetsgrad: 2/5", 5, 1),
    (4, "Trigonostigma heteromorpha", "Kilfläcksrasbora", "", 3, 1),
    (2, "Pterophyllum scalare", "Skalar", "Temperatur: 24 - 26 °C  Längd: 16 cm  Ursprunglig världsdel: Sydamerika  pH: 6-7.5  Minsta akvarie storlek: 90 cm & 200 liter  Svårighetsgrad: 2/5 ", 5, 1),
    (3, "Trigonostigma heteromorpha", "Kilfläcksrasbora", "", 7, 1),
)

types = (
    (1, "Fisk till auktionen", "auction"),
    (2, "Fisk till fasta bordet", "fixed_price"),
    (3, "Räkor till auktionen", "auction"),
    (4, "Räkor till fasta bordet", "fixed_price"),
    (5, "Övriga djur till fasta bordet", "fixed_price"),
    (6, "Växter till auktionen", "auction"),
    (7, "Växter till fasta bordet", "fixed_price"),
    (8, "Tillbehör till fasta bordet", "fixed_price"),
    (9, "Övrigt till fasta bordet", "fixed_price"))

with conn:
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS sellers")
    cur.execute("DROP TABLE IF EXISTS posts")
    cur.execute("DROP TABLE IF EXISTS types")
    cur.execute("DROP TABLE IF EXISTS auction_info")


    cur.execute('CREATE TABLE sellers (seller_id INTEGER PRIMARY KEY, name TEXT TEXT, address TEXT, email TEXT, phone TEXT, aquarium_club TEXT, password TEXT, isAdmin TEXT)')
    cur.execute('CREATE TABLE posts (obj_id INTEGER PRIMARY KEY, seller_id INTEGER, scientific_name TEXT, plain_name TEXT, description TEXT, quantity TEXT, type TEXT, minimum_price FLOAT, fixed_price FLOAT, sold_price FLOAT, sold_on TEXT)')
    cur.execute('CREATE TABLE types (type_id INTEGER PRIMARY KEY, description TEXT, sale_type TEXT)')
    # cur.execute('CREATE TABLE auction_info (type_id INTEGER PRIMARY KEY, name TEXT, year TEXT, date TEXT, commission INT)')
    cur.execute('CREATE TABLE auction_info (type_id INTEGER PRIMARY KEY, hosting_association TEXT, hosting_association_abrv TEXT, city TEXT, event_name TEXT, year TEXT, date TEXT, commission INT)')



    for seller in sellers:
        salt = bcrypt.gensalt()
        password = bcrypt.hashpw(seller[6], salt)
        print(seller[6], salt, password)
        seller_data = seller[:-1] + (password,)
        print(seller_data)
        cur.execute("INSERT INTO sellers (name, address, email, phone, aquarium_club, isAdmin, password) VALUES(?, ?, ?, ?, ?, ?, ?)", seller_data)

    # cur.executemany("INSERT INTO sellers (firstname, lastname, address, email, phone, aquarium_club) VALUES(?, ?, ?, ?, ?, ?)", sellers)
    cur.executemany("INSERT INTO posts (seller_id, scientific_name, plain_name, description, quantity, type) VALUES(?, ?, ?, ?, ?, ?)", posts)
    cur.executemany("INSERT INTO types (type_id, description, sale_type) VALUES(?, ?, ?)", types)
    cur.executemany("INSERT INTO auction_info (hosting_association, hosting_association_abrv, city, event_name, year, date, commission) VALUES(?, ?, ?, ?, ?, ?, ?)", auction_info)




