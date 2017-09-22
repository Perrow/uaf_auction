# coding=utf-8

import os
import sqlite3
import time
# from flask import Flask
from flask import jsonify
from flask import make_response
from flask import send_file
import bcrypt
from flask_login import LoginManager, login_required, login_user, logout_user, current_user  # , UserMixin
from flask import Flask, request, abort, redirect, url_for, render_template, flash  #, Response
from functools import wraps
###
import user_model
import zlabels
import make_compilation_pdf
import make_receipt_pdf
import list_shorter
import make_economic_report_pdf
import make_wall_list_pdf

# set default encoding on the server to utf-8 pyhton 2.7
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


__author__ = 'Kristian'


app = Flask(__name__)
app.config['SECRET_KEY'] = "HK(9045hjfd204hHFD345d"
DATABASE = "auktion.db3"
VERSION = "0.33"

# For flask-login
lm = LoginManager()
lm.init_app(app)
lm.login_view = "login"
# lm.anonymous_user = anonymous_user.Anonymous

# *** Login and Authentication *** #


def admin_required(func):
    """
    A decorater that checks if a logged in user has admin privileges
    :param func: page that need to be checked
    :return: If user has admin privileges then the page is rendered otherwise index page is rendered
    """
    @wraps(func)
    @login_required
    def func_wrapper(*args, **kwargs):
        if current_user.is_admin:
            print(current_user.name, current_user.is_admin)
            return func(*args, **kwargs)
        else:
            flash("Du måste vara administratör för att komma åt sidan.")
            return redirect(url_for('index'))

    return func_wrapper


@lm.user_loader
def load_user(user_id):
    """
    Loads a user from the database identified by id
    :param user_id: user id must match the database
    :return:
    """
    conn = sqlite3.connect(DATABASE)
    print("Load_user id={}".format(user_id))
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT name, email, isAdmin  FROM sellers WHERE seller_id=?", (user_id,))
        result = cur.fetchone()
        if result:
            name = result[0]
            email = result[1]
            is_admin = result[2]
            if is_admin == "yes":
                is_admin = True
            else:
                is_admin = False

            return user_model.User(name, user_id, email, is_admin)
    return None


def auth(username, password):
    """
    Authenticates a user against the database
    :param username:
    :param password:
    :return:
    """
    conn = sqlite3.connect(DATABASE)
    with conn:
        cur = conn.cursor()
        # cur.execute("SELECT id FROM users WHERE email=? and password=?", (username, password))
        cur.execute("SELECT seller_id, password FROM sellers WHERE email=?  COLLATE NOCASE", (username, ))
        result = cur.fetchone()
        if result:  # email is in database, check that password is correct
            if bcrypt.checkpw(password.encode('utf8'), result[1].encode('utf8')):
                user_id = result[0]
                return load_user(user_id)
            else:
                return None
        else:
            return None

# *** Utils *** #


def get_auction_info():
    """
    Extract the auction info from the database
    :return: club_name, club_short_name, event_name, event_date, event_city, commision
    """
    conn = sqlite3.connect(DATABASE)

    with conn:
        cur = conn.cursor()
        cur.execute("SELECT hosting_association, hosting_association_abrv, event_name, date, city, commission from auction_info")
        auction_info = cur.fetchone()
        club_name = auction_info[0]
        club_short_name = auction_info[1]
        event_name = auction_info[2]
        event_date = auction_info[3]
        event_city = auction_info[4]
        commision = auction_info[5]
        return club_name, club_short_name, event_name, event_date, event_city, commision

# *** Routes *** #


@app.route('/')
def index():
    """
    Index page
    :return:
    """
    if current_user.is_authenticated:
        print("Current user: {}".format(current_user.name))
        print("ÄR admin: {}".format(current_user.is_admin))
    else:
        print("No current user")

    conn = sqlite3.connect(DATABASE)
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT hosting_association, event_name, date, description from auction_info")
        auction_info = cur.fetchone()
        club_name = auction_info[0]
        event_name = auction_info[1]
        event_date = auction_info[2]
        event_description = auction_info[3]

    return render_template('index.html', event_name=event_name, club_name=club_name, event_date=event_date, event_description=event_description)


