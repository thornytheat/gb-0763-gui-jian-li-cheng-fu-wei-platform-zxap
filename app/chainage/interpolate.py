from bisect import bisect_right
from decimal import Decimal, ROUND_HALF_UP

from app.reasons import evidence
from .segments import delimit


def restore(events, anchors):
    spans, gaps = delimit(anchors)
    boundaries = {run: [span['left']['at'] for span in items] for run, items in spans.items()}
    progress, projected, missing = {}, [], []
    for event in events:
        if event['kind'] != 'defect':
            continue
        run, odo = event['run'], event['odo_mm']
        index = bisect_right(boundaries.get(run, ()), event['at']) - 1
        span = spans[run][index] if index >= 0 else None
        why, sources = 'NO_BRACKET', [event]
        if span and event['at'] < span['right']['at']:
            a, b = span['left'], span['right']
            sources.extend((a, b))
            why = span['reason']
            if not why and not a['odo_mm'] <= odo < b['odo_mm']:
                why = 'OUTSIDE_ODO'
            if not why and odo < progress.get((run, index), odo):
                why = 'ODO_REVERSAL'
            if not why:
                progress[run, index] = odo
                delta = Decimal((odo - a['odo_mm']) * (b['station_mm'] - a['station_mm']))
                relative = delta / (b['odo_mm'] - a['odo_mm'])
                station = int((a['station_mm'] + relative).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
                projected.append(dict(event, station_mm=station, chain=a['chain'], marks=[a['ref'], b['ref']],
                                      anchor_lines=[a['line'], b['line']]))
                continue
        missing.append(dict(evidence(why, *sources), event_id=event['event_id'], raw=event))
    usable = [span for group in spans.values() for span in group if not span['reason']]
    return {'projected_count': len(projected), 'unmapped_count': len(missing), 'projected': projected,
            'unmapped': missing, 'segments': usable, 'gaps': gaps}
