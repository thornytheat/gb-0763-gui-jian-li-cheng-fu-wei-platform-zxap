from flask import Flask

from app.api import api
from app.archive.storage import TrackArchive
from app.config import DATABASE
from app.errors import TrackError
from app.reasons import REASONS
from app.web import pages


def create_app(database=DATABASE):
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
    app.json.ensure_ascii = False
    app.track_archive = TrackArchive(database)
    app.register_blueprint(api)
    app.register_blueprint(pages)

    @app.errorhandler(TrackError)
    def handle(error):
        return {'error': error.code, 'message': REASONS[error.code]}, error.status

    @app.get('/healthz')
    def health():
        return {'status': 'ok'}

    return app