@app.route('/new_seller', methods=['GET', 'POST'])
def new_seller():
    """
   Page for adding new sellers to the database
    :return:
    """
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        email = request.form['email'].strip().lower()
        phone = request.form['phone']
        aquarium_club = request.form['aquarium_club']
        password = request.form['password'].strip().encode('utf-8')
        accept_cookies = "no"
        if request.form.get('cookies'):
            accept_cookies = "yes"
        accept_database = "no"
        if request.form.get('database'):
            accept_database = "yes"

        conn = sqlite3.connect(DATABASE)
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT email, seller_id FROM sellers WHERE email=?", (email,))
            result = cur.fetchone()
            if result:
                return render_template('done_seller_exists.html')
            else:
                salt = bcrypt.gensalt()
                encrypted_password = bcrypt.hashpw(password, salt)
                seller_data = [name, address, email, phone, aquarium_club, encrypted_password, "no", time.strftime("%Y-%m-%d %H:%M:%S"), accept_cookies, accept_database]
                cur.execute("INSERT INTO sellers (name, address, email, phone, aquarium_club, password, isAdmin, time_stamp, accepts_cookies, accepts_database) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", seller_data)

                flash("Användare {} skapad.".format(name))
            authed_user = auth(email, password)
            if authed_user:
                login_user(authed_user)

            return redirect(url_for('index'))
    else:
        return render_template('new_seller.html')


@app.route("/admin_register_many_posts", methods=['GET', 'POST'])
@admin_required
def admin_register_many_posts():
    """
    Register many new post at the same time for another seller
    :return:
    """
    if request.method == 'POST':
        # seller_email = request.form['seller_email']
        types = request.form.getlist('type')
        scinames = request.form.getlist('sciname')
        popnames = request.form.getlist('popname')
        min_prices = request.form.getlist('min_price')
        fixed_prices = request.form.getlist('fixed_price')
        descriptions = request.form.getlist('description')
        seller_id = request.form['seller_select']

        new_items = zip(scinames, popnames, descriptions, types, min_prices, fixed_prices)
        conn = sqlite3.connect(DATABASE)
        with conn:
            cur = conn.cursor()
            for scientific_name, plain_name, description, post_type, minimum_price, fixed_price in new_items:
                cur.execute("INSERT INTO posts (seller_id, scientific_name, plain_name, description, type, minimum_price, fixed_price, time_stamp_registration) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", (seller_id, scientific_name, plain_name, description, post_type, minimum_price, fixed_price, time.strftime("%Y-%m-%d %H:%M:%S")))

            flash("Posterna registrerade.")

    # Fetch sale types from database, generate a select for the default sale type
    conn = sqlite3.connect(DATABASE)
    select = '<select class="selectpicker form-control" id="master_type" name="master_type">'
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT type_id, description FROM types ORDER BY type_id")
        result = cur.fetchall()
        for row in result:
            tempstr = '<option value="{}">{}</option>'.format(row[0], row[1])
            select += tempstr
        # Get list of sellers
        cur.execute("SELECT seller_id, name FROM sellers")
        sellers = cur.fetchall()

    select += '</select>'

    return render_template('admin_register_many_posts.html', select=select, sellers=sellers)


@app.route("/register_many_posts", methods=['GET', 'POST'])
@login_required
def register_many_posts():
    """
    Register many new post at the same time
    :return:
    """
    if request.method == 'POST':
        # seller_email = request.form['seller_email']
        types = request.form.getlist('type')
        scinames = request.form.getlist('sciname')
        popnames = request.form.getlist('popname')
        min_prices = request.form.getlist('min_price')
        fixed_prices = request.form.getlist('fixed_price')
        descriptions = request.form.getlist('description')

        # print(seller_email)
        print(types)
        print(scinames)
        print(popnames)
        print(min_prices)
        print(fixed_prices)
        print(descriptions)
        new_items = zip(scinames, popnames, descriptions, types, min_prices, fixed_prices)
        # print(new_items)

        seller_id = current_user.get_id()
        conn = sqlite3.connect(DATABASE)
        with conn:
            cur = conn.cursor()
            for scientific_name, plain_name, description, post_type, minimum_price, fixed_price in new_items:
                cur.execute("INSERT INTO posts (seller_id, scientific_name, plain_name, description, type, minimum_price, fixed_price, time_stamp_registration) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", (seller_id, scientific_name, plain_name, description, post_type, minimum_price, fixed_price, time.strftime("%Y-%m-%d %H:%M:%S")))

            flash("Posterna registrerade.")

    # Fetch sale types from database, generate a select for the default sale type
    conn = sqlite3.connect(DATABASE)
    select = '<select  class="selectpicker form-control" id="master_type" name="master_type">'
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT type_id, description FROM types ORDER BY type_id")
        result = cur.fetchall()
        for row in result:
            tempstr = '<option value="{}">{}</option>'.format(row[0], row[1])
            select += tempstr
    select += '</select>'
    return render_template('register_many_posts.html', select=select)


