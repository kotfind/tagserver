#!/bin/python3

import logics

import flask
import waitress
import configparser 
import sys
import getpass

cfg = configparser.ConfigParser()
logics.init(cfg)

def usage():
    print('Usage: {} run|adduser'.format(sys.argv[0]))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        usage()
        exit(1)

    cmd = sys.argv[1].lower()

    if cmd == 'adduser':
        print('Adding new user')
        user = input('User: ').strip()
        password = getpass.getpass('Password: ').strip()
        logics.addUser(user, password)
        exit(0)
    elif cmd != 'run':
        usage()
        exit(1)

app = flask.Flask(__name__, template_folder = logics.static('templates'))


import delete
import file
import filesystem
import index
import login
import logout
import search
import taglist
import upload

app.register_blueprint(delete.bp)
app.register_blueprint(file.bp)
app.register_blueprint(filesystem.bp)
app.register_blueprint(index.bp)
app.register_blueprint(login.bp)
app.register_blueprint(logout.bp)
app.register_blueprint(search.bp)
app.register_blueprint(taglist.bp)
app.register_blueprint(upload.bp)

if __name__ == '__main__':
    waitress.serve(app,
        host='0.0.0.0',
        port=int(cfg['Network']['port']),
        threads=int(cfg['Network']['threads'])
    )
