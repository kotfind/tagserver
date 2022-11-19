from flask import Blueprint, render_template
import logics

bp = Blueprint('taglist', __name__)

@bp.route('/taglist')
def taglist():
    return render_template(
        'taglist.j2',
        tags = logics.getAllTags()
    )
