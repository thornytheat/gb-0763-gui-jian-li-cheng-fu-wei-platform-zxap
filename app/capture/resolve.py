from collections import defaultdict
from datetime import datetime

from app.config import LATE_SECONDS
from app.reasons import evidence


def temporal_order(events):
    grouped = defaultdict(list)
    for event in events:
        grouped[event['event_id']].append(event)
    accepted, rejected, repeats = [], [], []
    for group in grouped.values():
        head = group[0]
        keys = head.keys() - {'line'}
        if any(any(item[key] != head[key] for key in keys) for item in group[1:]):
            rejected.extend(dict(evidence('ID_CONFLICT', *group), line=item['line'], raw=item) for item in group)
        else:
            accepted.append(head)
            repeats.extend({'line': event['line'], 'kept_line': head['line']} for event in group[1:])
    watermark = {}
    ordered = []
    for item in accepted:
        at = datetime.fromisoformat(item['at'])
        previous = watermark.get(item['run'], at)
        late = int((previous - at).total_seconds())
        if late > LATE_SECONDS:
            rejected.append(dict(evidence('LATE_LIMIT', item), line=item['line'], raw=item))
            continue
        watermark[item['run']] = max(at, previous)
        ordered.append(dict(item, late_s=max(0, late)))
    return sorted(ordered, key=lambda e: (e['run'], e['at'], e['line'])), rejected, repeats