@app.route('/list')
def list_posts():
    """
    Page for listing all posts in the database
    """
    conn = sqlite3.connect(DATABASE)
    with conn:
        cur = conn.cursor()
        nr_posts = []
        cur.execute("select count(*) from posts")
        res = cur.fetchone()
        nr_posts.append("Antal poster: {}".format(res[0]))
        cur.execute("SELECT count(posts.type), types.sale_type from posts LEFT JOIN types ON posts.type = types.type_id group by types.sale_type")
        res = cur.fetchall()

        for row in res:
            if row[1] == "auction":
                nr_posts.append("Auktion: {}".format(row[0]))
            if row[1] == "fixed_price":
                nr_posts.append("Fastpris: {}".format(row[0]))

        cur.execute("""SELECT  posts.obj_id, posts.scientific_name, posts.plain_name, posts.description, types.description
        FROM posts
        INNER JOIN types
        ON posts.type=types.type_id""")
        result = cur.fetchall()
        return render_template('list_posts.html', heading="Anmälda poster", nr_posts=nr_posts, data=result)


@app.route('/list_my_posts')
def list_my_posts():
    """
    Page for listing current users posts in the database
    """
    conn = sqlite3.connect(DATABASE)
    with conn:
        cur = conn.cursor()
        cur_id = current_user.get_id()
        print(cur_id)
        nr_posts = []
        cur.execute("SELECT  COUNT(*) FROM posts WHERE seller_id=?", cur_id)
        res = cur.fetchone()
        nr_posts.append("Antal poster: {}".format(res[0]))
        cur.execute("SELECT COUNT(posts.type), types.sale_type from posts LEFT JOIN types ON posts.type = types.type_id WHERE seller_id = ? GROUP BY types.sale_type", cur_id)
        res = cur.fetchall()

        for row in res:
            if row[1] == "auction":
                nr_posts.append("Auktion: {}".format(row[0]))
            if row[1] == "fixed_price":
                nr_posts.append("Fastpris: {}".format(row[0]))

        cur.execute("""SELECT  posts.obj_id, posts.scientific_name, posts.plain_name, posts.description, types.description
        FROM posts
        INNER JOIN types
        ON posts.type=types.type_id
        WHERE seller_id = ?""", cur_id)
        result = cur.fetchall()
        return render_template('list_posts.html', heading="Mina anmälda poster", nr_posts=nr_posts, data=result)


@app.route('/list_seller')
@admin_required
def list_seller():
    """
    Page for listing all sellers in the database
    """
    conn = sqlite3.connect(DATABASE)
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT name, address, email, phone, aquarium_club, seller_id FROM sellers")
        result = cur.fetchall()
        return render_template('list_seller.html', data=result)


@app.route('/reports')
@admin_required
def reports():
    """
    Reports page
    :return:
    """
    return render_template('reports.html')


@app.route("/auktion", methods=['GET', 'POST'])
@admin_required
def auktion():
    """
    Shows the auction form and updates the database with the price it sold for and the sale type
    :return:
    """
    if request.method == 'POST':
        post_id = request.form['post_id']
        price = request.form['price']
        sale_type = request.form['sale_type']
        conn = sqlite3.connect(DATABASE)
        with conn:
            cur = conn.cursor()
            cur.execute("UPDATE Posts SET sold_price=?, sold_on=?, time_stamp_sold=? WHERE obj_id=?", (price, sale_type, time.strftime("%Y-%m-%d %H:%M:%S"), post_id))
            flash("Post {} registrerad som såld.".format(post_id))
        return render_template('auktion.html')
    return render_template('auktion.html')


@app.route("/loppis", methods=['GET', 'POST'])
@admin_required
def flea_market():
    """
    Handels the sale of posts at the fixed price table / fleamarket. Updates the sold post with the price and the sale type
    :return:
    """
    post_ids = request.form.getlist('post_id')
    prices = request.form.getlist('price')
    print(post_ids)
    print(prices)
    sold_items = zip(post_ids, prices)
    sale_type = "fasta bordet"

    conn = sqlite3.connect(DATABASE)
    with conn:
        cur = conn.cursor()
        for post_id, price in sold_items:
            cur.execute("UPDATE Posts SET sold_price=?, sold_on=?, time_stamp_sold=? WHERE obj_id=?", (price, sale_type, time.strftime("%Y-%m-%d %H:%M:%S"), post_id))
            flash("Post {} registrerad som såld för {} kronor.".format(post_id, price))

    return render_template('flea_market.html')


