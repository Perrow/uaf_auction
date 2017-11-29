# coding=utf-8

import os
import sqlite3
import time
import datetime
import subprocess
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


__author__ = 'Kristian Persson'

app = Flask(__name__)
app.config.from_pyfile('config.cfg')
DATABASE = app.config['DATABASE']
VERSION = "0.63"

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
    :param username: username same as email
    :param password: users password
    :return:
    """
    conn = sqlite3.connect(DATABASE)
    with conn:
        cur = conn.cursor()
        # cur.execute("SELECT id FROM users WHERE email=? and password=?", (username, password))
        cur.execute("SELECT seller_id, password FROM sellers WHERE email=? ", (username.lower(), ))
        result = cur.fetchone()
        if result:  # email is in database, check that password is correct
            if bcrypt.checkpw(password.encode('utf8'), result[1]):
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
                cur.execute("INSERT INTO posts (seller_id, scientific_name, plain_name, description, type, minimum_price, fixed_price, time_stamp_registration, label_printed) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", (seller_id, scientific_name, plain_name, description, post_type, minimum_price, fixed_price, time.strftime("%Y-%m-%d %H:%M:%S"), "no"))

            flash("Posterna registrerade.")

    # Fetch sale types from database, generate a select for the default sale type
    conn = sqlite3.connect(DATABASE)
    select = '<select class="selectpicker form-control" id="master_type" name="master_type">'
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT type_id, description FROM used_types ORDER BY type_id")
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
                if scientific_name == "" and plain_name == "":
                    pass
                else:
                    cur.execute("INSERT INTO posts (seller_id, scientific_name, plain_name, description, type, minimum_price, fixed_price, time_stamp_registration, label_printed) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", (seller_id, scientific_name, plain_name, description, post_type, minimum_price, fixed_price, time.strftime("%Y-%m-%d %H:%M:%S"), "no"))

            flash("Posterna registrerade.")

    # Fetch sale types from database, generate a select for the default sale type
    conn = sqlite3.connect(DATABASE)
    select = '<select  class="selectpicker form-control" id="master_type" name="master_type">'
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT type_id, description FROM used_types ORDER BY type_id")
        result = cur.fetchall()
        for row in result:
            tempstr = '<option value="{}">{}</option>'.format(row[0], row[1])
            select += tempstr
    select += '</select>'
    return render_template('register_many_posts.html', select=select, registration_open=is_registration_open())


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
        cur.execute("SELECT count(posts.type), used_types.sale_type from posts LEFT JOIN used_types ON posts.type = used_types.type_id group by used_types.sale_type")
        res = cur.fetchall()

        for row in res:
            if row[1] == "auction":
                nr_posts.append("Auktion: {}".format(row[0]))
            if row[1] == "fixed_price":
                nr_posts.append("Fastpris: {}".format(row[0]))

        cur.execute("""SELECT  posts.obj_id, posts.scientific_name, posts.plain_name, posts.description, used_types.description
        FROM posts
        INNER JOIN used_types
        ON posts.type=used_types.type_id""")
        result = cur.fetchall()
        return render_template('list_all_posts.html', heading="Anmälda poster", nr_posts=nr_posts, data=result)


@app.route('/list_my_posts')
@login_required
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
        cur.execute("SELECT  COUNT(*) FROM posts WHERE seller_id=?", [cur_id])
        res = cur.fetchone()
        nr_posts.append("Antal poster: {}".format(res[0]))
        cur.execute("SELECT COUNT(posts.type), used_types.sale_type from posts LEFT JOIN used_types ON posts.type = used_types.type_id WHERE seller_id = ? GROUP BY used_types.sale_type", [cur_id])
        res = cur.fetchall()

        for row in res:
            if row[1] == "auction":
                nr_posts.append("Auktion: {}".format(row[0]))
            if row[1] == "fixed_price":
                nr_posts.append("Fastpris: {}".format(row[0]))

        cur.execute("""SELECT  posts.obj_id, posts.scientific_name, posts.plain_name, posts.description, used_types.description
        FROM posts
        INNER JOIN used_types
        ON posts.type=used_types.type_id
        WHERE seller_id = ?""", [cur_id])
        result = cur.fetchall()
        return render_template('list_my_posts.html', heading="Mina anmälda poster", nr_posts=nr_posts, data=result, user=cur_id, registration_open=is_registration_open())


@app.route('/delete_post')
@app.route('/delete_post/<post_id>')
@login_required
def delete_post(post_id=None):
    """
    Deletes a post from the database
    """
    if is_registration_open():
        conn = sqlite3.connect(DATABASE)
        with conn:
            cur = conn.cursor()
            if post_id:
                # Check that the current user owns the post
                cur_id = current_user.get_id()
                check_user_sql = "SELECT seller_id FROM posts WHERE obj_id = ?"
                cur.execute(check_user_sql, [post_id])
                owner_id = str(cur.fetchone()[0])
                if cur_id == owner_id:
                    delete_posts_sql = "DELETE FROM posts WHERE obj_id=?"
                    cur.execute(delete_posts_sql, [post_id])
                else:
                    flash("Du har inte rättigheter att radera den posten.")
    else:
        flash("Registreringen är stängd.")
    return redirect(url_for('list_my_posts'))


@app.route('/edit_post', methods=['GET', 'POST'])
@app.route('/edit_post/<post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id=None):
    """
    Edits a post from the database
    """
    if not is_registration_open():
        flash("Registreringen är stängd.")
        return redirect(url_for('list_my_posts'))

    conn = sqlite3.connect(DATABASE)
    # post_id=94&master_type=1&sciname=Ceratophyllum+demersum&popname=Hornsärv&min_price=&fixed_price=90.0&description=hj&submit=Skicka

    if request.method == 'POST':
        post_id = request.form['post_id']
        post_type = request.form['master_type']
        sciname = request.form['sciname']
        popname = request.form['popname']
        min_price = request.form['min_price']
        fixed_price = request.form['fixed_price']
        description = request.form['description']
        print(post_type)
        print(sciname)
        print(popname)
        print(min_price)
        print(fixed_price)
        print(description)
        with conn:
            cur = conn.cursor()
            # Check that the current user owns the post
            cur_id = current_user.get_id()
            check_user_sql = "SELECT seller_id FROM posts WHERE obj_id = ?"
            cur.execute(check_user_sql, [post_id])
            owner_id = str(cur.fetchone()[0])
            if cur_id == owner_id:
                edit_posts_sql = "UPDATE posts SET scientific_name=?, plain_name=?, description=?, type=?, minimum_price=?, fixed_price=? WHERE obj_id=?; "
                cur.execute(edit_posts_sql, [sciname, popname, description, post_type, min_price, fixed_price, post_id])
                flash("Posten uppdaterad")
                return redirect(url_for('list_my_posts'))
            else:
                flash("Du har inte rättigheter att ändra på den posten.")
                return redirect(url_for('list_my_posts'))
    else:
        if post_id:

            with conn:
                cur = conn.cursor()
                # Check that the current user owns the post
                cur_id = current_user.get_id()
                check_user_sql = "SELECT seller_id FROM posts WHERE obj_id = ?"
                cur.execute(check_user_sql, [post_id])
                owner_id = str(cur.fetchone()[0])
                if cur_id == owner_id:
                    # Get the postdata
                    edit_posts_sql = 'SELECT obj_id, scientific_name, plain_name, description, type, COALESCE(minimum_price, ""), COALESCE(fixed_price, "") FROM posts WHERE obj_id=?'
                    cur.execute(edit_posts_sql, [post_id])
                    data = cur.fetchone()

                    # make the selectinput
                    cur_type = int(data[4])
                    cur.execute("SELECT type_id, description FROM used_types ORDER BY type_id")
                    result = cur.fetchall()
                    select = '<select  class="selectpicker form-control" id="master_type" name="master_type">'
                    for row in result:
                        if row[0] == cur_type:
                            selected = "selected"
                        else:
                            selected = ""
                        tempstr = '<option value="{}" {}>{}</option>'.format(row[0], selected, row[1])
                        select += tempstr
                    select += '</select>'

                    return render_template('edit_post.html', data=data, select=select)
                else:
                    flash("Du har inte rättigheter att ändra på den posten.")
                    return redirect(url_for('list_my_posts'))
        else:
            return redirect(url_for('list_my_posts'))


@app.route('/list_seller')
@admin_required
def list_seller():
    """
    Page for listing all sellers in the database
    """
    conn = sqlite3.connect(DATABASE)

    with conn:
        cur = conn.cursor()
        sql = """SELECT sellers.name, sellers.address, sellers.email, sellers.phone, sellers.aquarium_club, count(posts.obj_id) as num_posts, cast(sellers.seller_id as text), isAdmin FROM sellers
                 LEFT JOIN posts ON sellers.seller_id=posts.seller_id GROUP BY sellers.seller_id;"""
        cur.execute(sql)
        result = cur.fetchall()
    return render_template('list_seller.html', data=result)


@app.route('/delete_seller')
@app.route('/delete_seller/<seller_id>')
@admin_required
def delete_seller(seller_id=None):
    """
    Deletes a seller from the database
    """
    conn = sqlite3.connect(DATABASE)
    with conn:
        cur = conn.cursor()
        if seller_id:
            delete_seller_sql = "DELETE FROM sellers WHERE seller_id=?"
            cur.execute(delete_seller_sql, [seller_id])
            delete_posts_sql = "DELETE FROM posts WHERE seller_id=?"
            cur.execute(delete_posts_sql, [seller_id])
    return redirect(url_for('list_seller'))


@app.route('/make_admin')
@app.route('/make_admin/<seller_id>')
@admin_required
def make_admin(seller_id=None):
    """
    Makes a seller admin
    """
    conn = sqlite3.connect(DATABASE)
    with conn:
        cur = conn.cursor()
        if seller_id:
            make_admin_sql = "UPDATE sellers SET isAdmin = 'yes'  WHERE seller_id=?"
            cur.execute(make_admin_sql, [seller_id])
    return redirect(url_for('list_seller'))


@app.route('/demote_admin')
@app.route('/demote_admin/<seller_id>')
@admin_required
def demote_admin(seller_id=None):
    """
    Makes a admin basic seller
    """
    conn = sqlite3.connect(DATABASE)
    with conn:
        cur = conn.cursor()
        if seller_id:
            make_admin_sql = "UPDATE sellers SET isAdmin = 'no'  WHERE seller_id=?"
            cur.execute(make_admin_sql, seller_id)
    return redirect(url_for('list_seller'))


@app.route('/reports')
@admin_required
def reports():
    """
    Reports page
    :return:
    """
    return render_template('reports.html')


@app.route("/display_two", methods=['GET'])
@admin_required
def display_two():
    """
    A page for displaying current and next post on an projector or something
    """
    return render_template('display_two.html')


@app.route("/display_one", methods=['GET'])
@admin_required
def display_one():
    """
    A page for displaying current post on an projector or something
    """
    return render_template('display_one.html')


@app.route("/auktion", methods=['GET', 'POST'])
@admin_required
def auction():
    """
    Shows the auction form and updates the database with the price it sold for and the sale type
    :return:
    """
    conn = sqlite3.connect(DATABASE)
    if request.method == 'POST':
        post_id = request.form['post_id']
        price = request.form['price']
        sale_type = request.form['sale_type']
        with conn:
            cur = conn.cursor()
            if post_id != "":
                cur.execute("UPDATE Posts SET sold_price=?, sold_on=?, time_stamp_sold=? WHERE obj_id=?", (price, sale_type, time.strftime("%Y-%m-%d %H:%M:%S"), post_id))
                flash("Post {} registrerad som såld.".format(post_id))

    conn.close()
    sold_statistic = get_sold_statistic()
    return render_template('auktion.html', sold_statistic=sold_statistic)


@app.route("/loppis", methods=['GET', 'POST'])
@admin_required
def flea_market():
    """
    Handles the sale of posts at the fixed price table / fleamarket. Updates the sold post with the price and the sale type
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
            if post_id != "":
                cur.execute("UPDATE Posts SET sold_price=?, sold_on=?, time_stamp_sold=? WHERE obj_id=?", (price, sale_type, time.strftime("%Y-%m-%d %H:%M:%S"), post_id))
                flash("Post {} registrerad som såld för {} kronor.".format(post_id, price))

    conn.close()
    sold_statistic = get_sold_statistic()
    return render_template('flea_market.html', sold_statistic=sold_statistic)


