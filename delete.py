from flask import Blueprint, redirect
import logics

bp = Blueprint('delete', __name__)

@bp.route('/delete/<int:idx>', methods=['POST'])
def delete(idx):
    logics.deleteFile(idx)

    return redirect('/')
