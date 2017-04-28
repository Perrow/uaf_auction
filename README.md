
# UAF Auction program

This program are to be used during an auction or a fleamarket by an aquarium club or similar organisation.

1. It can handle registration of sellers and the registration of items to sell. This can be categorised by categories defined in a database.

2. It can generate labeles (pdf) and economic reports.

3. It registers price of items sold as well as if it was sold at auction or fleamarket.



## Requirements

This is a client server program written in Python 2.7, HTML, JavaScript and CSS. 
It is meant to be run on a Linux (tested on Ubuntu) server with Apache, but should run on other python compatible servers.

### Install and setup of webserver on Linux (Ubuntu / Rasbian)
Tested on Ubuntu 14.04 and Rasbian 2017-03-02-raspbian-jessie-lite.
Install apache with python support

```
sudo apt-get update
sudo apt-get upgrade

sudo apt-get install apache2
sudo apt-get install libapache2-mod-wsgi python-dev
```
Enable mod_wsgi, need for running pyhton under apache.
```
sudo a2enmod wsgi 
```

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
For apache 2.2 Require all granted should be replaced by
```
Order deny,allow
Allow from all
```

Deactivate the default website, and activate the flask-site.
```
sudo a2dissite 000-default.conf 
sudo a2ensite uaf.conf
sudo service apache2 restart
```

There must be a wsgi file in the same folder as the python program. In the above VirtualHost definifion WSGIScriptAlias points to this file. This links the requesed path in the webbrowser to the python program to run. It should look like this.
```
import sys

sys.path.append('/home/pi/uaf')
from uaf import app as application
```


### Python

If needed:
```
sudo apt-get install python-pip 
```

Needed Python libraries:

* flask
* wtforms (flask-wtf)
* flask_login
* reportlab
* bcrypt


Recommended Python environment is anaconda then:
```
conda install flask-wtf
conda install flask-login
conda install reportlab
conda install bcrypt
```

Or use pip:
```
sudo pip install flask-wtf
sudo pip install flask_login
sudo pip install reportlab
sudo pip install bcrypt
```
In order to install bcrypt on Ubuntu 14.04 and Rasbian, libffi-dev was needed.
```
sudo apt-get install  libffi-dev
```




