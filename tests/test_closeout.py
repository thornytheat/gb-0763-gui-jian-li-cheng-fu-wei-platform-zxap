import sqlite3

import pytest

from app.anchors.match import match
from app.anchors.register import survey_book
from app.archive.save import history, replay
from app.capture.scan import scan
from app.chainage.interpolate import restore
from app.defects.cluster import consolidate
from app.inputs import published_repairs, sample
from app.repairs.closeout import normalize, settle

HEADER = 'event_id,run,kind,at,odo_mm,ref,grade'
MARK, _PLAN = survey_book()


def verdict_of(lines, repairs):
    captured = scan(('\n'.join([HEADER] + lines)).encode())
    located = restore(captured['events'], match(captured['events'], MARK)['anchors'])
    clusters = consolidate(located['projected'])['clusters']
    return settle(repairs, located['segments'], clusters)['verdicts'][0]


BASE = ['a0,R1,anchor,2026-01-01T00:00:00Z,0,A0,3',
        'a1,R1,anchor,2026-01-01T00:01:00Z,100000,A1,3']

REPAIR = [{'repair_id': 'X', 'chain': 'UP-A', 'start_mm': 1000000, 'end_mm': 1090000,
           'repaired_at': '2025-12-31T00:00:00Z', 'title': '打磨'}]


def test_partial_repair_closes_verified_stretch(dirty):
    repairs = [{'repair_id': 'UP-A-1', 'chain': 'UP-A', 'start_mm': 1000000, 'end_mm': 1100000,
                'repaired_at': '2026-11-21T00:00:00Z', 'title': '打磨'}]
    verdict = settle(repairs, dirty['chainage']['segments'],
                     dirty['defects']['clusters'])['verdicts'][0]
    # 复巡只到 1020000 之前就重新报缺，销项止步于此，剩余恢复待修。
    assert verdict['closed_parts'] == [[1000000, 1020000]]
    assert verdict['closed_to_mm'] == 1020000
    assert verdict['status'] == 'PARTIAL'
    assert verdict['pending_parts'][0]['reason'] == 'DEFECT_REPORTED'


def test_closed_plus_pending_covers_item(dirty):
    repairs = [{'repair_id': f'R{index}', 'chain': chain, 'start_mm': lo, 'end_mm': hi,
                'repaired_at': '2026-11-21T00:00:00Z'}
               for index, (chain, lo, hi) in enumerate(
                   [('UP-A', 1000000, 1100000), ('UP-B', 2000000, 2400000),
                    ('DN-A', 400000, 500000)])]
    result = settle(repairs, dirty['chainage']['segments'], dirty['defects']['clusters'])
    for verdict in result['verdicts']:
        assert verdict['closed_mm'] + verdict['pending_mm'] == verdict['end_mm'] - verdict['start_mm']
    assert result['closed_mm'] + result['pending_mm'] == 600000


def test_pre_repair_coverage_cannot_close(dirty):
    # 维修时间设在复巡之后：全部覆盖都早于维修，一分都不能销。
    repairs = [{'repair_id': 'LATE', 'chain': 'DN-A', 'start_mm': 400000, 'end_mm': 500000,
                'repaired_at': '2027-01-01T00:00:00Z', 'title': '捣固'}]
    verdict = settle(repairs, dirty['chainage']['segments'],
                     dirty['defects']['clusters'])['verdicts'][0]
    assert verdict['closed_mm'] == 0
    assert verdict['status'] == 'PENDING'
    assert verdict['pending_parts'][0]['reason'] == 'PRE_REPAIR_ONLY'


def test_uncovered_stretch_stays_pending(dirty):
    # UP-B 中间 2100000–2300000 复巡没走过，不能算销。
    repairs = [{'repair_id': 'UP-B-1', 'chain': 'UP-B', 'start_mm': 2000000, 'end_mm': 2400000,
                'repaired_at': '2026-11-21T00:00:00Z', 'title': '换轨'}]
    verdict = settle(repairs, dirty['chainage']['segments'],
                     dirty['defects']['clusters'])['verdicts'][0]
    reasons = {part['reason'] for part in verdict['pending_parts']}
    assert 'NOT_COVERED' in reasons
    assert [part for part in verdict['pending_parts']
            if part['reason'] == 'NOT_COVERED'][0]['start_mm'] == 2100000


def test_fully_verified_item_is_closed():
    verdict = verdict_of(BASE, REPAIR)
    assert verdict['status'] == 'CLOSED'
    assert verdict['closed_to_mm'] == 1090000 and verdict['pending_mm'] == 0


