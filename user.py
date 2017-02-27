# coding=utf-8

# from flask import Flask, request, render_template, redirect, url_for, flash
# from flask_login import (LoginManager, current_user, login_required,
#                             login_user, logout_user, UserMixin, AnonymousUser,
# confirm_login, fresh_login_required)

from flask_login import UserMixin
import sqlite3

class User(UserMixin):
    def __init__(self, name, id, email, is_admin=False, active=True):
        self.name = name
        self.id = id
        self.email = email
        self.active = active
        self.is_admin = is_admin

    def is_active(self):
        # Here you should write whatever the code is
        # that checks the database if your user is active
        print("Active: {}".format(self.active))
        return self.active

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True

    def get_id(self):
        #try:
        return unicode(self.id)  # python 2
        #except NameError:
        #return str(self.id)  # python 3

    def is_admin(self):
        """
        Returns True if the user has administrative powers otherwise False is returned
        :return:
        """
        return self.is_admin



