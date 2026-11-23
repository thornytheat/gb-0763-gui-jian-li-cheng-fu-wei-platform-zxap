import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / 'sample_data'
DATABASE = os.getenv('TRACK_DB', 'var/track.sqlite')
REVISION = 'track-1.0'
GAP_SECONDS = 120
LATE_SECONDS = 900
MERGE_MM = 5000
