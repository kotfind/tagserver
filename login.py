from flask import Blueprint, request, render_template, make_response, redirect
import logics

bp = Blueprint('login', __name__)

@bp.before_request
def before_request():
    if request.path == '/login':
        return

    user = request.cookies.get('user')
    password = request.cookies.get('password')

    if not logics.checkUser(user, password):
        return redirect('/login')

@bp.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        return render_template('login.j2')

    resp = make_response(redirect('/'))
    resp.set_cookie('user', request.form['user'].strip())
    resp.set_cookie('password', logics.hashPassword(request.form['password'].strip()))

    return resp
