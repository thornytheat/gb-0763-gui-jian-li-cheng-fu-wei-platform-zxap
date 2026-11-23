from flask import Blueprint, current_app, render_template, request

from app.archive.save import recent
from app.config import REVISION
from app.errors import TrackError
from app.inputs import sample
from app.pipeline import inspect

pages = Blueprint('track_web', __name__)
SECTIONS = {'coverage': '轨段覆盖对账', 'capture': '轨检报文采信', 'anchors': '基点匹配',
            'chainage': '区间坐标复位', 'defects': '缺陷投影合并', 'runs': '批次留档复跑',
            'issue': '巡检证据签发'}


@pages.get('/')
@pages.get('/work/<section>')
def screen(section='coverage'):
    if section not in SECTIONS:
        raise TrackError('NO_SAMPLE', 404)
    label = request.args.get('sample', 'dirty')
    results = inspect(sample(label), section if section not in ('runs', 'issue') else 'coverage')
    ledger = recent(current_app.track_archive)['runs'] if section in ('runs', 'issue') else []
    return render_template('base.html', section=section, nav=SECTIONS, label=label, stages=results,
                           ledger=ledger, rev=REVISION, run_id=request.args.get('run', ''))