@app.route("/create_event", methods=['GET', 'POST'])
def create_event():
    """
    Empties the database and inserts the information for the new event and an admin user.
    :return:
    """
    if request.method == 'POST':

        hosting_association = request.form['hosting_association']
        hosting_association_abrv = request.form['hosting_association_abrv']
        city = request.form['city']
        event_name = request.form['event_name']
        date = request.form['date']
        year = date[:4]
        commission = float(request.form['commission']) / 100
        event_description = request.form['event_description']

        admin_name = request.form['admin_name']
        admin_address = request.form['admin_address']
        admin_email = request.form['admin_email']
        admin_phone = request.form['admin_phone']
        admin_aquarium_club = request.form['admin_aquarium_club']
        admin_password = request.form['admin_password']
        admin_accept_cookies = "no"
        if request.form.get('cookies'):
            admin_accept_cookies = "yes"
        admin_accept_database = "no"
        if request.form.get('database'):
            admin_accept_database = "yes"

        salt = bcrypt.gensalt()
        encrypted_password = bcrypt.hashpw(admin_password.encode("utf-8"), salt)
        admin_data = [admin_name, admin_address, admin_email, admin_phone, admin_aquarium_club, "yes", encrypted_password, time.strftime("%Y-%m-%d %H:%M:%S"), admin_accept_cookies, admin_accept_database]

        conn = sqlite3.connect("auktion.db3")
        with conn:
            cur = conn.cursor()

            cur.execute("DROP TABLE IF EXISTS sellers")
            cur.execute("DROP TABLE IF EXISTS posts")
            cur.execute("DROP TABLE IF EXISTS types")
            cur.execute("DROP TABLE IF EXISTS auction_info")

            cur.execute('CREATE TABLE auction_info (type_id INTEGER PRIMARY KEY, hosting_association TEXT, hosting_association_abrv TEXT, city TEXT, event_name TEXT, year TEXT, date TEXT, commission INT, description TEXT)')
            cur.execute('CREATE TABLE sellers (seller_id INTEGER PRIMARY KEY, name TEXT TEXT, address TEXT, email TEXT, phone TEXT, aquarium_club TEXT, password TEXT, isAdmin TEXT, time_stamp TEXT, accepts_cookies TEXT, accepts_database TEXT)')
            cur.execute('CREATE TABLE posts (obj_id INTEGER PRIMARY KEY, seller_id INTEGER, scientific_name TEXT, plain_name TEXT, description TEXT, type TEXT, minimum_price FLOAT, fixed_price FLOAT, sold_price FLOAT, sold_on TEXT, time_stamp_registration TEXT, time_stamp_sold TEXT)')
            cur.execute('CREATE TABLE types (type_id INTEGER PRIMARY KEY, description TEXT, sale_type TEXT)')

            auction_info = [hosting_association, hosting_association_abrv, city, event_name, year, date, commission, event_description]
            cur.execute("INSERT INTO auction_info (hosting_association, hosting_association_abrv, city, event_name, year, date, commission, description) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", auction_info)

            types = (
                (1, u"Fisk till auktionen", u"auction"),
                (2, u"Fisk till fasta bordet", u"fixed_price"),
                (3, u"Räkor till auktionen", u"auction"),
                (4, u"Räkor till fasta bordet", u"fixed_price"),
                (5, u"Övriga djur till fasta bordet", u"fixed_price"),
                (6, u"Växter till auktionen", u"auction"),
                (7, u"Växter till fasta bordet", u"fixed_price"),
                (8, u"Tillbehör till fasta bordet", u"fixed_price"),
                (9, u"Övrigt till fasta bordet", u"fixed_price"))
            cur.executemany("INSERT INTO types (type_id, description, sale_type) VALUES(?, ?, ?)", types)

            cur.execute("INSERT INTO sellers (name, address, email, phone, aquarium_club, isAdmin, password, time_stamp, accepts_cookies, accepts_database) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", admin_data)
            conn.commit()

            flash("Ny databas skapad.")
        return render_template('create_event.html')
    else:
        return render_template('create_event.html')


@app.route('/about')
def about():
    """
    About page
    :return:
    """
    return render_template('about.html', version=VERSION)


@app.route('/download_database')
@admin_required
def download_database():
    """
    Download database page
    :return:
    """
    return render_template('download_database.html')


@app.route('/get_database/')
@admin_required
def get_database():
    try:
        filename = os.path.join(app.root_path, "auktion.db3")
        print(filename)
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return str(e)

# *** JSON *** #


@app.route('/json_get_type/<type_nr>')
def json_get_type(type_nr):
    """
    Returns the type for a type_id as a jsonobject. Useful for javascript to know if a sell type is an auction or a fixed price
    :param type_nr: id of seller type
    :return: a json object
    """
    conn = sqlite3.connect(DATABASE)
    with conn:
        cur = conn.cursor()
        cur.execute(""" SELECT sale_type FROM types WHERE type_id=?""", (type_nr,))

        columns = [d[0] for d in cur.description]
        sql_result = cur.fetchall()

        if sql_result:
            result = [dict(zip(columns, row)) for row in sql_result]
            return jsonify(result[0])
        else:
            return jsonify({"error": "id not found"})


