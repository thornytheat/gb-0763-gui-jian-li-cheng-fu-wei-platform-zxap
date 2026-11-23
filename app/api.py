from flask import Blueprint, current_app, jsonify

from app.archive.save import history as run_history
from app.archive.save import recent, replay, retrieve
from app.inputs import resolved
from app.pipeline import inspect
from app.seals.issue import issue, verified

api = Blueprint('track_api', __name__)


def stage(name):
    raw, repairs = resolved()
    # 只有销项阶段需要维修项；其余阶段保持原有输出结构。
    return inspect(raw, name, repairs=repairs if name == 'repairs' else None)[name]


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


@api.route('/api/repairs', methods=['GET', 'POST'])
def repairs():
    return stage('repairs')


@api.get('/api/runs')
def history():
    return recent(current_app.track_archive)


@api.post('/api/runs')
def run():
    raw, repairs = resolved()
    data = replay(current_app.track_archive, raw, repairs)
    return data, 200 if data['reused'] else 201


@api.get('/api/runs/<run_id>')
def get_run(run_id):
    return retrieve(current_app.track_archive, run_id)


@api.get('/api/runs/<run_id>/adjudications')
def adjudications(run_id):
    return run_history(current_app.track_archive, run_id)


@api.post('/api/runs/<run_id>/issue')
def sign(run_id):
    return issue(current_app.track_archive, run_id)


@api.get('/api/runs/<run_id>/export')
def export(run_id):
    response = jsonify(verified(current_app.track_archive, run_id))
    response.headers['Content-Disposition'] = f'attachment; filename="track-{run_id}.json"'
    return response
