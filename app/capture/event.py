from datetime import datetime, timezone

from .dialect import MISSING


def event_from_row(line, raw):
    if any(value == '' or value in MISSING for value in raw.values()):
        raise ValueError('MISSING')
    try:
        at = datetime.fromisoformat(raw['at'])
        odo = int(raw['odo_mm'])
        grade = int(raw['grade'])
        if at.utcoffset() is None or not 0 <= odo <= 10**12 or grade not in (1, 2, 3):
            raise ValueError
        if raw['kind'] not in ('anchor', 'defect'):
            raise ValueError
    except (ValueError, OverflowError) as exc:
        raise ValueError('FORMAT') from exc
    return dict(raw, line=line, at=at.astimezone(timezone.utc).isoformat(), odo_mm=odo, grade=grade)
