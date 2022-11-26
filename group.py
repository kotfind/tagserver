from flask import Blueprint, request, render_template
import logics

bp = Blueprint('group', __name__)

@bp.route('/group/<int:groupId>')
def search(groupId):
    page = request.args.get('page', default=0, type=int)

    countPages = logics.countPages(groupId = groupId)

    return render_template(
        'search.j2',
        files = logics.getFiles(groupId = groupId, page = page),
        groupId = groupId,
        page = page,
        countPages = countPages,
        minPage = max(0, page - 3),
        maxPage = min(countPages - 1, page + 3)
    )
