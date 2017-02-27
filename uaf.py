# coding=utf-8


import sqlite3
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
from wtforms import StringField, SubmitField, SelectField, IntegerField, HiddenField
from wtforms.validators import DataRequired, Email, Optional, NumberRange
import bcrypt
from flask_login import LoginManager, login_required, UserMixin, login_user, logout_user, current_user
from flask import Flask, request, abort, redirect, Response, url_for, render_template, flash
from functools import wraps
###
import user_model
import zlabels
import compilation


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


class PersonForm(Form):
    """
    wtf form class for the input form
    """
    name = StringField('Namn:', validators=[DataRequired()])
    address = StringField('Adress:', validators=[DataRequired()])
    email = StringField('Email:', validators=[DataRequired(), Email()])
    phone = StringField('Telefonnummer:', validators=[DataRequired()])
    aquarium_club = StringField('Akvarieförening:', validators=[DataRequired()])
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

    seller_email = StringField('Säljarens email:', validators=[DataRequired(), Email()])
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

        conn = sqlite3.connect(DATABASE)
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT email, seller_id FROM sellers WHERE email=?", (email,))
            result = cur.fetchone()
            if result:
                session["seller_id"] = result[1]
                session["seller_email"] = result[0]
                return render_template('done_seller_exists.html', cur_seller_id=session.get("seller_email"))
            else:
                cur.execute("INSERT INTO sellers (name, address, email, phone, aquarium_club) VALUES(?, ?, ?, ?, ?)", (name, address, email, phone, aquarium_club))
                cur_seller_id = cur.lastrowid
                session["seller_id"] = cur_seller_id
                session["seller_email"] = email
                return render_template('done.html', name=name, address=address, email=email, phone=phone, aquarium_club=aquarium_club, cur_seller_id=cur_seller_id)
    else:
        return render_template('new_seller.html', form=form)


@app.route("/register_many", methods=['GET', 'POST'])
def register_many():
    """
    Register many new post at the same time
    :return:
    """
    if request.method == 'POST':
        seller_email = request.form['seller_email']
        types = request.form.getlist('type')
        scinames = request.form.getlist('sciname')
        popnames = request.form.getlist('popname')
        min_prices = request.form.getlist('min_price')
        fixed_prices = request.form.getlist('fixed_price')
        descriptions = request.form.getlist('description')

        print(seller_email)
        print(types)
        print(scinames)
        print(popnames)
        print(min_prices)
        print(fixed_prices)
        print(descriptions)
        new_items = zip(scinames, popnames, descriptions, types, min_prices, fixed_prices)
        print(new_items)

        session["seller_email"] = seller_email
        conn = sqlite3.connect(DATABASE)
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT seller_id FROM sellers WHERE email=?", [seller_email])
            result = cur.fetchone()
            if result:
                seller_id = result[0]
                session["seller_id"] = seller_id
                for scientific_name, plain_name, description, type, minimum_price, fixed_price in new_items:
                    cur.execute(
                        "INSERT INTO posts (seller_id, scientific_name, plain_name, description, type, minimum_price, fixed_price) VALUES(?, ?, ?, ?, ?, ?, ?)",
                    (seller_id, scientific_name, plain_name, description, type, minimum_price, fixed_price))

                flash("Posterna registrerade.")
            else:
                flash(
                    "Email-adressen finns inte i databasen, kontrollera att du skrivit rätt email eller registrera dig som säljare.")

    return render_template('register_many_posts.html')

@app.route("/new_post", methods=['GET', 'POST'])
def add_object():
    """
    Page for adding new posts to the database
    :return:
    """
    form = ObjectForm()
    if form.validate_on_submit():
        seller_email = form.seller_email.data
        description = form.description.data
        scientific_name = form.scientific_name.data
        plain_name = form.plain_name.data
        quantity = form.quantity.data
        type = form.type.data
        min_price = form.min_price.data
        fixed_price = form.fixed_price.data
        session["seller_email"] = seller_email
        conn = sqlite3.connect(DATABASE)
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT seller_id FROM sellers WHERE email=?", [seller_email])
            result = cur.fetchone()
            if result:
                seller_id = result[0]
                session["seller_id"] = seller_id
                cur.execute("INSERT INTO posts (seller_id, scientific_name, plain_name, description, quantity, type, minimum_price, fixed_price) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", (seller_id, scientific_name, plain_name, description, quantity, type, min_price, fixed_price))

                form.description.data = None
                form.scientific_name.data = None
                form.plain_name.data = None
                form.quantity.data = None
                form.type.data = None
                form.min_price.data = None
                form.fixed_price.data = None
                flash("Posten registrerad.")
            else:
                flash("Email-adressen finns inte i databasen, kontrollera att du skrivit rätt eller registrera dig som säljare.")

        return render_template('object.html', form=form)
    else:
        form.seller_email.data = session.get("seller_email")
        print("session seller_email: {}".format(session.get("seller_email")))
        return render_template('object.html', form=form)


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




