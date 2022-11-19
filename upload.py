from flask import Blueprint, render_template, request, redirect
import logics

bp = Blueprint('upload', __name__)

@bp.route('/upload', methods=['POST', 'GET'])
def upload():
    if request.method == 'GET':
        return render_template('upload.j2')

    files = request.files.getlist('imgs[]')
    tags = list(map(lambda s: s.strip().lower().replace(' ', '_'),
        request.form['tags'].splitlines()))

    for file in files:
        logics.saveFile(file, tags)

    return redirect(request.url)
