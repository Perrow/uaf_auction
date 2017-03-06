
# UAF Auction program

This program are to be used during an auction or a fleamarket by an aquarium club or similar organisation.

1. It can handle registration of sellers and the registration of items to sell. This can be categorised by categories defined in a database.

2. It can generate labeles (pdf) and economic reports.

3. It registers price of items sold as well as if it was sold at auction or fleamarket.



## Requirements

This is a client server program written in Python 2.7, HTML, JavaScript and CSS. 
It is meant to be run on a Linux (tested on Ubuntu) server with Apache, but should run on other python compatible servers.

Needed Python libraries:

* flask
* wtforms (flask-wtf)
* flask_login
* reportlab
* bcrypt


Recommended Python environment is anaconda then:
```
pip install flask-wtf
pip install reportlab
pip install bcrypt
```
In order to install bcrypt on Ubuntu 14.04 libffi-dev was needed.
```
sudo apt-get install  libffi-dev   
```
