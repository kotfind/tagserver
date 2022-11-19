from flask import Blueprint, request, render_template
import logics

bp = Blueprint('file', __name__)

@bp.route('/file/<int:idx>', methods=['POST', 'GET'])
def file(idx):
    if request.method == 'GET':
        file = logics.getFile(idx)
        ownTags = logics.getTags(idx)
        queryTags = request.args.get('queryTags', '').lower().split()
        prevId, nextId = logics.getNeighbours(queryTags, idx)

        return render_template(
            'file.j2',
            file = file,
            ownTags = ownTags,
            queryTags = queryTags,
            isVideo = logics.isVideo(file.imgFilename),
            prevId = prevId,
            nextId = nextId,
            )

    tags = list(map(lambda s: s.strip().lower().replace(' ', '_'),
        request.form['tags'].splitlines()))

    logics.updateTags(idx, tags)

    return redirect(request.url)
