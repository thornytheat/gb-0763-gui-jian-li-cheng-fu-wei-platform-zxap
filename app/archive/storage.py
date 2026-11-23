from contextlib import contextmanager
from pathlib import Path
import sqlite3


class TrackArchive:
    def __init__(self, filename):
        self.file = Path(filename)
        self.file.parent.mkdir(parents=True, exist_ok=True)
        with self.transaction() as db:
            db.execute('CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, payload BLOB NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS issues (run_id TEXT PRIMARY KEY REFERENCES runs(id), seal TEXT NOT NULL)')
            # 历次裁定留档：每次归档按维修项记一条销项结论，供批次页回查。
            db.execute('CREATE TABLE IF NOT EXISTS adjudications '
                       '(run_id TEXT NOT NULL REFERENCES runs(id), repair_id TEXT NOT NULL, '
                       'seq INTEGER NOT NULL, payload BLOB NOT NULL, '
                       'PRIMARY KEY (run_id, repair_id))')
            db.execute('CREATE INDEX IF NOT EXISTS idx_adjudications_run ON adjudications(run_id, seq)')

    @contextmanager
    def transaction(self):
        db = sqlite3.connect(self.file, timeout=15)
        try:
            db.execute('PRAGMA foreign_keys=ON')
            with db:
                yield db
        finally:
            db.close()
