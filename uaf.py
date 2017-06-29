# coding=utf-8
import os
import sqlite3
import time
from flask import Flask
from flask import jsonify
# from flask import url_for
from flask import render_template
# from flask import render_template_string
# from flask import redirect
from flask import request
from flask import make_response
from flask import session
from flask import flash
from flask_wtf import Form
from wtforms import StringField, SubmitField, SelectField, IntegerField, HiddenField, PasswordField
from wtforms.validators import DataRequired, Email, Optional, NumberRange
import bcrypt
from flask_login import LoginManager, login_required, UserMixin, login_user, logout_user, current_user
from flask import Flask, request, abort, redirect, Response, url_for, render_template, flash
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

# For flask-login
lm = LoginManager()
lm.init_app(app)
lm.login_view = "login"
# lm.anonymous_user = anonymous_user.Anonymous

# *** WTF Form classes *** #


class PersonForm(Form):
    """
    wtf form class for the input form
    """
    name = StringField('Namn:', validators=[DataRequired()])
    address = StringField('Adress:', validators=[DataRequired()])
    email = StringField('Email:', validators=[DataRequired(), Email()])
    phone = StringField('Telefonnummer:', validators=[DataRequired()])
    aquarium_club = StringField('Akvarieförening:', validators=[DataRequired()])
    password = PasswordField('Lösenord:', validators=[DataRequired()])
    submit = SubmitField('Skicka')


class ObjectForm(Form):
    """
    wtf form class for the input form
    """
    # Fetch sale types from database
    conn = sqlite3.connect(DATABASE)
    choices = []
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT type_id, description FROM types ORDER BY type_id")
        result = cur.fetchall()
        for row in result:
            choices.append((str(row[0]), row[1]))

    # seller_email = StringField('Säljarens email:', validators=[DataRequired(), Email()])
    plain_name = StringField('Namn:', validators=[DataRequired()])
    scientific_name = StringField('Vetenskapligt namn:', validators=[Optional()])
    description = StringField('Beskrivning:', validators=[Optional()])
    quantity = StringField('Antal:', validators=[DataRequired()])
    type = SelectField('Godstyp', choices=choices)
    min_price = StringField('Reserverat utropspris (frivilligt):', validators=[Optional()])
    fixed_price = StringField('Fast pris:', validators=[Optional()])
    # min_price = IntegerField('Reserverat utropspris (frivilligt):', validators=[Optional()])
    # fixed_price = IntegerField('Fast pris:', validators=[Optional(), NumberRange(min=0, max=1000)])
    submit = SubmitField('Skicka')


class AuctionForm(Form):
    """
    Form for auction
    """
    post_id = IntegerField('Postens nummer:', validators=[DataRequired()])
    price = IntegerField('Pris:', validators=[DataRequired()])
    sale_type = HiddenField("", default="auktion")
    submit = SubmitField('Skicka')

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
            flash("This page need admin priviliges.")
            return render_template('index.html')

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
        cur.execute("SELECT seller_id, password FROM sellers WHERE email=? ", (username, ))
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
    return render_template('index.html')


@app.route('/new_seller', methods=['GET', 'POST'])
def new_seller():
    """
   Page for adding new sellers to the database
    :return:
    """
    form = PersonForm()
    if form.validate_on_submit():
        name = form.name.data
        # surname = form.surname.data
        email = form.email.data
        address = form.address.data
        phone = form.phone.data
        aquarium_club = form.aquarium_club.data
        password = form.password.data.encode('utf-8')

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
                cur.execute("INSERT INTO sellers (name, address, email, phone, aquarium_club, password, isAdmin, time_stamp) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", (name, address, email, phone, aquarium_club, encrypted_password, "no", time.strftime("%Y-%m-%d %H:%M:%S")))

                flash("Användare {} skapad.".format(name))
            authed_user = auth(name, password)
            if authed_user:
                # print("new user logged in {} {}".format(user_model, username))
                login_user(authed_user)

            return redirect(url_for('index'))
                # return render_template('done.html', name=name, address=address, email=email, phone=phone, aquarium_club=aquarium_club, cur_seller_id=cur_seller_id)
    else:
        return render_template('new_seller.html', form=form)


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
    select = '<select id="master_type" name="master_type">'
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT type_id, description FROM types ORDER BY type_id")
        result = cur.fetchall()
        for row in result:
            tempstr = '<option value="{}">{}</option>'.format(row[0], row[1])
            select += tempstr
    select += '</select>'
    return render_template('register_many_posts.html', select=select)


