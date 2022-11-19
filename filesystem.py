from flask import Blueprint, send_from_directory
import logics

bp = Blueprint('filesystem', __name__)

@bp.route('/img/<string:filename>')
def img(filename):
    return send_from_directory(logics.imgDir, filename)

@bp.route('/thumb/<string:filename>')
def thumb(filename):
    return send_from_directory(logics.thumbDir, filename)
