from flask import Blueprint, current_app, render_template, request

from app.archive.save import history, recent, retrieve
from app.config import REVISION
from app.errors import TrackError
from app.inputs import published_repairs, sample
from app.pipeline import inspect

pages = Blueprint('track_web', __name__)
SECTIONS = {'coverage': '轨段覆盖对账', 'capture': '轨检报文采信', 'anchors': '基点匹配',
            'chainage': '区间坐标复位', 'defects': '缺陷投影合并', 'repairs': '维修项销项',
            'runs': '批次留档复跑', 'issue': '巡检证据签发'}
LABELS = {'dirty': '夜巡原始报文', 'clean': '标定对照报文'}
SNAPSHOT = ('runs', 'issue')


@pages.get('/')
@pages.get('/work/<section>')
def screen(section='coverage'):
    if section not in SECTIONS:
        raise TrackError('NO_SAMPLE', 404)
    label = request.args.get('sample', 'dirty')
    needs_closeout = section in ('repairs',) or section in SNAPSHOT
    repairs = published_repairs(label) if needs_closeout else None
    until = 'repairs' if section in SNAPSHOT else section
    results = inspect(sample(label), until, repairs=repairs)
    ledger = recent(current_app.track_archive)['runs'] if section in SNAPSHOT else []
    snapshot = adjudication = None
    run_id = request.args.get('run', '')
    if section == 'runs' and run_id:
        try:
            snapshot = retrieve(current_app.track_archive, run_id)
            adjudication = history(current_app.track_archive, run_id)
        except TrackError:
            snapshot = adjudication = None
    return render_template('base.html', section=section, nav=SECTIONS, label=label, labels=LABELS,
                           stages=results, ledger=ledger, rev=REVISION, run_id=run_id,
                           snapshot=snapshot, adjudication=adjudication)
