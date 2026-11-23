"""维修项销项裁定。

修后复巡常常只走过维修项的一截。班组交班前要销掉已验的部分：整项一起销会漏验，
等全段走完又耽误交班。一个维修项能销到哪，由两件事共同决定：

* **复位覆盖** —— 只认维修完成之后复位出来的有效双基点区间。维修前的覆盖不能拿来
  销项，否则会把旧巡检当成修复后的复核。
* **归并后的报缺** —— 缺陷归并后的缺陷群就是复巡仍在报的缺。每段连续覆盖从段起点
  量到段内第一处报缺为止才可销；报缺之后的里程尚未确认修好，恢复待修。

于是每项先取维修后覆盖与维修项范围的交集，逐段截到本段第一处报缺，剩下的
``closed_parts`` 才是可销的部分；交班看的 ``closed_to_mm`` 是从维修项起点连续销出去
的位置。剩余里程逐段标回待修原因：复巡仍在报缺（``DEFECT_REPORTED``）、只有维修前覆盖
（``PRE_REPAIR_ONLY``）、复巡未覆盖到（``NOT_COVERED``）。

迟到记录在已销位置重新报缺时，缺陷归并会把它算进缺陷群，重算后该段从已销里扣回、
恢复待修。裁定只由输入报文、维修项与测绘表确定：归档失败整笔回滚可重试，重跑同一
批次命中运行键取回同一份结果，不重复销项。
"""
from datetime import datetime, timezone

from app.coverage.intervals import measure, subtract, union
from app.errors import TrackError
from app.reasons import REASONS

FIELDS = frozenset({'repair_id', 'chain', 'start_mm', 'end_mm', 'repaired_at', 'title'})
REQUIRED = frozenset({'repair_id', 'chain', 'start_mm', 'end_mm', 'repaired_at'})
LIMIT_MM = 10**12


def _instant(value):
    if not isinstance(value, str):
        raise TrackError('BAD_REPAIR')
    try:
        moment = datetime.fromisoformat(value)
    except ValueError as exc:
        raise TrackError('BAD_REPAIR') from exc
    if moment.utcoffset() is None:
        raise TrackError('BAD_REPAIR')
    return moment.astimezone(timezone.utc).isoformat()


def _count(value):
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= LIMIT_MM:
        raise TrackError('BAD_REPAIR')
    return value


def normalize(items):
    """校验维修项并折算成半开区间；同一标识只允许一条，供归档键复跑去重。

    维修项以位置区间表示，低端点为起点、高端点为终点，下行链按同一长度计。
    ``repaired_at`` 统一到 UTC，作为区分维修前后覆盖的分界。
    """
    if items is None:
        return []
    if not isinstance(items, list):
        raise TrackError('BAD_REPAIR')
    seen = set()
    cleaned = []
    for item in items:
        if not isinstance(item, dict) or set(item) - FIELDS or not REQUIRED <= set(item):
            raise TrackError('BAD_REPAIR')
        repair_id, chain = item['repair_id'], item['chain']
        if not isinstance(repair_id, str) or not repair_id.strip() or repair_id in seen:
            raise TrackError('BAD_REPAIR')
        if not isinstance(chain, str) or not chain.strip():
            raise TrackError('BAD_REPAIR')
        lo, hi = _count(item['start_mm']), _count(item['end_mm'])
        if lo >= hi:
            raise TrackError('BAD_REPAIR')
        title = item.get('title', '')
        if title is None:
            title = ''
        if not isinstance(title, str):
            raise TrackError('BAD_REPAIR')
        seen.add(repair_id)
        cleaned.append({'repair_id': repair_id, 'chain': chain, 'start_mm': lo, 'end_mm': hi,
                        'repaired_at': _instant(item['repaired_at']), 'title': title})
    cleaned.sort(key=lambda item: (item['chain'], item['start_mm'], item['repair_id']))
    return cleaned


def _clip(intervals, lo, hi):
    return union((max(start, lo), min(end, hi)) for start, end in intervals
                 if min(end, hi) > max(start, lo))


def _coverage(segments, chain, lo, hi, repaired_at, *, post):
    pieces = []
    for span in segments:
        left, right = span['left'], span['right']
        if left['chain'] != chain:
            continue
        after = datetime.fromisoformat(left['at']) >= datetime.fromisoformat(repaired_at)
        if after != post:
            continue
        pieces.append(tuple(sorted((left['station_mm'], right['station_mm']))))
    return _clip(pieces, lo, hi)


