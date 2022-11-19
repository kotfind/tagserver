#!/bin/python3

import logics

import flask
import waitress

app = flask.Flask(__name__, template_folder = logics.static('templates'))

@app.cli.command('adduser')
def adduser():
    from getpass import getpass
    print('Adding new user')
    user = input('User: ').strip()
    password = getpass('Password: ').strip()
    logics.addUser(user, password)

import delete
import file
import filesystem
import index
import login
import logout
import search
import taglist
import upload

import configparser
cfg = configparser.ConfigParser()
logics.init(cfg)

app.register_blueprint(delete.bp)
app.register_blueprint(file.bp)
app.register_blueprint(filesystem.bp)
app.register_blueprint(index.bp)
app.register_blueprint(login.bp)
app.register_blueprint(logout.bp)
app.register_blueprint(search.bp)
app.register_blueprint(taglist.bp)
app.register_blueprint(upload.bp)
