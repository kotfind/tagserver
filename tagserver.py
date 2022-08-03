#!/bin/python3

import logics

import flask
import waitress
import configparser 
import os

os.chdir(os.path.dirname(__file__))

app = flask.Flask(__name__)

cfg = configparser.ConfigParser()
logics.init(cfg)

@app.route('/')
def index():
    return 'Hello, world!'

@app.route('/upload', methods=['POST', 'GET'])
def upload():
    if flask.request.method == 'GET':
        return flask.render_template('upload.j2')

    files = flask.request.files.getlist('imgs[]')
    tags = list(map(lambda s: s.strip(),
        flask.request.form['tags'].splitlines()))

    for file in files:
        logics.saveFile(file, tags)

    return flask.redirect(flask.request.url)

if __name__ == '__main__':
    waitress.serve(app, host='0.0.0.0', port=int(cfg['Network']['port']))
