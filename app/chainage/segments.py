from collections import defaultdict
from datetime import datetime
from itertools import pairwise

from app.config import GAP_SECONDS
from app.reasons import evidence


def delimit(anchors):
    trains = defaultdict(list)
    for mark in anchors:
        trains[mark['run']].append(mark)
    spans = defaultdict(list)
    gaps = []
    for run, marks in trains.items():
        for left, right in pairwise(marks):
            elapsed = (datetime.fromisoformat(right['at']) - datetime.fromisoformat(left['at'])).total_seconds()
            why = None
            if left['chain'] != right['chain']:
                why = 'BREAK'
            elif elapsed <= 0 or elapsed > GAP_SECONDS:
                why = 'SIGNAL_GAP'
            elif right['odo_mm'] <= left['odo_mm']:
                why = 'ODO_REVERSAL'
            span = {'left': left, 'right': right, 'reason': why, 'seconds': int(elapsed)}
            spans[run].append(span)
            if why:
                gaps.append(dict(evidence(why, left, right), chain=left['chain'], next_chain=right['chain'],
                                 start_mm=left['station_mm'], end_mm=right['station_mm']))
    return spans, gaps