@app.route('/json/<post_id>')
def get_json(post_id):
    """
    Returns post data as a jsonobject.
    Used by the auction and fleamarket pages to fetch information about the current post
    :param post_id: id for post to retrun
    :return: json object
    """
    conn = sqlite3.connect(DATABASE)
    with conn:
        cur = conn.cursor()

        cur.execute(""" SELECT posts.obj_id, sellers.name, posts.description, posts.scientific_name, posts.plain_name, posts.sold_on, posts.fixed_price, posts.sold_price, types.sale_type as type, posts.minimum_price
        FROM sellers
        INNER JOIN posts
        ON sellers.seller_id=posts.seller_id
            INNER JOIN types
            ON posts.type=types.type_id
        WHERE posts.obj_id=? """, (post_id,))

        columns = [d[0] for d in cur.description]
        sql_result = cur.fetchall()

        if sql_result:
            result = [dict(zip(columns, row)) for row in sql_result]
            return jsonify(result[0])
        else:

            return jsonify({"error": "id not found"})


@app.route('/json_get_sell_types')
def json_get_sell_types():
    """
    Returns the type for a type_id as a jsonobject. Useful for javascript to know if a sell type is an auction or a fixed price
    :return: a json object
    """
    conn = sqlite3.connect(DATABASE)
    with conn:
        cur = conn.cursor()
        cur.execute(""" SELECT type_id, description, sale_type FROM types""")

        columns = [d[0] for d in cur.description]
        sql_result = cur.fetchall()

        if sql_result:
            result = [dict(zip(columns, row)) for row in sql_result]
            return jsonify(result)
        else:
            return jsonify({"error": "id not found"})

# *** PDF Generation *** #


@app.route('/lables')
@app.route('/lables/<selected_id>')
@admin_required
def labels_view(selected_id=None):
    """
    Generates a downloadable pdf of lables
    :param selected_id: selected seller id or None for all sellers
    :return: pdf response
    """
    pdf = get_labels_pdf(selected_id)

    response = make_response(pdf)
    response.headers['Content-Disposition'] = "attachment; filename=labels.pdf"
    response.mimetype = 'application/pdf'
    return response


@app.route('/labels_print')
@app.route('/labels_print/<selected_id>')
@admin_required
def labels_server_print(selected_id=None):
    """
    Writes the receipt pdf on a printer connected to the server via CUPS
    :param selected_id: selected seller id or None for all sellers
    :return: Nothing
    """
    pdf = get_labels_pdf(selected_id)
    pdf_temp = "temp_pdf.pdf"
    f = open(pdf_temp, "w")
    f.write(pdf)
    f.close()
    # cups_printer = "Samsung_ML-331x_Series"
    # os.system('lp -d {} {}'.format(cups_printer, pdf_temp))
    os.system('lp {}'.format(pdf_temp))
    os.unlink(pdf_temp)
    return '', 204  # empty response


def get_labels_pdf(selected_id=None):
    """
    Generates a pdf with all the sellers labels or the labels for one seller identified by the seller id
    :param selected_id:
    :return: a pdf as a cStringIO object
    """
    conn = sqlite3.connect(DATABASE)
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT event_name, date from auction_info")
        auction_info = cur.fetchone()
        auction_name = auction_info[0]
        auction_date = auction_info[1]
        # print(auction_name, auction_date, int(selected_id))
        labels = zlabels.ZLabels("mypdf", auction_name, auction_date)
        print("SELECT seller_id, name, phone, aquarium_club FROM sellers WHERE seller_id=?", [selected_id])
        if selected_id:
            cur.execute("SELECT seller_id, name, phone, aquarium_club FROM sellers WHERE seller_id=?", [selected_id])
        else:
            cur.execute("SELECT seller_id, name, phone, aquarium_club FROM sellers")
        sellers = cur.fetchall()
        data = []
        for seller in sellers:
            seller_id = seller[0]
            print(seller_id)
            cur.execute("SELECT obj_id, plain_name, scientific_name, fixed_price FROM posts WHERE seller_id=?", (seller_id,))
            posts = cur.fetchall()
            seller_data = [seller[0], seller[1], seller[2], seller[3]]
            post_data = []
            for post in posts:
                post_data.append([post[0], " ".join([post[1], post[2]]), post[3]])
            seller_data.append(post_data)
            data.append(seller_data)
        print(data)

    pdf = labels.make_pdf(data, border=False)
    return pdf


