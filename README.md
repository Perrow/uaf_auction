
# UAF Auction program

This program are to be used during an auction or a fleamarket by an aquarium club or similar organisation.

1. It can handle registration of sellers and the registration of items to sell. This can be categorised by categories defined in a database.

2. It can generate labeles (pdf) and economic reports.

3. It registers price of items sold as well as if it was sold at auction or fleamarket.



## Requirements

This is a client server program written in Python 3.5, HTML5, JavaScript and CSS with Bootstrap. 
It is meant to be run on a Linux (tested on Ubuntu) server with Apache, but should run on other python compatible servers.

### Install and setup of webserver on Linux (Ubuntu / Raspbian)
Tested on Ubuntu 14.04, 16.04, Linux Mint 18, Raspbian 2017-03-02-raspbian-jessie-lite and 
piOS Raspbian 11 Bullseye (2022-11-22).
.

This file describes the installation on a Raspberry pi with Raspbian 11 in the folder /home/pi/uaf.

Install apache with Python3 support:

```
sudo apt-get update
sudo apt-get upgrade

sudo apt-get install apache2
sudo apt-get install libapache2-mod-wsgi-py3 python3-dev
```

Enable mod_wsgi, need for running python under apache.
```
sudo a2enmod wsgi 
```

Download the code from gitlab, requires ssh-keys to access gitlab:
```
sudo apt-get install git
git clone git@gitlab.com:kristianpersson/uaf_auction.git
mv uaf_auction/ uaf/
```
Or copy the code in another way, but place it in /home/pi/uaf.


For apache 2.4 the uaf.conf file should look like this, if the program is in the folder /home/pi/uaf.
```
<VirtualHost *:80>

                WSGIDaemonProcess uaf user=pi group=pi threads=5 home=/home/pi/uaf
                WSGIScriptAlias / /home/pi/uaf/uaf.wsgi

                <Directory /home/pi/uaf/>
                     WSGIProcessGroup uaf
                     WSGIApplicationGroup %{GLOBAL}

                     WSGIScriptReloading On
                     Require all granted
                </Directory>

                LogLevel warn
                CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
```

If the server has an domain name (like auction.uaf.se) and the program is to be accessed via that, then 
add the line:

```
ServerName auction.uaf.se
```
As the first line after <VirtualHost *:80>.
 

Copy the conf-file to /etc/apache2/sites-available\
```
sudo cp uaf.conf /etc/apache2/sites-available/
```

Deactivate the default website, and activate the flask-site.
```
sudo a2dissite 000-default.conf 
sudo a2ensite uaf.conf
sudo systemctl reload apache2
```

There must be a wsgi file in the same folder as the python program. 
In the above VirtualHost definifion WSGIScriptAlias points to this file. 
This links the requested path in the webb-browser to the python program to run. 
It should look like this:
```
import sys

sys.path.append('/home/pi/uaf')
from uaf import app as application
```


### Python3

If needed:
```
sudo apt-get install python3-pip 
```

Always upgrade pip to the latest version:
```
sudo pip3 install --upgrade pip
```

Install build-essentials 
```
sudo apt-get install build-essential
```

Install rust for compilation of bcrypt. Rust must be version 1.56 or later.
On raspberry pi I did not manage to get rust working, so use an older version of bcrypt 3.2.2 
which is not dependent on rust.

```
curl https://sh.rustup.rs -sSf | sh
```

Needed Python libraries:

* flask
* flask_login
* reportlab
* bcrypt

Install with pip:
```
sudo pip3 install flask_login
sudo pip3 install reportlab
sudo pip3 install bcrypt
or
sudo pip3 install bcrypt==3.2.2
```
In order to install bcrypt on Ubuntu 14.04 and Rasbian, libffi-dev was needed:
```
sudo apt-get install  libffi-dev
```

If internal server error, check the error log for error messages:
```
tail -n 20 /var/log/apache2/error.log
```

If PIL error in logfile:
```
>>> from PIL import Image
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/usr/local/lib/python3.9/dist-packages/PIL/Image.py", line 100, in <module>
    from . import _imaging as core
ImportError: libopenjp2.so.7: cannot open shared object file: No such file or directory
```
Uninstall and reinstall of Pillow might solve the problem:
```
sudo pip3 uninstall Pillow
sudo pip3 install Pillow
```

### Configure the program
#### Config file
The program has a config file that gives the location and name of the database.
Copy the example config file and edit the content.
```
cp config.cfg.example config.cfg
```

Content of config file:
```
SECRET_KEY='a secret string'
DATABASE='auktion_generated.db3'
GMAILUSER='username@gmail.com'
GMAILPASSWORD='password'
```

The most important is DATABASE which is the name of the database.
SECRET_KEY generates the key for cookies and should be a random string.
GMAILUSER and GMAILPASSWORD was used to send notification emails from this gmail account when users are 
created and posts are added. In Settings under Administration menu on the webinterface the reciving mailaddress
can be given, empty means no emails are sent.
The mail function does not work anymore as Google has increased the security for Google accounts.

#### Database
The program needs a database to work. A new example database can be generated with:
```
python3 make_database.py
```
The admin user in that database is Kalle Persson. Username kalle.persson@mail.com and password password.
The database can be reset by creating a new event. All existing users will then be removed,
including the admin and a new admin will be created.