@app.route('/list')
def list():
    """
    Page for listing all posts in the database
    """
    conn = sqlite3.connect(DATABASE)
    with conn:
        cur = conn.cursor()
        # cur.execute("""SELECT sellers.firstname, sellers.lastname, objects.description, objects.scientific_name, objects.quantity, objects.type
        # FROM sellers
        # INNER JOIN objects
        # ON sellers.seller_id=objects.seller_id""")
        cur.execute("""SELECT  posts.obj_id, posts.scientific_name, posts.plain_name, posts.description, posts.quantity, types.description
        FROM posts
        INNER JOIN types
        ON posts.type=types.type_id""")
        result = cur.fetchall()
        return render_template('list_posts.html', data=result)


@app.route('/list_seller')
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

        conn = sqlite3.connect(DATABASE)
        with conn:
            cur = conn.cursor()
            cur.execute("UPDATE Posts SET sold_price=?, sold_on=? WHERE obj_id=?", (price, sale_type, post_id))
            flash("Post {} registrerad som såld.".format(post_id))

        form.post_id.raw_data = [""]
        form.price.raw_data = [""]
        form.sale_type.data = ""
        return render_template('auktion.html', form=form)

    return render_template('auktion.html', form=form)


@app.route("/loppis", methods=['GET', 'POST'])
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
            cur.execute("UPDATE Posts SET sold_price=?, sold_on=? WHERE obj_id=?", (price, sale_type, post_id))
            flash("Post {} registrerad som såld för {} kronor.".format(post_id, price))

    return render_template('flea_market.html')


@app.route('/labels')
@app.route('/labels/<id>')
def make_labels(id=None):
    """
    Generates a pdf with all the sellers labels or the labels for one seller identified by the seller id
    :param id:
    :return:
    """
    conn = sqlite3.connect(DATABASE)
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT name, date from auction_info")
        auction_info = cur.fetchone()
        auction_name = auction_info[0]
        auction_date = auction_info[1]
        print(auction_name, auction_date, id)
        MK = zlabels.ZLabels("mypdf", auction_name, auction_date)

        if id:
            cur.execute("SELECT seller_id, name, phone, aquarium_club FROM sellers WHERE seller_id=?", id)
        else:
            cur.execute("SELECT seller_id, tname, phone, aquarium_club FROM sellers")
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

    pdf = MK.make_pdf(data)

    response = make_response(pdf)
    response.headers['Content-Disposition'] = "attachment; filename=labels.pdf"
    response.mimetype = 'application/pdf'
    return response


@app.route('/compilation')
@app.route('/compilation/<id>')
def comp(id=None):
    """
    Generates a pdf with a compilation of the sales for each seller or for a singels seller identified by the seller id.
    :param id:
    :return:
    """
    conn = sqlite3.connect(DATABASE)
    data = []
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT name, date, commission from auction_info")
        auction_info = cur.fetchone()
        auction_name = auction_info[0]
        auction_date = auction_info[1]
        commision = auction_info[2]
        print(auction_name, auction_date, id)
        comp_pdf = compilation.Compilation("mypdf", auction_name, auction_date, commision)

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

            cur.execute("SELECT obj_id, type, plain_name, sold_price, sold_on FROM posts WHERE seller_id = ? and sold_price>0", [seller_id])
            res = cur.fetchall()
            data_posts = []
            for posts in res:
                data_posts.append([posts[0], posts[1], posts[2], posts[3], posts[4]])
            data.append([seller_id, seller_name, sold_for, data_posts])

        print(data)

    pdf = comp_pdf.make_pdf(data)

    response = make_response(pdf)
    response.headers['Content-Disposition'] = "attachment; filename=result.pdf"
    response.mimetype = 'application/pdf'
    return response



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


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Register of user
    :return:
    """
    if request.method == 'POST':
        logout_user()
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        # encrypt password
        salt = bcrypt.gensalt()
        password = bcrypt.hashpw(password.encode('utf8'), salt)

        conn = sqlite3.connect(DATABASE)
        with conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO sellers (name, email, password, isAdmin) VALUES (?,?, ?, 'false')",
                        (name, username, password))
            flash("Användare {} skapad.".format(username))
        authed_user = auth(username, password)
        if authed_user:
            # print("new user logged in {} {}".format(user_model, username))
            login_user(authed_user)

        return redirect(url_for('index'))
    else:
        return render_template('register.html')


@app.route("/logout", methods=["GET"])
@login_required
def logout():
    """
    Logout a user
    :return:
    """
    logout_user()
    return render_template('index.html')



@app.errorhandler(404)
def page_not_found(error):
    """
    Route for non existing pages
    """
    return render_template('page_not_found.html'), 404


@app.errorhandler(401)
def page_not_found(error):
    """
    Page not found
    :param error:
    :return:
    """
    return render_template('login_failed.html'), 401

if __name__ == '__main__':
    app.run(debug=True)