@app.route("/create_event", methods=['GET', 'POST'])
@admin_required
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
        selected_types = request.form.getlist('type')
        print(request.form.getlist('type'))

        salt = bcrypt.gensalt()
        encrypted_password = bcrypt.hashpw(admin_password.encode("utf-8"), salt)
        admin_data = [admin_name, admin_address, admin_email, admin_phone, admin_aquarium_club, "yes", encrypted_password, time.strftime("%Y-%m-%d %H:%M:%S"), admin_accept_cookies, admin_accept_database]

        conn = sqlite3.connect(DATABASE)
        with conn:
            cur = conn.cursor()

            cur.execute("DROP TABLE IF EXISTS sellers")
            cur.execute("DROP TABLE IF EXISTS posts")
            cur.execute("DROP TABLE IF EXISTS used_types")
            cur.execute("DROP TABLE IF EXISTS auction_info")

            cur.execute('CREATE TABLE auction_info (type_id INTEGER PRIMARY KEY, hosting_association TEXT, hosting_association_abrv TEXT, city TEXT, event_name TEXT, year TEXT, date TEXT, commission INT, description TEXT)')
            cur.execute('CREATE TABLE sellers (seller_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT TEXT, address TEXT, email TEXT, phone TEXT, aquarium_club TEXT, password TEXT, isAdmin TEXT, time_stamp TEXT, accepts_cookies TEXT, accepts_database TEXT)')
            cur.execute('CREATE TABLE posts (obj_id INTEGER PRIMARY KEY AUTOINCREMENT, seller_id INTEGER, scientific_name TEXT, plain_name TEXT, description TEXT, type TEXT, minimum_price FLOAT, fixed_price FLOAT, sold_price FLOAT, sold_on TEXT, time_stamp_registration TEXT, time_stamp_sold TEXT, label_printed TEXT)')
            cur.execute('CREATE TABLE used_types (type_id INTEGER PRIMARY KEY, description TEXT, sale_type TEXT)')

            auction_info = [hosting_association, hosting_association_abrv, city, event_name, year, date, commission, event_description]
            cur.execute("INSERT INTO auction_info (hosting_association, hosting_association_abrv, city, event_name, year, date, commission, description) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", auction_info)

            # cur.execute("SELECT type_id, description, sale_type FROM all_types WHERE type_id=?", selected_types)
            print([",".join(selected_types)])
            sql = "SELECT type_id, description, sale_type FROM all_types WHERE type_id in ({})".format(", ".join(["?"] * len(selected_types)))
            print(sql)
            cur.execute(sql, selected_types)
            selected_types_data = cur.fetchall()
            print(selected_types_data)
            cur.executemany("INSERT INTO used_types (type_id, description, sale_type) VALUES(?, ?, ?)", selected_types_data)

            cur.execute("INSERT INTO sellers (name, address, email, phone, aquarium_club, isAdmin, password, time_stamp, accepts_cookies, accepts_database) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", admin_data)
            conn.commit()

            flash("Ny databas skapad.")
        return render_template('index.html')
    else:
        conn = sqlite3.connect(DATABASE)
        with conn:
            cur = conn.cursor()
            cur.execute(""" SELECT type_id, description FROM all_types""")
            all_types = cur.fetchall()
        return render_template('create_event.html', all_types=all_types)


