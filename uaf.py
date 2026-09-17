# coding=utf-8

import os
import sys
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
import smtplib
from email.mime.text import MIMEText
###
import user_model
import zlabels
import label_preview
import make_compilation_pdf
import make_receipt_pdf
import list_shorter
import make_economic_report_pdf
import make_wall_list_pdf
import make_clerk_receipt_pdf


__author__ = 'Kristian Persson'

app = Flask(__name__)
app.config.from_pyfile('config.cfg')
DATABASE = app.config['DATABASE']
GMAILUSER = app.config['GMAILUSER']
GMAILPASSWORD = app.config['GMAILPASSWORD']
label_preview.register_routes(app)

VERSION = "0.85"

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


def get_email_notification_address():
    """
    Fetch the notification email address from the database
    :return: str with the email address
    """
    conn = sqlite3.connect(DATABASE)

    with conn:
        cur = conn.cursor()
        cur.execute("SELECT email FROM notification_email")
        email = cur.fetchone()
        if email:
            return email[0]
        else:
            return ""


def send_email(subject, message):
    """
    Sends an email message via gmail account
    :param subject: email subject
    :param message: email message
    """
    send_to = get_email_notification_address()
    if send_to != "":
        msg = MIMEText(message)
        msg['Subject'] = subject
        msg['From'] = GMAILUSER
        msg['To'] = send_to
        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.ehlo()
            server.login(GMAILUSER, GMAILPASSWORD)
            server.sendmail(GMAILUSER, send_to, msg.as_bytes())
            server.close()
        except:
            e = sys.exc_info()[0]
            print("Failed to send notification email\n{}".format(e))


def get_auction_info():
    """
    Extract the auction info from the database
    :return: club_name, club_short_name, event_name, event_date, event_city, commision
    """
    conn = sqlite3.connect(DATABASE)

    with conn:
        cur = conn.cursor()
        cur.execute("SELECT hosting_association, hosting_association_abrv, event_name, date, city, commission FROM auction_info")
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


@app.route('/edit_password', methods=['GET', 'POST'])
@app.route('/edit_password/<seller_id>', methods=['GET', 'POST'])
@admin_required
def edit_password(seller_id=None):
    if request.method == 'POST':
        seller_id = request.form['seller_id'].strip().lower()
        password = request.form['password'].strip().encode('utf-8')
        salt = bcrypt.gensalt()
        encrypted_password = bcrypt.hashpw(password, salt)
        con = sqlite3.connect(DATABASE)
        with con:
            cur = con.cursor()
            sql = 'UPDATE sellers SET password = ? WHERE seller_id = ?'
            cur.execute(sql, [encrypted_password, seller_id])
            flash("Nytt lösenord för säljare: {} sparat.".format(seller_id))
        return redirect(url_for('list_seller_actions'))
    else:
        con = sqlite3.connect(DATABASE)
        with con:
            cur = con.cursor()
            cur.execute('SELECT sellers.name FROM sellers WHERE sellers.seller_id = ?', [seller_id])
            sellers = cur.fetchone()
            if sellers:
                return render_template('edit_password.html', seller_id=seller_id, name=sellers[0])
            else:
                flash("Användaren hittades inte.")
                return redirect(url_for('list_seller_actions'))


