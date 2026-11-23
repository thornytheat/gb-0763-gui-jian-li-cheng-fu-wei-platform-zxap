from bisect import bisect_right

from app.reasons import REASONS
from .intervals import intersect, measure, subtract, union


def _as_interval(item):
    """有效区间有两种形态：双基点 span（left/right）或已摊平的链区间。

    下行链标称里程递减（见 TRAP 下行链），统一折算成低/高端点的半开区间。
    """
    if 'left' in item:
        chain, lo, hi = item['left']['chain'], item['left']['station_mm'], item['right']['station_mm']
    else:
        chain, lo, hi = item['chain'], item['start_mm'], item['end_mm']
    return chain, min(lo, hi), max(lo, hi)


def _group_by_chain(items):
    grouped = {}
    for item in items:
        chain, lo, hi = _as_interval(item)
        grouped.setdefault(chain, []).append((lo, hi))
    return grouped


def _group_plans(items):
    grouped = {}
    for item in items:
        grouped.setdefault(item['chain'], []).append(item)
    return grouped


def _gap_lookup(gaps):
    lookup = {}
    for chain, items in _group_plans(gaps).items():
        ordered = sorted(items, key=lambda gap: gap['start_mm'])
        lookup[chain] = ([gap['start_mm'] for gap in ordered], ordered)
    return lookup


def _explain(chain, lo, hi, gap_index):
    entry = gap_index.get(chain)
    if entry is None:
        return ['NO_COVERAGE'], []
    starts, ordered = entry
    hits = []
    pos = bisect_right(starts, lo)
    candidates = ordered[max(0, pos - 1):pos + 1] + ordered[pos + 1:pos + 3]
    for gap in candidates:
        if gap['start_mm'] < hi and gap['end_mm'] > lo:
            hits.append(gap)
    if not hits:
        return ['NO_COVERAGE'], []
    reasons, sources = [], []
    for gap in hits:
        for reason in gap['reasons'] if 'reasons' in gap else [gap['reason']]:
            if reason not in reasons:
                reasons.append(reason)
        for line in gap['sources']:
            if line not in sources:
                sources.append(line)
    return reasons, sources


def balance(plan, segments, gaps):
    gap_index = _gap_lookup(gaps)
    planned = _group_plans(plan)
    effective = _group_by_chain(segments)

    tracks, missing_parts = [], []
    planned_mm = mapped_mm = raw_mm = 0
    for chain in sorted(planned):
        plan_parts = union((item['start_mm'], item['end_mm']) for item in planned[chain])
        raw_parts = union(effective.get(chain, []))
        credited = intersect(plan_parts, raw_parts)
        uncovered = subtract(plan_parts, raw_parts)
        chain_missing = []
        for lo, hi in uncovered:
            reasons, sources = _explain(chain, lo, hi, gap_index)
            part = {'chain': chain, 'start_mm': lo, 'end_mm': hi, 'reasons': reasons, 'sources': sources}
            chain_missing.append(part)
            missing_parts.append(part)
        chain_planned, chain_mapped = measure(plan_parts), measure(credited)
        # 原始长度先逐段裁剪到计划再求和：直接求并集会吞掉同段多车巡检的重复长度。
        chain_raw = sum(measure(intersect(plan_parts, [(lo, hi)]))
                        for lo, hi in effective.get(chain, []))
        planned_mm += chain_planned
        mapped_mm += chain_mapped
        raw_mm += chain_raw
        start_mm = plan_parts[0][0]
        tracks.append({'chain': chain, 'start_mm': start_mm, 'end_mm': plan_parts[-1][1],
                       'planned_mm': chain_planned, 'mapped_mm': chain_mapped,
                       'mapped_parts': credited})
    missing_mm = planned_mm - mapped_mm
    return {'planned_mm': planned_mm, 'mapped_mm': mapped_mm, 'missing_mm': missing_mm,
            'overlap_mm': raw_mm - mapped_mm, 'tracks': tracks, 'missing_parts': missing_parts,
            'reason_labels': {code: REASONS[code] for code in REASONS if
                              code in {r for part in missing_parts for r in part['reasons']}}}