@app.route("/edit_event", methods=['GET', 'POST'])
@admin_required
def edit_event():
    """
    Shows an prefilled form with the current info for the event
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

        selected_types = request.form.getlist('type')
        print(request.form.getlist('type'))

        conn = sqlite3.connect(DATABASE)
        with conn:
            cur = conn.cursor()
            cur.execute('DELETE FROM auction_info')
            auction_info = [hosting_association, hosting_association_abrv, city, event_name, year, date, commission, event_description]
            cur.execute("INSERT INTO auction_info (hosting_association, hosting_association_abrv, city, event_name, year, date, commission, description) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", auction_info)

            # cur.execute("SELECT type_id, description, sale_type FROM all_types WHERE type_id=?", selected_types)
            print([",".join(selected_types)])
            cur.execute('DELETE FROM used_types')
            sql = "SELECT type_id, description, sale_type FROM all_types WHERE type_id in ({})".format(", ".join(["?"] * len(selected_types)))
            print(sql)
            cur.execute(sql, selected_types)
            selected_types_data = cur.fetchall()
            print(selected_types_data)
            cur.executemany("INSERT INTO used_types (type_id, description, sale_type) VALUES(?, ?, ?)", selected_types_data)

            conn.commit()

            flash("Databasen uppdaterad.")
        return render_template('index.html')
    else:
        conn = sqlite3.connect(DATABASE)
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT type_id, description FROM all_types')
            all_types = cur.fetchall()
            cur.execute('SELECT type_id FROM used_types')
            used_types_tuples = cur.fetchall()
            used_types = [x[0] for x in used_types_tuples]
            print(used_types)
            cur.execute('SELECT hosting_association, hosting_association_abrv, city, event_name, date, commission, description FROM auction_info')
            auction_info = cur.fetchone()
        return render_template('edit_event.html', all_types=all_types, auction_info=auction_info, used_types=used_types)


@app.route('/about')
def about():
    """
    About page
    :return:
    """
    return render_template('about.html', version=VERSION)


def is_registration_open():
    """
    Checks if registration is open
    :return: True if open, False if closed.
    """
    conn = sqlite3.connect(DATABASE)
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT registration_open FROM auction_info")
        result = cur.fetchone()
        print(result)
        print("registration_open: ".format(result[0]))
        if result[0] == "yes":
            registration_open = True
        else:
            registration_open = False
    return registration_open


@app.route('/open_close_registration', methods=['GET', 'POST'])
@admin_required
def open_close_registration():
    """
    Open or close registration
    :return:
    """
    if request.method == 'POST':
        close_registration_button = request.form.get('close_registration_button', None)
        open_registration_button = request.form.get('open_registration_button', None)
        open_close = ""
        if close_registration_button is not None:
            flash("Föranmälan är: {}".format("stängd"))
            open_close = "no"
        if open_registration_button is not None:
            flash("Föranmälan är: {}".format("öppen"))
            open_close = "yes"
        conn = sqlite3.connect(DATABASE)
        with conn:
            cur = conn.cursor()
            cur.execute("UPDATE auction_info SET registration_open = ?", [open_close])
            conn.commit()

        return redirect(url_for('index'))
    else:
        return render_template('open_close_registration.html', registration_open=is_registration_open())


@app.route('/setup_printer', methods=['GET', 'POST'])
@admin_required
def setup_printer():
    """
    Setup printers
    :return:
    """
    if request.method == 'POST':
        # ?label_printer=Samsung_ML-331x_Series&paper_printer=HL1110
        label_printer = request.form['label_printer']
        paper_printer = request.form['paper_printer']
        printers = (
            ("label", label_printer),
            ("paper", paper_printer)
        )
        conn = sqlite3.connect(DATABASE)
        with conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM printers")
            cur.executemany("INSERT INTO printers (purpose, cups_name) VALUES (?, ?)", printers)

        flash("Etikettskrivare: {}".format(label_printer))
        flash("Pappersskrivare: {}".format(paper_printer))

        return redirect(url_for('setup_printer'))
    else:

        printers_found = False
        try:
            result = subprocess.run(['lpstat', '-a'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            all_printer_str = result.stdout.decode("utf-8")
            err_msg = result.stderr.decode("utf-8")

            print("stdout: {}".format(all_printer_str))
            print("error: {}".format(err_msg))

            all_printers_lst = str(all_printer_str).strip().split("\n")
            printer_names = []
            # Split words in each row and save the printer name
            if err_msg == "":
                for row in all_printers_lst:
                    words = row.split()
                    printer_names.append(words[0].strip())
                    printers_found = True
        except FileNotFoundError:
            print("Skrivar sytem CUPS är inte installerat. Inga skrivare hittades")
            printer_names = []
            printers_found = False
        # print(default_printer)
        print("Found printers: {}".format(printer_names))
        return render_template('setup_printer.html', printers=printer_names, printers_found=printers_found)


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
        filename = os.path.join(app.root_path, DATABASE)
        print(filename)
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return str(e)


@app.route('/plot_registration')
@admin_required
def plot_registration():
        """
        Plots a diagram showing the number of registations per day
        :return: webpage
        """
        conn = sqlite3.connect(DATABASE)
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT substr(time_stamp_registration, 0, 11) AS date, count(*)  FROM posts GROUP BY date  ORDER BY date ASC')
            res = cur.fetchall()

            first_date = datetime.datetime.strptime(res[0][0], "%Y-%m-%d").date() + datetime.timedelta(days=-1)
            last_date = datetime.datetime.strptime(res[-1][0], "%Y-%m-%d").date() + datetime.timedelta(days=1)

            # Compile plot data in csv format that are injected into the script part of the template
            plot_data = '"Datum,Antal\\n"+\n'
            plot_data += '"{},\\n"+\n'.format(first_date)  # Buffert to avoid half a bar
            for row in res:
                plot_data += '"{},{}\\n"+\n'.format(row[0], row[1])
            plot_data += '"{},\\n"+\n'.format(last_date)   # Buffert to avoid half a bar
            plot_data = plot_data[:-3] + '",'

        return render_template('plot_registration.html', plot_data=plot_data)


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
        cur.execute("SELECT sale_type FROM used_types WHERE type_id=?", (type_nr,))

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

        cur.execute(""" SELECT posts.obj_id, sellers.name, posts.description, posts.scientific_name, posts.plain_name, posts.sold_on, posts.fixed_price, posts.sold_price, used_types.sale_type as type, posts.minimum_price
        FROM sellers
        INNER JOIN posts
        ON sellers.seller_id=posts.seller_id
            INNER JOIN used_types
            ON posts.type=used_types.type_id
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
        cur.execute(""" SELECT type_id, description, sale_type FROM used_types""")

        columns = [d[0] for d in cur.description]
        sql_result = cur.fetchall()

        if sql_result:
            result = [dict(zip(columns, row)) for row in sql_result]
            return jsonify(result)
        else:
            return jsonify({"error": "id not found"})