@app.route('/economic_report_view')
@admin_required
def economic_report_view(selected_id=None):
    """
    Generates a downloadable pdf of seller receipts
    :param selected_id: selected seller id or None for all sellers
    :return: pdf response
    """
    pdf = get_economic_report_pdf()

    response = make_response(pdf)
    response.headers['Content-Disposition'] = "attachment; filename=economic_report.pdf"
    response.mimetype = 'application/pdf'
    return response


@app.route('/economic_report_print')
@admin_required
def economic_report_server_print(selected_id=None):
    """
    Writes the compilation pdf on a printer connected to the server via CUPS
    :param selected_id: selected seller id or None for all sellers
    :return: Nothing
    """
    pdf = get_economic_report_pdf()
    pdf_temp = "temp_pdf.pdf"
    f = open(pdf_temp, "w")
    f.write(pdf)
    f.close()
    # cups_printer = "Samsung_ML-331x_Series"
    # os.system('lp -d {} {}'.format(cups_printer, pdf_temp))
    os.system('lp {}'.format(pdf_temp))
    os.unlink(pdf_temp)
    return '', 204  # empty response


def get_economic_report_pdf():
    """
    Generates a pdf of the economic report
    :return: a pdf as a cStringIO object
    """
    conn = sqlite3.connect(DATABASE)
    data = []
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT hosting_association, hosting_association_abrv, event_name, date, city, commission from auction_info")
        auction_info = cur.fetchone()
        club_name = auction_info[0]
        club_short_name = auction_info[1]
        event_name = auction_info[2]
        event_date = auction_info[3]
        event_city = auction_info[4]
        commision = auction_info[5]

        economic_pdf = make_economic_report_pdf.EconomicReport(event_name, club_name, club_short_name, event_date, event_city)

        cur.execute("SELECT DISTINCT seller_id, name, aquarium_club FROM sellers")
        sellers = cur.fetchall()

        for seller in sellers:
            seller_id = seller[0]
            seller_name = seller[1]
            club = seller[2]

            # Get sold total sum and count sold posts
            cur.execute("SELECT sum(sold_price), count(sold_price) FROM posts WHERE seller_id=? and sold_price>0", [seller_id])
            sold = cur.fetchone()
            try:
                tot_sold = int(sold[0])
            except TypeError:
                tot_sold = 0
            count_sold = sold[1]

            to_society = tot_sold * commision
            to_society = int(to_society + 0.5)
            to_seller = int(tot_sold - to_society)

            cur.execute("SELECT  count(*) FROM posts WHERE seller_id=?", [seller_id])
            tot_nr_posts = cur.fetchone()[0]

            cur.execute(""" Select posts.seller_id, posts.type, sum(posts.sold_price), posts.sold_on, types.description FROM posts
                            LEFT JOIN types on types.type_id=posts.type
                            WHERE posts.seller_id=?  and sold_price>0
                            GROUP BY type, sold_on
                            ORDER BY posts.sold_on ASC""", [seller_id])
            sold_stats = cur.fetchall()

            sold_stat_data = [['Kategori', 'Summa', 'Sålt på']]
            if sold_stats:
                for sold_stat in sold_stats:
                    print(sold_stat[0], sold_stat[1], sold_stat[2], sold_stat[3], sold_stat[4])
                    sold_stat_data.append([sold_stat[4], int(sold_stat[2]), sold_stat[3], ""])
            else:
                sold_stat_data.append(["", "", "", ""])

            data.append([seller_id, seller_name, club, tot_sold, to_society, to_seller, tot_nr_posts, count_sold, sold_stat_data])

        # Summation for the whole auction and flea market
        # GEt the total number of registered posts and for auction and fleamarket
        cur.execute(""" SELECT types.sale_type, count(posts.obj_id) as antal FROM posts
                        LEFT JOIN types
                        ON posts.type=types.type_id
                        GROUP BY types.sale_type
                    """)
        res = cur.fetchall()
        tot_nr_posts = 0
        stat = {}
        for row in res:
            tot_nr_posts += row[1]
            key = ""
            if row[0] == "auction":
                key = "auktion"
            elif row[0] == "fixed_price":
                key = "fasta bordet"
            stat[key] = row[1]

        # Get total sum and number of sales per auction or fleamarket
        cur.execute("SELECT sum(sold_price), count(sold_price), sold_on FROM posts WHERE sold_price>0 GROUP BY sold_on")
        res2 = cur.fetchall()
        tot_sold_sum = 0

        tot_nr_sold_posts = 0
        tot_data_type = [[u"Sålt på", u"Antal inlämnade poster", u"Antal sålda poster", u"Summa"]]

        for row in res2:
            tot_sold_sum += row[0]
            tot_nr_sold_posts += row[1]

            print("key {}".format(stat[key]))
            print([row[2], stat[key], row[1], row[0]])
            tot_data_type.append([row[2], stat[row[2]], row[1], int(row[0])])

        tot_sold_sum = int(tot_sold_sum)
        tot_commision = tot_sold_sum * commision
        tot_commision = int(tot_commision + 0.5)
        netto = int(tot_sold_sum - tot_commision)

        tot_data = [tot_sold_sum, tot_commision, netto, tot_nr_posts, tot_nr_sold_posts, tot_data_type]

    pdf = economic_pdf.make_pdf(data, tot_data)
    return pdf