def test_late_recheck_restores_closed_stretch():
    # 复巡先走过全线，随后迟到窗口内的第二车次在 1060000 重新报缺：该段退回待修。
    late = BASE + ['b0,R2,anchor,2026-01-01T00:00:00Z,0,A0,3',
                   'b1,R2,anchor,2026-01-01T00:02:00Z,100000,A1,3',
                   'd2,R2,defect,2026-01-01T00:01:00Z,60000,裂纹,2']
    verdict = verdict_of(late, REPAIR)
    assert verdict['closed_parts'] == [[1000000, 1060000]]
    assert verdict['blockers'] == ['DEFECT_REPORTED']
    pending = verdict['pending_parts'][0]
    assert (pending['start_mm'], pending['end_mm'], pending['sources']) == (1060000, 1090000, [6])


def test_reports_before_repair_do_not_block():
    # 维修前的报缺已被修复，不该再拦住销项。
    earlier = BASE + ['d0,R1,defect,2025-12-30T00:00:00Z,60000,裂纹,2']
    verdict = verdict_of(earlier, REPAIR)
    assert verdict['status'] in ('CLOSED', 'PARTIAL')
    assert all(part['reason'] != 'DEFECT_REPORTED' for part in verdict['pending_parts'])


def test_normalize_rejects_bad_records():
    good = REPAIR[0]
    for bad in ({**good, 'start_mm': 'x'}, {**good, 'start_mm': 5, 'end_mm': 5},
                {**good, 'repaired_at': '2026-01-01T00:00:00'}, {**good, 'extra': 1},
                {k: v for k, v in good.items() if k != 'chain'}):
        with pytest.raises(Exception):
            normalize([bad])
    with pytest.raises(Exception):
        normalize([good, good])


def test_closeout_api_and_stage(client):
    result = client.get('/api/repairs?sample=dirty').json
    assert result['item_count'] == 4 and result['closed_mm'] > 0


def test_bad_repair_body(client):
    response = client.post('/api/repairs', json={'sample': 'dirty', 'repairs': [{'repair_id': ''}]})
    assert (response.status_code, response.json['error']) == (422, 'BAD_REPAIR')


def test_summary_carries_closeout(client):
    manifest = client.post('/api/runs', json={'sample': 'dirty'}).json
    assert manifest['summary']['closed_mm'] > 0
    assert manifest['summary']['repair_count'] == 4


def test_archive_history_is_queryable(client):
    run_id = client.post('/api/runs', json={'sample': 'dirty'}).json['run_id']
    rows = client.get(f'/api/runs/{run_id}/adjudications').json['adjudications']
    assert [row['repair_id'] for row in rows] == ['WR-103', 'WR-101', 'WR-104', 'WR-102']


def test_rerun_same_batch_does_not_double_close(client, archive_app):
    first = client.post('/api/runs', json={'sample': 'dirty'}).json
    again = client.post('/api/runs', json={'sample': 'dirty'}).json
    assert again['reused'] and again['run_id'] == first['run_id']
    with archive_app.track_archive.transaction() as db:
        count = db.execute('SELECT COUNT(*) FROM adjudications WHERE run_id=?',
                           (first['run_id'],)).fetchone()[0]
    assert count == 4


def test_repaired_identity_changes_with_items(client):
    plain = client.post('/api/runs', json={'sample': 'dirty'}).json
    altered = client.post('/api/runs', json={
        'sample': 'dirty',
        'repairs': [{'repair_id': 'X', 'chain': 'UP-A', 'start_mm': 1000000,
                     'end_mm': 1100000, 'repaired_at': '2026-11-21T00:00:00Z'}]}).json
    assert plain['run_id'] != altered['run_id']


def test_failed_archive_is_retryable(archive_app):
    archive = archive_app.track_archive
    items = published_repairs('dirty')
    with archive.transaction() as db:
        db.execute("CREATE TRIGGER fail_closeout BEFORE INSERT ON adjudications "
                   "BEGIN SELECT RAISE(ABORT, 'fault'); END")
    with pytest.raises(sqlite3.IntegrityError):
        replay(archive, sample('dirty'), items)
    # 半份快照未发布：批次与裁定都没有落库。
    assert archive_app.test_client().get('/api/runs').json == {'runs': []}
    with archive.transaction() as db:
        db.execute('DROP TRIGGER fail_closeout')
    result = replay(archive, sample('dirty'), items)
    assert result['summary']['repair_count'] == 4
    assert len(archive_app.test_client().get('/api/runs').json['runs']) == 1


def test_replay_signature_accepts_repairs(archive_app):
    data = replay(archive_app.track_archive, sample('clean'), [])
    assert data['summary']['repair_count'] == 0
    history(archive_app.track_archive, data['run_id'])  # 无裁定也不报错
