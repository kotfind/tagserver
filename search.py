from flask import Blueprint, request, render_template
import logics

bp = Blueprint('search', __name__)

@bp.route('/search')
def search():
    tags = request.args.get('tags', '').lower().split()
    page = request.args.get('page', default=0, type=int)

    countPages = logics.countPages(tags = tags)

    return render_template(
        'search.j2',
        files = logics.getFiles(tags = tags, page = page),
        tags = tags,
        page = page,
        countPages = countPages,
        minPage = max(0, page - 3),
        maxPage = min(countPages - 1, page + 3)
    )
