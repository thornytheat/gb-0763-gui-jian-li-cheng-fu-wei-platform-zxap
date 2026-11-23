from datetime import datetime, timezone
import json
import sqlite3
from time import perf_counter

from app.config import GAP_SECONDS, LATE_SECONDS, MERGE_MM, REVISION
from app.errors import TrackError
from app.manifest import canonical, digest
from app.pipeline import inspect
from app.anchors.register import survey_book
from app.repairs.closeout import normalize
from app.reasons import REASONS


def retrieve(archive, run_id):
    with archive.transaction() as db:
        record = db.execute('SELECT payload FROM runs WHERE id=?', (run_id,)).fetchone()
    if record is None:
        raise TrackError('RUN_MISSING', 404)
    return json.loads(record[0])


def _summary(evidence):
    summary = {key: evidence['coverage'][key]
               for key in ('planned_mm', 'mapped_mm', 'missing_mm', 'overlap_mm')}
    closeout = evidence.get('repairs') or {'item_count': 0, 'closed_mm': 0, 'pending_mm': 0,
                                           'verdicts': []}
    summary.update(repair_count=closeout['item_count'], closed_mm=closeout['closed_mm'],
                   pending_mm=closeout['pending_mm'],
                   pending_items=sum(1 for item in closeout['verdicts']
                                     if item['status'] != 'CLOSED'))
    summary['reason_labels'] = {code: REASONS[code] for code in REASONS
                                if code in {blocker for item in closeout['verdicts']
                                            for blocker in item['blockers']}}
    return summary


def replay(archive, raw, repairs=None):
    """复算并归档一趟巡检；同一报文、测绘表与维修项的组合只落一次。

    归档失败整笔回滚，不留半份快照，可直接重试；重跑同一批次命中运行键，取回原快照，
    不重复销项。
    """
    started = perf_counter()
    survey = survey_book()
    repairs = normalize(repairs)
    evidence = inspect(raw, survey=survey, repairs=repairs)
    parameters = {'gap_s': GAP_SECONDS, 'late_s': LATE_SECONDS, 'merge_mm': MERGE_MM}
    identity = {'input_sha256': digest(raw), 'survey_sha256': digest(canonical(survey)),
                'repairs_sha256': digest(canonical(repairs)), 'revision': REVISION,
                'parameters': parameters}
    run_id = digest(canonical(identity))
    summary = _summary(evidence)
    manifest = dict(identity, run_id=run_id, created_at=datetime.now(timezone.utc).isoformat(),
                    elapsed_ms=round((perf_counter() - started) * 1000), summary=summary,
                    repair_count=len(repairs))
    payload = canonical({'manifest': manifest, 'stages': evidence})
    for attempt in range(2):
        try:
            with archive.transaction() as db:
                inserted = db.execute('INSERT OR IGNORE INTO runs VALUES (?, ?)',
                                      (run_id, payload)).rowcount
                _record_adjudications(db, run_id, evidence['repairs'])
                previous = db.execute('SELECT payload FROM runs WHERE id=?', (run_id,)).fetchone()[0]
            return dict(json.loads(previous)['manifest'], reused=not bool(inserted))
        except sqlite3.OperationalError:
            # 写锁冲突：事务已整体回滚，重试一次即可从空档继续，不留下半份快照。
            if attempt:
                raise
    raise AssertionError('unreachable')


def _record_adjudications(db, run_id, closeout):
    """把本批每次裁定按维修项留档；重跑命中同一运行键，不会重复记账。"""
    for seq, item in enumerate(closeout['verdicts']):
        record = {'repair_id': item['repair_id'], 'chain': item['chain'],
                  'status': item['status'], 'closed_to_mm': item['closed_to_mm'],
                  'closed_mm': item['closed_mm'], 'pending_mm': item['pending_mm'],
                  'blockers': item['blockers'],
                  'blocker_labels': [REASONS[code] for code in item['blockers']],
                  'repaired_at': item['repaired_at']}
        db.execute('INSERT OR IGNORE INTO adjudications VALUES (?, ?, ?, ?)',
                   (run_id, item['repair_id'], seq, canonical(record)))


def history(archive, run_id):
    """取一批历次裁定；批次不存在时报错。"""
    retrieve(archive, run_id)
    with archive.transaction() as db:
        rows = db.execute('SELECT payload FROM adjudications WHERE run_id=? ORDER BY seq',
                          (run_id,)).fetchall()
    return {'run_id': run_id, 'adjudications': [json.loads(row[0]) for row in rows]}


def recent(archive):
    with archive.transaction() as db:
        rows = db.execute('SELECT payload FROM runs ORDER BY rowid DESC LIMIT 30').fetchall()
    return {'runs': [json.loads(row[0])['manifest'] for row in rows]}