@app.route("/register_post", methods=['GET', 'POST'])
@login_required
def register_post():
    """
    Page for adding new posts to the database
    :return:
    """
    form = ObjectForm()
    if form.validate_on_submit():
        # seller_email = form.seller_email.data
        description = form.description.data
        scientific_name = form.scientific_name.data
        plain_name = form.plain_name.data
        quantity = form.quantity.data
        post_type = form.type.data
        min_price = form.min_price.data
        fixed_price = form.fixed_price.data
        # session["seller_email"] = seller_email
        seller_id = current_user.get_id()
        conn = sqlite3.connect(DATABASE)
        with conn:
            cur = conn.cursor()
            # cur.execute("SELECT seller_id FROM sellers WHERE email=?", [seller_email])
            # result = cur.fetchone()
            # if result:
            #     seller_id = result[0]
            #     session["seller_id"] = seller_id
            cur.execute("INSERT INTO posts (seller_id, scientific_name, plain_name, description, quantity, type, minimum_price, fixed_price, time_stamp_registration) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", (seller_id, scientific_name, plain_name, description, quantity, post_type, min_price, fixed_price, time.strftime("%Y-%m-%d %H:%M:%S")))

            form.description.data = None
            form.scientific_name.data = None
            form.plain_name.data = None
            form.quantity.data = None
            form.type.data = None
            form.min_price.data = None
            form.fixed_price.data = None
            flash("Posten registrerad.")
            # else:
            #     flash("Email-adressen finns inte i databasen, kontrollera att du skrivit rätt eller registrera dig som säljare.")

        return render_template('object.html', form=form)
    else:
        # form.seller_email.data = session.get("seller_email")
        # print("session seller_email: {}".format(session.get("seller_email")))
        return render_template('object.html', form=form)


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

        cur.execute("""SELECT  posts.obj_id, posts.scientific_name, posts.plain_name, posts.description, posts.quantity, types.description
        FROM posts
        INNER JOIN types
        ON posts.type=types.type_id""")
        result = cur.fetchall()
        return render_template('list_posts.html', nr_posts=nr_posts, data=result)


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
    form = AuctionForm()
    if form.validate_on_submit():

        post_id = form.post_id.data
        price = form.price.data
        sale_type = form.sale_type.data
        print(sale_type)

        conn = sqlite3.connect(DATABASE)
        with conn:
            cur = conn.cursor()
            cur.execute("UPDATE Posts SET sold_price=?, sold_on=?, time_stamp_sold=? WHERE obj_id=?", (price, sale_type, time.strftime("%Y-%m-%d %H:%M:%S"), post_id))
            flash("Post {} registrerad som såld.".format(post_id))

        form.post_id.raw_data = [""]
        form.price.raw_data = [""]
        # form.sale_type.data = ""
        return render_template('auktion.html', form=form)

    return render_template('auktion.html', form=form)


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

        cur.execute(""" SELECT posts.obj_id, sellers.name, posts.description, posts.scientific_name, posts.plain_name, posts.quantity, posts.sold_on, posts.fixed_price, posts.sold_price, types.sale_type as type, posts.minimum_price
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
    return ('', 204)  # empty response


# @app.route('/labels')
# @app.route('/labels/<selected_id>')
# @admin_required
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
        print(auction_name, auction_date, selected_id)
        labels = zlabels.ZLabels("mypdf", auction_name, auction_date)
        print("SELECT seller_id, name, phone, aquarium_club FROM sellers WHERE seller_id=?", selected_id)
        if selected_id:
            cur.execute("SELECT seller_id, name, phone, aquarium_club FROM sellers WHERE seller_id=?", selected_id)
        else:
            cur.execute("SELECT seller_id, name, phone, aquarium_club FROM sellers")
        sellers = cur.fetchall()
        data = []
        for seller in sellers:
            seller_id = seller[0]
            print(seller_id)
            cur.execute("SELECT obj_id, plain_name, scientific_name, quantity, fixed_price FROM posts WHERE seller_id=?", (seller_id,))
            posts = cur.fetchall()
            seller_data = [seller[0], seller[1], seller[2], seller[3]]
            post_data = []
            for post in posts:
                post_data.append([post[0], " ".join([post[1], post[2]]), post[3], post[4]])
            seller_data.append(post_data)
            data.append(seller_data)
        print(data)

    pdf = labels.make_pdf(data)
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
    return ('', 204)  # empty response

# @app.route('/economic_report')
# @admin_required
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
            # tot_data_type.append([row[3], row[1], row[2], row[0]])
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
    return ('', 204)  # empty response


def get_auction_wall_list():
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
        # my_data2 = cur.fetchall()
        # my_data.extend(my_data2)
        # my_data.extend(my_data2)
        my_headings.extend(my_data)  # Add headings to list of auction objects

        MWL = make_wall_list_pdf.MakeWallList(club_name, event_name, event_date, event_city)
        pdf = MWL.make_pdf(my_headings)
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
    return ('', 204)  # empty response


# @app.route('/compilation')
# @app.route('/compilation/<selected_id>')
# @admin_required
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
        # cur.execute("SELECT hosting_association, event_name, date, city, commission from auction_info")
        # auction_info = cur.fetchone()
        # hosting_association = auction_info[0]
        # auction_name = auction_info[1]
        # auction_date = auction_info[2]
        # event_city = auction_info[3]
        # commision = auction_info[4]
        print(event_name, event_date, selected_id)
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

            # cur.execute("SELECT obj_id, type, plain_name, sold_price, sold_on FROM posts WHERE seller_id = ? and sold_price>0", [seller_id])
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
    return ('', 204)  # empty response


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
        username = request.form['username']
        password = request.form['password']

        authed_user = auth(username, password)
        if authed_user:
            login_user(authed_user)
            flash('Logged in successfully.')
            next_page = request.args.get('next')

            # is_safe_url should check if the url is safe for redirects.
            # See http://flask.pocoo.org/snippets/62/ for an example.
            # if not is_safe_url(next):
            #     return abort(400)

            return redirect(next_page or url_for('index'))

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
    return render_template('index.html')


# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     """
#     Register a new user
#     :return:
#     """
#     if request.method == 'POST':
#         logout_user()
#         name = request.form['name']
#         username = request.form['username']
#         password = request.form['password']
#         # encrypt password
#         salt = bcrypt.gensalt()
#         password = bcrypt.hashpw(password.encode('utf8'), salt)
# 
#         conn = sqlite3.connect(DATABASE)
#         with conn:
#             cur = conn.cursor()
#             cur.execute("INSERT INTO sellers (name, email, password, isAdmin) VALUES (?,?, ?, 'false')",
#                         (name, username, password))
#             flash("Användare {} skapad.".format(username))
#         authed_user = auth(username, password)
#         if authed_user:
#             # print("new user logged in {} {}".format(user_model, username))
#             login_user(authed_user)
# 
#         return redirect(url_for('index'))
#     else:
#         return render_template('register.html')

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
