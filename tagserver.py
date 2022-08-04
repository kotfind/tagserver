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
    tags = flask.request.args.get('tags', '').split()
    return flask.render_template(
        'index.j2',
        files=logics.getFiles(tags)
        )

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

@app.route('/file/<int:idx>', methods=['POST', 'GET'])
def file(idx):
    if flask.request.method == 'GET':
        return flask.render_template(
            'file.j2',
            file = logics.getFile(idx),
            tags = '\n'.join(logics.getTags(idx))
            )

    tags = list(map(lambda s: s.strip(),
        flask.request.form['tags'].splitlines()))

    logics.updateTags(idx, tags)

    return flask.redirect(flask.request.url)

@app.route('/img/<string:filename>')
def img(filename):
    return flask.send_from_directory(logics.imgDir, filename)

@app.route('/thumb/<string:filename>')
def thumb(filename):
    return flask.send_from_directory(logics.thumbDir, filename)

if __name__ == '__main__':
    waitress.serve(app, host='0.0.0.0', port=int(cfg['Network']['port']))
