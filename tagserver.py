#!/bin/python3

import logics

import flask
import waitress
import configparser 
import os
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

@app.route('/')
def index():
    return flask.render_template('index.j2')

@app.route('/search')
def search():
    tags = flask.request.args.get('tags', '').lower().split()
    page = flask.request.args.get('page', default=0, type=int)

    countPages = logics.countPages(tags)

    return flask.render_template(
        'search.j2',
        files = logics.getFiles(tags, page),
        tags = tags,
        page = page,
        countPages = countPages,
        minPage = max(0, page - 3),
        maxPage = min(countPages - 1, page + 3)
        )

@app.route('/upload', methods=['POST', 'GET'])
def upload():
    if flask.request.method == 'GET':
        return flask.render_template('upload.j2')

    files = flask.request.files.getlist('imgs[]')
    tags = list(map(lambda s: s.strip().lower().replace(' ', '_'),
        flask.request.form['tags'].splitlines()))

    for file in files:
        logics.saveFile(file, tags)

    return flask.redirect(flask.request.url)

@app.route('/file/<int:idx>', methods=['POST', 'GET'])
def file(idx):
    if flask.request.method == 'GET':
        file = logics.getFile(idx)
        ownTags = logics.getTags(idx)
        queryTags = flask.request.args.get('queryTags', '').lower().split()
        prevId, nextId = logics.getNeighbours(queryTags, idx)

        return flask.render_template(
            'file.j2',
            file = file,
            ownTags = ownTags,
            queryTags = queryTags,
            isVideo = logics.isVideo(file.imgFilename),
            prevId = prevId,
            nextId = nextId,
            )

    tags = list(map(lambda s: s.strip().lower().replace(' ', '_'),
        flask.request.form['tags'].splitlines()))

    logics.updateTags(idx, tags)

    return flask.redirect(flask.request.url)

@app.route('/img/<string:filename>')
def img(filename):
    return flask.send_from_directory(logics.imgDir, filename)

@app.route('/thumb/<string:filename>')
def thumb(filename):
    return flask.send_from_directory(logics.thumbDir, filename)

@app.route('/taglist')
def taglist():
    return flask.render_template(
        'taglist.j2',
        tags = logics.getAllTags()
        )

@app.route('/delete/<int:idx>', methods=['POST'])
def delete(idx):
    logics.deleteFile(idx)

    return flask.redirect('/')

@app.before_request
def before_request():
    if flask.request.path == '/login':
        return

    user = flask.request.cookies.get('user')
    password = flask.request.cookies.get('password')

    if not logics.checkUser(user, password):
        return flask.redirect('/login')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if flask.request.method == 'GET':
        return flask.render_template('login.j2')

    resp = flask.make_response(flask.redirect('/'))
    resp.set_cookie('user', flask.request.form['user'].strip())
    resp.set_cookie('password', logics.hashPassword(flask.request.form['password'].strip()))

    return resp

@app.route('/logout')
def logout():
    resp = flask.make_response(flask.redirect('/'))
    resp.set_cookie('user', '', 0)
    resp.set_cookie('password', '', 0)

    return resp

if __name__ == '__main__':
    waitress.serve(app,
        host='0.0.0.0',
        port=int(cfg['Network']['port']),
        threads=int(cfg['Network']['threads'])
        )
