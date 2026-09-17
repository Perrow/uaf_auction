import sys

sys.path.append('/home/kristian/UAF_auction')
from uaf import app as application
from label_preview import register_routes

register_routes(application)