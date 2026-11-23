from collections import Counter

from app.errors import TrackError
from app.reasons import REASONS
from .dialect import records
from .event import event_from_row
from .resolve import temporal_order


def scan(raw):
    events, rejects = [], []
    rows = repeated_headers = 0
    for line, record, header in records(raw):
        if tuple(record) == header:
            repeated_headers += 1
            continue
        rows += 1
        try:
            if not any(value.strip() for value in record):
                raise ValueError('EMPTY_ROW')
            if len(record) != len(header):
                raise ValueError('WIDTH')
            events.append(event_from_row(line, {key: val.strip() for key, val in zip(header, record)}))
        except ValueError as exc:
            code = str(exc)
            rejects.append({'line': line, 'reason': code, 'label': REASONS[code], 'raw': record})
    if not rows:
        raise TrackError('HEADER_ONLY')
    accepted, conflicts, duplicates = temporal_order(events)
    rejects.extend(conflicts)
    return {'input_rows': rows, 'sections': repeated_headers + 1, 'accepted': len(accepted),
            'isolated': len(rejects), 'duplicates': len(duplicates), 'events': accepted,
            'rejects': sorted(rejects, key=lambda row: row['line']), 'repeated': duplicates,
            'reasons': dict(Counter(row['reason'] for row in rejects))}
