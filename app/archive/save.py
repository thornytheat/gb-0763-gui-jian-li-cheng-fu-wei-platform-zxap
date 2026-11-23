from datetime import datetime, timezone
import json
from time import perf_counter

from app.config import GAP_SECONDS, LATE_SECONDS, MERGE_MM, REVISION
from app.errors import TrackError
from app.manifest import canonical, digest
from app.pipeline import inspect
from app.anchors.register import survey_book


def retrieve(archive, run_id):
    with archive.transaction() as db:
        record = db.execute('SELECT payload FROM runs WHERE id=?', (run_id,)).fetchone()
    if record is None:
        raise TrackError('RUN_MISSING', 404)
    return json.loads(record[0])


def replay(archive, raw):
    started = perf_counter()
    survey = survey_book()
    evidence = inspect(raw, survey=survey)
    parameters = {'gap_s': GAP_SECONDS, 'late_s': LATE_SECONDS, 'merge_mm': MERGE_MM}
    identity = {'input_sha256': digest(raw), 'survey_sha256': digest(canonical(survey)),
                'revision': REVISION, 'parameters': parameters}
    run_id = digest(canonical(identity))
    summary = {key: evidence['coverage'][key] for key in ('planned_mm', 'mapped_mm', 'missing_mm', 'overlap_mm')}
    manifest = dict(identity, run_id=run_id, created_at=datetime.now(timezone.utc).isoformat(),
                    elapsed_ms=round((perf_counter() - started) * 1000), summary=summary)
    with archive.transaction() as db:
        inserted = db.execute('INSERT OR IGNORE INTO runs VALUES (?, ?)',
                              (run_id, canonical({'manifest': manifest, 'stages': evidence}))).rowcount
        previous = db.execute('SELECT payload FROM runs WHERE id=?', (run_id,)).fetchone()[0]
    return dict(json.loads(previous)['manifest'], reused=not bool(inserted))


def recent(archive):
    with archive.transaction() as db:
        rows = db.execute('SELECT payload FROM runs ORDER BY rowid DESC LIMIT 30').fetchall()
    return {'runs': [json.loads(row[0])['manifest'] for row in rows]}
