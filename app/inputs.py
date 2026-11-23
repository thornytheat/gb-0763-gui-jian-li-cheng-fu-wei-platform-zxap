from flask import request

from app.config import SAMPLES
from app.errors import TrackError


def sample(name):
    if name not in ('dirty', 'clean'):
        raise TrackError('NO_SAMPLE', 404)
    return (SAMPLES / f'{name}.csv').read_bytes()


def source():
    if request.method == 'GET':
        return sample(request.args.get('sample', 'dirty'))
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or set(body) - {'sample', 'csv'} or len(body) != 1:
        raise TrackError('BAD_BODY')
    if 'csv' in body and isinstance(body['csv'], str):
        try:
            return body['csv'].encode('utf-8')
        except UnicodeEncodeError as exc:
            raise TrackError('BAD_CSV') from exc
    if isinstance(body.get('sample'), str):
        return sample(body['sample'])
    raise TrackError('BAD_BODY')