@app.route('/wall_list_view')
@admin_required
def wall_list_view():
    """
    Generates a pdf with all aucktion posts, renders as pdf
    :return: pdf
    """
    pdf = get_auction_wall_list()

    response = make_response(pdf)
    response.headers['Content-Disposition'] = "attachment; filename=wall_list.pdf"
    response.mimetype = 'application/pdf'
    return response


@app.route('/wall_list_print')
@admin_required
def wall_list_server_print():
    """
    Writes the wall list pdf on a printer connected to the server via CUPS
    :return: Nothing
    """
    pdf = get_auction_wall_list()
    pdf_temp = "temp_pdf.pdf"
    f = open(pdf_temp, "w")
    f.write(pdf)
    f.close()
    # cups_printer = "Samsung_ML-331x_Series"
    # os.system('lp -d {} {}'.format(cups_printer, pdf_temp))
    os.system('lp {}'.format(pdf_temp))
    os.unlink(pdf_temp)
    return '', 204  # empty response


def get_auction_wall_list():
    """
    Creates a pdf with all the auction objects for printing
    :return: a pdf
    """
    conn = sqlite3.connect(DATABASE)

    with conn:
        club_name, club_short_name, event_name, event_date, event_city, commision = get_auction_info()

        cur = conn.cursor()
        sql = """Select posts.obj_id, posts.scientific_name, posts.plain_name, posts.minimum_price from posts
                 join types on types.type_id=posts.type
                 where types.sale_type='auction' """
        cur.execute(sql)
        my_headings = [("Post", "Vetenskapligt namn", "Populärnamn", "Min pris")]
        my_data = cur.fetchall()
        cur.execute(sql)
        my_headings.extend(my_data)  # Add headings to list of auction objects

        m_w_l = make_wall_list_pdf.MakeWallList(club_name, event_name, event_date, event_city)
        pdf = m_w_l.make_pdf(my_headings)
        return pdf


@app.route('/compilation_view')
@app.route('/compilation_view/<selected_id>')
@admin_required
def compilation_view(selected_id=None):
    """
    Generates a downloadable pdf of seller receipts
    :param selected_id: selected seller id or None for all sellers
    :return: pdf response
    """
    pdf = get_compilation_pdf(selected_id)

    response = make_response(pdf)
    response.headers['Content-Disposition'] = "attachment; filename=result.pdf"
    response.mimetype = 'application/pdf'
    return response


@app.route('/compilation_print')
@app.route('/compilation_print/<selected_id>')
@admin_required
def compilation_server_print(selected_id=None):
    """
    Writes the compilation pdf on a printer connected to the server via CUPS
    :param selected_id: selected seller id or None for all sellers
    :return: Nothing
    """
    pdf = get_compilation_pdf(selected_id)
    pdf_temp = "temp_pdf.pdf"
    f = open(pdf_temp, "w")
    f.write(pdf)
    f.close()
    # cups_printer = "Samsung_ML-331x_Series"
    # os.system('lp -d {} {}'.format(cups_printer, pdf_temp))
    os.system('lp {}'.format(pdf_temp))
    os.unlink(pdf_temp)
    return '', 204  # empty response


def get_compilation_pdf(selected_id=None):
    """
    Generates a pdf with a compilation of the sales for each seller or for a singels seller identified by the seller id.
    :param selected_id:
    :return: a pdf as a cStringIO object
    """
    conn = sqlite3.connect(DATABASE)
    data = []
    with conn:
        cur = conn.cursor()
        club_name, club_short_name, event_name, event_date, event_city, commision = get_auction_info()
        comp_pdf = make_compilation_pdf.Compilation(club_name, event_name, event_date, event_city, commision)

        cur.execute("SELECT DISTINCT seller_id FROM posts WHERE sold_price > 0")
        seller_ids = cur.fetchall()

        for seller_id in seller_ids:
            seller_id = seller_id[0]
            cur.execute("SELECT name FROM sellers WHERE seller_id=?", [seller_id])
            names = cur.fetchone()
            seller_name = " ".join(names)
            # Get sold total sum
            cur.execute("SELECT sum(sold_price) FROM posts WHERE seller_id=? and sold_price>0", [seller_id])
            sold_for = cur.fetchone()[0]

            cur.execute("SELECT posts.obj_id, types.description, (posts.plain_name || ' ' || posts.scientific_name) as name , posts.sold_price, posts.sold_on FROM posts INNER JOIN types on posts.type=types.type_id WHERE posts.seller_id = ? and posts.sold_price>0", [seller_id])
            res = cur.fetchall()
            data_posts = [[u'Post', u'Typ', u'Namn', u'Pris', u'Såld']]
            for posts in res:
                data_posts.append([posts[0], posts[1], posts[2], int(posts[3]), posts[4]])
            data.append([seller_id, seller_name, sold_for, data_posts])

        print(data)

    pdf = comp_pdf.make_pdf(data)
    return pdf


