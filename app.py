#!/bin/python3

import logics

import flask
import click

app = flask.Flask(__name__, template_folder = logics.static('templates'))

userCli = flask.cli.AppGroup('user')

@userCli.command('add')
def addUser():
    from getpass import getpass
    print('Adding new user')
    user = input('User: ').strip()
    password = getpass('Password: ').strip()
    logics.addUser(user, password)

@userCli.command('list')
def listUsers():
    print('\n'.join(logics.getUsers()))

@userCli.command('delete')
@click.argument('name')
def deleteUser(name):
    if not logics.deleteUser(name):
        print('Error: could not delete user')

app.cli.add_command(userCli)

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

# Won't work inside login template
@app.before_request
def before_request():
    from flask import request, redirect
    if request.path == '/login':
        return

    user = request.cookies.get('user')
    password = request.cookies.get('password')

    if not logics.checkUser(user, password):
        return redirect('/login')
