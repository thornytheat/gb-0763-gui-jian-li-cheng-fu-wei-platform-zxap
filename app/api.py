from flask import Blueprint, current_app, jsonify

from app.archive.save import recent, replay, retrieve
from app.inputs import source
from app.pipeline import inspect
from app.seals.issue import issue, verified

api = Blueprint('track_api', __name__)


def stage(name):
    return inspect(source(), name)[name]


@api.route('/api/capture', methods=['GET', 'POST'])
def capture():
    return stage('capture')


@api.route('/api/anchors', methods=['GET', 'POST'])
def anchors():
    return stage('anchors')


@api.route('/api/chainage', methods=['GET', 'POST'])
def chainage():
    return stage('chainage')


@api.route('/api/defects', methods=['GET', 'POST'])
def defects():
    return stage('defects')


@api.route('/api/coverage', methods=['GET', 'POST'])
def coverage():
    return stage('coverage')


@api.get('/api/runs')
def history():
    return recent(current_app.track_archive)


@api.post('/api/runs')
def run():
    data = replay(current_app.track_archive, source())
    return data, 200 if data['reused'] else 201


@api.get('/api/runs/<run_id>')
def get_run(run_id):
    return retrieve(current_app.track_archive, run_id)


@api.post('/api/runs/<run_id>/issue')
def sign(run_id):
    return issue(current_app.track_archive, run_id)


@api.get('/api/runs/<run_id>/export')
def export(run_id):
    response = jsonify(verified(current_app.track_archive, run_id))
    response.headers['Content-Disposition'] = f'attachment; filename="track-{run_id}.json"'
    return response