@app.route('/json_sold')
def json_sold():
    """
    Json generation of nr of sold post at auction and fleamarket and total nr of posts, total auction and total fleamarket.
    """
    sold_stat = get_sold_statistic()
    sold_stat_dict = {"total": sold_stat[0], "total_auction": sold_stat[1], "sold_auction": sold_stat[2], "sold_auction_percent": sold_stat[3], "total_fleamarket": sold_stat[4], "sold_fleamarket": sold_stat[5], "sold_fleamarket_percent": sold_stat[6]}

    return jsonify(sold_stat_dict)


def get_sold_statistic():
    conn = sqlite3.connect(DATABASE)
    with conn:
        cur = conn.cursor()
        cur.execute("""SELECT "total_" || all_types.sale_type, count(posts.type) FROM posts
                      INNER JOIN all_types
                      ON posts.type=all_types.type_id
                      GROUP BY all_types.sale_type

                      UNION ALL

                      SELECT "sold_on_" || sold_on, count(sold_price) AS nr_sold FROM posts GROUP BY sold_on""")

        sql_result = cur.fetchall()
        total_auction = 0
        total_fleamarket = 0
        sold_auction = 0
        sold_fleamarket = 0
        for row in sql_result:
            if row[0] == "total_auction":
                total_auction = row[1]
            if row[0] == "sold_on_auktion":
                sold_auction = row[1]
            if row[0] == "total_fixed_price":
                total_fleamarket = row[1]
            if row[0] == "sold_on_fasta bordet":
                sold_fleamarket = row[1]
        total = total_auction + total_fleamarket
        if total_auction > 0:
            sold_auction_percent = sold_auction / float(total_auction) * 100
        else:
            sold_auction_percent = 0
        if total_fleamarket > 0:
            sold_fleamarket_percent = sold_fleamarket / float(total_fleamarket) * 100
        else:
            sold_fleamarket_percent = 0
        # result = {"total": total, "total_auction": total_auction, "sold_auction": sold_auction, "sold_auction_percent": sold_auction_percent, "total_fleamarket": total_fleamarket, "sold_fleamarket": sold_fleamarket, "sold_fleamarket_percent": sold_fleamarket_percent}
        result = [total, total_auction, sold_auction, sold_auction_percent, total_fleamarket, sold_fleamarket, sold_fleamarket_percent]
        return result