@app.route('/receipt')
@app.route('/receipt/<selected_id>')
@admin_required
def receipt_view(selected_id=None):
    """
    Generates a downloadable pdf of seller receipts
    :param selected_id: selected seller id or None for all sellers
    :return: pdf response
    """
    pdf = get_receipt_pdf(selected_id)

    response = make_response(pdf)
    response.headers['Content-Disposition'] = "attachment; filename=receipt.pdf"
    response.mimetype = 'application/pdf'
    return response


@app.route('/receipt_print')
@app.route('/receipt_print/<selected_id>')
@admin_required
def receipt_server_print(selected_id=None):
    """
    Writes the receipt pdf on a printer connected to the server via CUPS
    :param selected_id: selected seller id or None for all sellers
    :return: Nothing
    """
    pdf = get_receipt_pdf(selected_id)
    pdf_temp = "temp_pdf.pdf"
    f = open(pdf_temp, "w")
    f.write(pdf)
    f.close()
    # cups_printer = "Samsung_ML-331x_Series"
    # os.system('lp -d {} {}'.format(cups_printer, pdf_temp))
    os.system('lp {}'.format(pdf_temp))
    os.unlink(pdf_temp)
    return '', 204  # empty response


def get_receipt_pdf(selected_id=None):
    """
    Generates a receipt pdf for one or all sellers.
    :param selected_id: id of selected seller or none for all
    :return: a pdf as a cStringIO object
    """
    conn = sqlite3.connect(DATABASE)
    data = []
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT hosting_association, hosting_association_abrv, city, event_name, year, date from auction_info")
        auction_info = cur.fetchone()
        hosting_association = auction_info[0]
        hosting_association_abrv = auction_info[1]
        city = auction_info[2]
        event_name = auction_info[3]
        # year = auction_info[4]
        auction_date = auction_info[5]

        receipt_pdf = make_receipt_pdf.Receipt(event_name, hosting_association, hosting_association_abrv, auction_date, city)

        if selected_id:
            seller_ids = [selected_id]
        else:
            cur.execute("SELECT DISTINCT seller_id FROM posts ORDER BY seller_id")
            seller_ids = cur.fetchall()

        for seller_id in seller_ids:
            seller_id = seller_id[0]
            cur.execute("SELECT name, address, email, phone, aquarium_club FROM sellers WHERE seller_id=?", [seller_id])
            result = cur.fetchone()
            seller_name = result[0]
            # seller_address = result[1]
            # seller_email = result[2]
            seller_phone = result[3]
            seller_club = result[4]
            cur.execute("SELECT obj_id  FROM posts WHERE seller_id = ? ORDER BY obj_id", [seller_id])
            res = cur.fetchall()
            post_ids = []
            for posts in res:
                post_ids.append(posts[0])
            nr_posts = len(post_ids)
            shorter = list_shorter.ListShorter()
            post_ids = shorter.short(post_ids)
            data.append([seller_id, seller_name, seller_club, seller_phone, nr_posts, post_ids])

    pdf = receipt_pdf.make_pdf(data)
    return pdf


# *** User handling *** #


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login of user
    :return:
    """
    if request.method == 'POST':
        logout_user()
        username = request.form['username'].strip().lower()
        password = request.form['password'].strip()

        authed_user = auth(username, password)
        if authed_user:
            login_user(authed_user)
            flash('Inloggad.')
            return redirect(url_for('index'))
        else:
            return abort(401)
    else:
        return render_template('login.html')


@app.route("/logout", methods=["GET"])
@login_required
def logout():
    """
    Logout a user
    :return:
    """
    logout_user()
    return redirect(url_for('index'))

# *** ERROR handling *** #


@app.errorhandler(404)
def page_not_found(error):
    """
    Route for non existing pages
    """
    print(error)
    return render_template('page_not_found.html'), 404


@app.errorhandler(401)
def page_not_found(error):
    """
    Page not found
    :param error:
    :return:
    """
    print(error)
    return render_template('login_failed.html'), 401

if __name__ == '__main__':
    app.run(debug=True)