def _reports(clusters, chain, lo, hi, repaired_at):
    """复巡在维修后仍报缺的观测，带报文证据，按里程排序。"""
    points = []
    for cluster in clusters:
        if cluster['chain'] != chain:
            continue
        for item in cluster.get('observations', ()):
            station = item['station_mm']
            if not lo <= station < hi:
                continue
            if datetime.fromisoformat(item['at']) < datetime.fromisoformat(repaired_at):
                continue
            points.append({'station_mm': station, 'event_id': item['event_id'],
                           'line': item['line'], 'run': item['run']})
    points.sort(key=lambda point: (point['station_mm'], point['line']))
    return points


def _split(runs, points):
    """每段连续覆盖截到段内第一处报缺，返回 (可销片段, 报缺后待修片段)。"""
    closed, blocked = [], []
    for start, end in runs:
        limit = end
        for point in points:
            if point['station_mm'] < start:
                continue
            if point['station_mm'] >= end:
                break
            limit = point['station_mm']
            break
        if limit > start:
            closed.append((start, limit))
        if end > limit:
            blocked.append((limit, end))
    return union(closed), union(blocked)


def _reason_parts(lo, hi, closed, post, pre, blocked, points):
    parts = []
    for start, end in subtract([(lo, hi)], closed):
        cuts = sorted({start, end}
                      | {mark for interval in post + pre + blocked
                         for mark in interval if start < mark < end}
                      | {point['station_mm'] for point in points if start < point['station_mm'] < end})
        for a, b in zip(cuts, cuts[1:]):
            reported = any(s <= a < e for s, e in blocked) or any(
                a <= point['station_mm'] < b for point in points)
            if reported:
                reason = 'DEFECT_REPORTED'
            elif any(s <= a < e for s, e in pre) and not any(s <= a < e for s, e in post):
                reason = 'PRE_REPAIR_ONLY'
            else:
                reason = 'NOT_COVERED'
            hits = [point for point in points if a <= point['station_mm'] < b]
            if parts and parts[-1]['reason'] == reason and parts[-1]['end_mm'] == a:
                parts[-1]['end_mm'] = b
                parts[-1]['sources'] = sorted(set(parts[-1]['sources'])
                                              | {point['line'] for point in hits})
                parts[-1]['events'] = parts[-1]['events'] + [p['event_id'] for p in hits]
                continue
            parts.append({'chain': None, 'start_mm': a, 'end_mm': b, 'reason': reason,
                          'label': REASONS[reason],
                          'sources': sorted({point['line'] for point in hits}),
                          'events': [point['event_id'] for point in hits]})
    return parts


def _closed_to(lo, closed):
    """从维修项起点连续销出去的位置，交班用它回答「销到哪」。"""
    cursor = lo
    for start, end in closed:
        if start > cursor:
            break
        if end > cursor:
            cursor = end
    return cursor


def adjudicate(item, segments, clusters):
    """对单个维修项给出销项裁定。"""
    lo, hi = item['start_mm'], item['end_mm']
    repaired_at = item['repaired_at']
    post = _coverage(segments, item['chain'], lo, hi, repaired_at, post=True)
    pre = _coverage(segments, item['chain'], lo, hi, repaired_at, post=False)
    points = _reports(clusters, item['chain'], lo, hi, repaired_at)

    closed, blocked = _split(post, points)
    pending_parts = _reason_parts(lo, hi, closed, post, pre, blocked, points)
    for part in pending_parts:
        part['chain'] = item['chain']

    closed_mm = measure(closed)
    pending_mm = (hi - lo) - closed_mm
    blockers = []
    for part in pending_parts:
        if part['reason'] not in blockers:
            blockers.append(part['reason'])
    status = 'CLOSED' if pending_mm == 0 else 'PENDING' if closed_mm == 0 else 'PARTIAL'
    return {'repair_id': item['repair_id'], 'chain': item['chain'], 'title': item['title'],
            'start_mm': lo, 'end_mm': hi, 'repaired_at': repaired_at,
            'closed_parts': closed, 'pending_parts': pending_parts,
            'closed_mm': closed_mm, 'pending_mm': pending_mm,
            'closed_to_mm': _closed_to(lo, closed), 'status': status, 'blockers': blockers}


def settle(items, segments, clusters):
    """对一组维修项逐项裁定并汇总。"""
    normalized = normalize(items)
    verdicts = [adjudicate(item, segments, clusters) for item in normalized]
    return {'item_count': len(verdicts),
            'closed_mm': sum(item['closed_mm'] for item in verdicts),
            'pending_mm': sum(item['pending_mm'] for item in verdicts),
            'verdicts': verdicts}
