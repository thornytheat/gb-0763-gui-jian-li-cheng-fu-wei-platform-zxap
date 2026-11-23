from collections import defaultdict

from app.reasons import evidence


def match(events, survey):
    buckets = defaultdict(list)
    discarded, anchors = [], []
    for event in events:
        if event['kind'] != 'anchor':
            continue
        mark = survey.get(event['ref'])
        if mark is None:
            discarded.append(evidence('UNKNOWN_MARK', event))
            continue
        buckets[event['run'], event['ref']].append(dict(event, **mark))
    for candidates in buckets.values():
        ranked = sorted(candidates, key=lambda point: (-point['grade'], point['line']))
        best = ranked[0]
        peers = [point for point in ranked if point['grade'] == best['grade']]
        discarded.extend(evidence('LOW_GRADE', point, best) for point in ranked[len(peers):])
        if len({(point['at'], point['odo_mm']) for point in peers}) > 1:
            discarded.append(evidence('ANCHOR_TIE', *peers))
            continue
        anchors.append(best)
        discarded.extend(evidence('ANCHOR_REPEAT', point, best) for point in peers[1:])
    return {'matched': len(anchors), 'anchors': sorted(anchors, key=lambda a: (a['run'], a['at'], a['line'])),
            'discarded': discarded}
