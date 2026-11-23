from app.archive.save import retrieve
from app.errors import TrackError
from .packet import fingerprint, packet


def issue(archive, run_id):
    document = packet(retrieve(archive, run_id))
    seal = fingerprint(document)
    with archive.transaction() as db:
        issued = db.execute('INSERT OR IGNORE INTO issues VALUES (?, ?)', (run_id, seal)).rowcount
        committed = db.execute('SELECT seal FROM issues WHERE run_id=?', (run_id,)).fetchone()[0]
    return {'run_id': run_id, 'seal': committed, 'reused': not bool(issued), 'issued': True}


def verified(archive, run_id):
    data = packet(retrieve(archive, run_id))
    with archive.transaction() as db:
        saved = db.execute('SELECT seal FROM issues WHERE run_id=?', (run_id,)).fetchone()
    if saved is None:
        raise TrackError('NOT_ISSUED', 409)
    return {'seal': saved[0], 'verified': saved[0] == fingerprint(data), 'evidence': data}
