from app.anchors.match import match
from app.anchors.register import survey_book
from app.capture.scan import scan
from app.chainage.interpolate import restore
from app.coverage.balance import balance
from app.defects.cluster import consolidate
from app.repairs.closeout import settle

STAGES = ('capture', 'anchors', 'chainage', 'defects', 'coverage', 'repairs')


def inspect(raw, until='coverage', *, survey=None, repairs=None):
    captured = scan(raw)
    results = {'capture': captured}
    if until == 'capture':
        return results
    marks, plan = survey if survey is not None else survey_book()
    anchors = match(captured['events'], marks)
    results['anchors'] = anchors
    if until == 'anchors':
        return results
    located = restore(captured['events'], anchors['anchors'])
    results['chainage'] = located
    if until == 'chainage':
        return results
    defects = consolidate(located['projected'])
    if until == 'defects':
        return dict(results, defects=defects)
    coverage = balance(plan, located['segments'], located['gaps'])
    results.update(defects=defects, coverage=coverage)
    # 销项只认维修后覆盖与归并后的报缺，故在覆盖与缺陷都算完之后再裁定。
    if until == 'coverage' and repairs is None:
        return results
    results['repairs'] = settle(repairs, located['segments'], defects['clusters'])
    return results
