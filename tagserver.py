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

if __name__ == '__main__':
    waitress.serve(app, host='0.0.0.0', port=int(cfg['Network']['port']))