# *** PDF Generation *** #


@app.route('/reset_printed_labels')
@app.route('/reset_printed_labels/<selected_id>')
@admin_required
def reset_printed_labels(selected_id=None):
    """
    Writes the receipt pdf on a printer connected to the server via CUPS
    :param selected_id: selected seller id or None for all sellers
    :return: Nothing
    """
    conn = sqlite3.connect(DATABASE)
    with conn:
        cur = conn.cursor()
        if selected_id:
            reset_sql = 'UPDATE posts SET label_printed = "no" WHERE seller_id = ?'
            cur.execute(reset_sql, [selected_id])
            flash("Etiketter för säljare {} markerade som ej utskrivna".format(selected_id))
        else:
            reset_sql = 'UPDATE posts SET label_printed = "no"'
            cur.execute(reset_sql)
            flash('Alla etiketter markerade som ej utskrivna')
    # return '', 204  # empty response
    return redirect(request.referrer)


@app.route('/my_labels')
@app.route('/my_labels/<selected_id>')
@login_required
def my_labels(selected_id=None):
    """
    Generates a downloadable pdf of labels for the selected seller must be the current seller
    :param selected_id: user to produce labels for
    :return: pdf response
    """
    cur_id = current_user.get_id()
    if cur_id == selected_id:
        pdf = get_labels_pdf(selected_id)

        response = make_response(pdf)
        response.headers['Content-Disposition'] = "attachment; filename=labels.pdf"
        response.mimetype = 'application/pdf'
        return response
    else:
        flash("Du kan inte skriva ut andras etiketter")
        return redirect(url_for('list_my_posts'))