@app.route('/register_seller', methods=['GET', 'POST'])
def register_seller():
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
        has_checked_in = "no"

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
                seller_data = [name, address, email, phone, aquarium_club, encrypted_password, "no", time.strftime("%Y-%m-%d %H:%M:%S"), accept_cookies, accept_database, has_checked_in]
                cur.execute("INSERT INTO sellers (name, address, email, phone, aquarium_club, password, isAdmin, time_stamp, accepts_cookies, accepts_database, has_checked_in) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", seller_data)

                flash("Användare {} skapad.".format(name))
                send_email("uaf_auction: new seller registered", 'Seller {} with email: {} created.'.format(name, email))
            authed_user = auth(email, password)
            if authed_user:
                login_user(authed_user)

            return redirect(url_for('index'))
    else:
        return render_template('register_seller.html', registration_open=is_registration_open())


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
                cur.execute("INSERT INTO posts (seller_id, scientific_name, plain_name, description, type, minimum_price, fixed_price, time_stamp_registration, label_printed, is_checked_in, is_closed) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (seller_id, scientific_name, plain_name, description, post_type, minimum_price, fixed_price, time.strftime("%Y-%m-%d %H:%M:%S"), "no", "no", "no"))

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
        cur.execute('SELECT seller_id, sellers.seller_id || " - " || sellers.name FROM sellers')
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
        types = request.form.getlist('type')
        scinames = request.form.getlist('sciname')
        popnames = request.form.getlist('popname')
        min_prices = request.form.getlist('min_price')
        fixed_prices = request.form.getlist('fixed_price')
        descriptions = request.form.getlist('description')

        new_items = zip(scinames, popnames, descriptions, types, min_prices, fixed_prices)

        seller_id = current_user.get_id()
        conn = sqlite3.connect(DATABASE)
        nr_posts = 0
        with conn:
            cur = conn.cursor()
            for scientific_name, plain_name, description, post_type, minimum_price, fixed_price in new_items:
                if scientific_name == "" and plain_name == "":
                    pass
                else:
                    nr_posts += 1
                    cur.execute("INSERT INTO posts (seller_id, scientific_name, plain_name,  description, type, minimum_price, fixed_price, time_stamp_registration, label_printed, is_checked_in, is_closed) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (seller_id, scientific_name, plain_name, description, post_type, minimum_price, fixed_price, time.strftime("%Y-%m-%d %H:%M:%S"), "no", "no", "no"))

            flash("{} poster registrerade.".format(nr_posts))
            send_email("uaf_auction: posts registered", 'Seller no {} registered {} posts.\n {}\n {}'.format(seller_id, nr_posts, scinames, popnames))

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

        cur.execute("""SELECT  posts.obj_id, posts.scientific_name, posts.plain_name, posts.minimum_price, fixed_price, posts.description, used_types.description
        FROM posts
        INNER JOIN used_types
        ON posts.type=used_types.type_id
        WHERE seller_id = ?""", [cur_id])
        result = cur.fetchall()
        return render_template('list_my_posts.html', heading="Mina anmälda poster", nr_posts=nr_posts, data=result, user=cur_id, registration_open=is_registration_open(), print_labels=True)

@app.route('/list_seller_posts')
@app.route('/list_seller_posts/<seller_id>')
@admin_required
def list_seller_posts(seller_id=None):
    if seller_id == None:
        print("ingen säljar id")
        return
    conn = sqlite3.connect(DATABASE)
    with conn:
        cur = conn.cursor()
        print("seller id", seller_id)
        nr_posts = []
        cur.execute("SELECT  COUNT(*) FROM posts WHERE seller_id=?", [seller_id])
        res = cur.fetchone()
        nr_posts.append("Antal poster: {}".format(res[0]))
        cur.execute("SELECT name FROM sellers WHERE seller_id = ?", [seller_id])
        res = cur.fetchone()
        seller_name = res[0]
        cur.execute("SELECT COUNT(posts.type), used_types.sale_type from posts LEFT JOIN used_types ON posts.type = used_types.type_id WHERE seller_id = ? GROUP BY used_types.sale_type", [seller_id])
        res = cur.fetchall()
        for row in res:
            if row[1] == "auction":
                nr_posts.append("Auktion: {}".format(row[0]))
            if row[1] == "fixed_price":
                nr_posts.append("Fastpris: {}".format(row[0]))
        cur.execute("""SELECT  posts.obj_id, posts.scientific_name, posts.plain_name, posts.minimum_price, fixed_price, posts.description, used_types.description
        FROM posts
        INNER JOIN used_types
        ON posts.type=used_types.type_id
        WHERE seller_id = ?""", [seller_id])
        result = cur.fetchall()
        return render_template('list_my_posts.html', heading="{} anmälda poster".format(seller_name), nr_posts=nr_posts, data=result, user=seller_id, registration_open=is_registration_open(), print_labels=False)


@app.route('/list_post_checkin')
@app.route('/list_post_checkin/<seller_id>')
@admin_required
def list_posts_checkin(seller_id=None):
    if seller_id:
        conn = sqlite3.connect(DATABASE)
        with conn:
            cur = conn.cursor()
            list_sql = 'SELECT obj_id, scientific_name, plain_name, description, is_checked_in FROM posts WHERE seller_id=?'
            cur.execute(list_sql, [seller_id])
            result = cur.fetchall()
            return render_template('list_posts_checkin.html', data=result)


@app.route('/delete_post')
@app.route('/delete_post/<post_id>')
@login_required
def delete_post(post_id=None):
    if is_registration_open():
        conn = sqlite3.connect(DATABASE)
        with conn:
            cur = conn.cursor()
            if post_id:
                cur_id = current_user.get_id()
                check_user_sql = "SELECT seller_id FROM posts WHERE obj_id = ?"
                cur.execute(check_user_sql, [post_id])
                owner_id = str(cur.fetchone()[0])
                if cur_id == owner_id or current_user.is_admin:
                    delete_posts_sql = "DELETE FROM posts WHERE obj_id=?"
                    cur.execute(delete_posts_sql, [post_id])
                else:
                    flash("Du har inte rättigheter att radera den posten.")
                    return redirect(request.referrer)
    else:
        flash("Registreringen är stängd.")
    return redirect(request.referrer)


@app.route('/edit_post', methods=['GET', 'POST'])
@app.route('/edit_post/<post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id=None):
    if not is_registration_open() and current_user.is_admin is False:
        flash("Registreringen är stängd.")
        return redirect(request.referrer)

    conn = sqlite3.connect(DATABASE)

    if request.method == 'POST':
        post_id = request.form['post_id']
        post_type = request.form['master_type']
        sciname = request.form['sciname']
        popname = request.form['popname']
        min_price = request.form['min_price']
        fixed_price = request.form['fixed_price']
        description = request.form['description']
        with conn:
            cur = conn.cursor()
            cur_id = current_user.get_id()
            check_user_sql = "SELECT seller_id FROM posts WHERE obj_id = ?"
            cur.execute(check_user_sql, [post_id])
            owner_id = str(cur.fetchone()[0])
            if cur_id == owner_id or current_user.is_admin:
                edit_posts_sql = "UPDATE posts SET scientific_name=?, plain_name=?, description=?, type=?, minimum_price=?, fixed_price=?, label_printed=? WHERE obj_id=?; "
                cur.execute(edit_posts_sql, [sciname, popname, description, post_type, min_price, fixed_price, "no", post_id])
                flash("Posten uppdaterad")
                if current_user.is_admin:
                    return redirect(url_for('list_posts'))
                else:
                    return redirect(url_for('list_my_posts'))
            else:
                flash("Du har inte rättigheter att ändra på den posten.")
                if current_user.is_admin:
                    return redirect(url_for('list_posts'))
                else:
                    return redirect(url_for('list_my_posts'))
    else:
        if post_id:
            with conn:
                cur = conn.cursor()
                cur_id = current_user.get_id()
                check_user_sql = "SELECT seller_id FROM posts WHERE obj_id = ?"
                cur.execute(check_user_sql, [post_id])
                owner_id = str(cur.fetchone()[0])
                if cur_id == owner_id or current_user.is_admin:
                    edit_posts_sql = 'SELECT obj_id, scientific_name, plain_name, description, type, COALESCE(minimum_price, ""), COALESCE(fixed_price, "") FROM posts WHERE obj_id=?'
                    cur.execute(edit_posts_sql, [post_id])
                    data = cur.fetchone()
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
                    if current_user.is_admin:
                        return redirect(url_for('list_all_posts'))
                    else:
                        return redirect(url_for('list_my_posts'))
        else:
            if current_user.is_admin:
                return redirect(url_for('list_posts'))
            else:
                return redirect(url_for('list_my_posts'))


# NOTE: The remaining routes and helper functions below are intentionally unchanged.
# This marker is not valid as a full replacement and would truncate the application.
