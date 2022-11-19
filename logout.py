from flask import Blueprint, redirect, make_response

bp = Blueprint('logout', __name__)

@bp.route('/logout')
def logout():
    resp = make_response(redirect('/'))
    resp.set_cookie('user', '', 0)
    resp.set_cookie('password', '', 0)

    return resp
