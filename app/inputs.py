import json

from flask import request

from app.config import SAMPLES
from app.errors import TrackError

SAMPLE_NAMES = ('dirty', 'clean')
SOURCES = ('sample', 'csv')


def sample(name):
    if name not in SAMPLE_NAMES:
        raise TrackError('NO_SAMPLE', 404)
    return (SAMPLES / f'{name}.csv').read_bytes()


def published_repairs(name):
    """样例随附的维修项记录；没有时返回空表。"""
    path = SAMPLES / 'repairs.json'
    if not path.exists():
        return []
    document = json.loads(path.read_text(encoding='utf-8'))
    return document.get(name, [])


def _body():
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or set(body) - {*SOURCES, 'repairs'}:
        raise TrackError('BAD_BODY')
    return body


def _choice():
    if request.method == 'GET':
        name = request.args.get('sample', 'dirty')
        return sample(name), published_repairs(name)
    body = _body()
    if len([key for key in SOURCES if key in body]) != 1:
        raise TrackError('BAD_BODY')
    if 'csv' in body:
        value = body['csv']
        if not isinstance(value, str):
            raise TrackError('BAD_BODY')
        try:
            raw = value.encode('utf-8')
        except UnicodeEncodeError as exc:
            raise TrackError('BAD_CSV') from exc
        return raw, body.get('repairs')
    name = body.get('sample')
    if not isinstance(name, str):
        raise TrackError('BAD_BODY')
    repairs = published_repairs(name) if 'repairs' not in body else body['repairs']
    return sample(name), repairs


def resolved():
    """一次解析取回报文与维修项记录，避免同一请求体被读两遍。"""
    return _choice()


def source():
    """只取报文，保留旧调用点；维修项另由 resolved() 取得。"""
    return _choice()[0]