@app.route('/all_labels')
@app.route('/all_labels/<selected_id>')
@admin_required
def labels_view(selected_id=None):
    """
    Generates a downloadable pdf of labels
    :param selected_id: selected seller id or None for all sellers
    :return: pdf response
    """
    pdf = get_labels_pdf(selected_id)

    response = make_response(pdf)
    response.headers['Content-Disposition'] = "attachment; filename=labels.pdf"
    response.mimetype = 'application/pdf'
    return response


@app.route('/unprinted_labels')
@app.route('/unprinted_labels/<selected_id>')
@admin_required
def unprinted_labels(selected_id=None):
    """
    Generates a downloadable pdf of labels
    :param selected_id: selected seller id or None for all sellers
    :return: pdf response
    """
    pdf = get_labels_pdf(selected_id, only_printed=True)

    response = make_response(pdf)
    response.headers['Content-Disposition'] = "attachment; filename=labels.pdf"
    response.mimetype = 'application/pdf'
    return response


def server_print(pdf, printer="paper"):
    """
    Prints a pdf to the label printer
    :param pdf: pdf data to print
    :param printer: The printer to print on, can be paper of label
    :return:
    """
    # temporary save the pdf
    pdf_temp = "temp_pdf.pdf"
    f = open(pdf_temp, "wb")
    f.write(pdf)
    f.close()
    # get printer
    conn = sqlite3.connect(DATABASE)
    with conn:
        sql = 'SELECT cups_name FROM printers WHERE purpose=? '
        cur = conn.cursor()
        cur.execute(sql, [printer])
        cups_printer = cur.fetchone()[0]
        if cups_printer == "":  # No printer set
            os.system('lp {}'.format(pdf_temp))
        else:  # Name found
            os.system('lp -d {} {}'.format(cups_printer, pdf_temp))
    os.unlink(pdf_temp)


