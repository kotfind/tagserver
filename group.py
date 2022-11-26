from flask import Blueprint, request, render_template
import logics

bp = Blueprint('group', __name__)

@bp.route('/group/<int:groupId>')
def search(groupId):
    page = request.args.get('page', default=0, type=int)

    return render_template(
        'search.j2',
        files = logics.getGroupFiles(groupId),
        groupId = groupId
    )
