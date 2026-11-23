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

    @contextmanager
    def transaction(self):
        db = sqlite3.connect(self.file, timeout=15)
        try:
            db.execute('PRAGMA foreign_keys=ON')
            with db:
                yield db
        finally:
            db.close()