@app.route('/all_labels_print')
@app.route('/all_labels_print/<selected_id>')
@admin_required
def labels_server_print(selected_id=None):
    """
    Writes the receipt pdf on a printer connected to the server via CUPS
    :param selected_id: selected seller id or None for all sellers
    :return: Nothing
    """
    pdf = get_labels_pdf(selected_id, mark_printed=True)
    server_print(pdf, printer="label")
    return '', 204  # empty response


@app.route('/unprinted_labels_print')
@app.route('/unprinted_labels_print/<selected_id>')
@admin_required
def unprinted_labels_server_print(selected_id=None):
    """
    Writes the receipt pdf on a printer connected to the server via CUPS
    :param selected_id: selected seller id or None for all sellers
    :return: Nothing
    """
    pdf = get_labels_pdf(selected_id, only_printed=True, mark_printed=True)
    server_print(pdf, printer="label")
    return '', 204  # empty response


def get_labels_pdf(selected_id=None, only_printed=False, mark_printed=False):
    """
    Generates a pdf with all the sellers labels or the labels for one seller identified by the seller id
    :param selected_id: seller_id to print labels for
    :param only_printed: If true only print labels that is mot marked as printed in database
    :param mark_printed: If True then labels that are printed are marked as printed in the database
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
        if selected_id:
            cur.execute("SELECT seller_id, name, phone, aquarium_club FROM sellers WHERE seller_id=?", [selected_id])
        else:
            cur.execute("SELECT seller_id, name, phone, aquarium_club FROM sellers")
        sellers = cur.fetchall()
        data = []
        printed_labels = []
        for seller in sellers:
            seller_id = seller[0]
            if only_printed:
                cur.execute("""SELECT posts.obj_id, posts.plain_name, posts.scientific_name, posts.fixed_price, posts.minimum_price, all_types.sale_type, all_types.description FROM posts
                        INNER JOIN all_types ON posts.type = all_types.type_id
                        WHERE posts.seller_id=? and posts.label_printed='no'""", (seller_id,))
            else:
                cur.execute("""SELECT posts.obj_id, posts.plain_name, posts.scientific_name, posts.fixed_price, posts.minimum_price, all_types.sale_type, all_types.description FROM posts
                        INNER JOIN all_types ON posts.type = all_types.type_id
                        WHERE posts.seller_id=?""", (seller_id,))
            posts = cur.fetchall()
            seller_data = [seller[0], seller[1], seller[2], seller[3]]
            post_data = []
            for post in posts:
                printed_labels.append(str(post[0]))
                post_data.append([post[0], post[1], post[2], post[3], post[4], post[5]])
            seller_data.append(post_data)
            data.append(seller_data)
        if mark_printed:
            # Mark printed labels as printed in database
            update_sql = "UPDATE posts SET label_printed = 'yes'  WHERE obj_id IN({})".format(", ".join(printed_labels))
            print(update_sql)
            cur.execute(update_sql)
            conn.commit()

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
    server_print(pdf, printer="paper")
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

            cur.execute(""" Select posts.seller_id, posts.type, sum(posts.sold_price), posts.sold_on, used_types.description FROM posts
                            LEFT JOIN used_types on used_types.type_id=posts.type
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
        cur.execute(""" SELECT used_types.sale_type, count(posts.obj_id) as antal FROM posts
                        LEFT JOIN used_types
                        ON posts.type=used_types.type_id
                        GROUP BY used_types.sale_type
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
    server_print(pdf, printer="paper")
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
                 join used_types on used_types.type_id=posts.type
                 where used_types.sale_type='auction' """
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
    server_print(pdf, printer="paper")
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

        # cur.execute("SELECT DISTINCT seller_id FROM posts WHERE sold_price > 0")
        # seller_ids = cur.fetchall()
        cur.execute("SELECT DISTINCT seller_id FROM sellers")
        seller_ids = cur.fetchall()

        for seller_id in seller_ids:
            seller_id = seller_id[0]
            cur.execute("SELECT name FROM sellers WHERE seller_id=?", [seller_id])
            names = cur.fetchone()
            seller_name = " ".join(names)
            # Get sold total sum
            cur.execute("SELECT sum(sold_price) FROM posts WHERE seller_id=? and sold_price>0", [seller_id])
            sold_for = cur.fetchone()[0]

            cur.execute("SELECT posts.obj_id, used_types.description, (posts.plain_name || ' ' || posts.scientific_name) as name , posts.sold_price, posts.sold_on FROM posts INNER JOIN used_types on posts.type=used_types.type_id WHERE posts.seller_id = ? and posts.sold_price>0", [seller_id])
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
    server_print(pdf, printer="paper")
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
        seller_ids = []
        if selected_id:
            seller_ids = [[selected_id]]
        else:
            cur.execute("SELECT DISTINCT seller_id FROM posts ORDER BY seller_id")
            seller_ids = cur.fetchall()

        for seller_id in seller_ids:
            print("Seller_id: {}".format(seller_id))
            cur.execute("SELECT name, address, email, phone, aquarium_club FROM sellers WHERE seller_id=?", seller_id)
            result = cur.fetchone()
            seller_name = result[0]
            # seller_address = result[1]
            # seller_email = result[2]
            seller_phone = result[3]
            seller_club = result[4]
            cur.execute("SELECT obj_id  FROM posts WHERE seller_id = ? ORDER BY obj_id", seller_id)
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
