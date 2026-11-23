from app.anchors.match import match
from app.anchors.register import survey_book
from app.capture.scan import scan
from app.chainage.interpolate import restore
from app.coverage.balance import balance
from app.defects.cluster import consolidate

STAGES = ('capture', 'anchors', 'chainage', 'defects', 'coverage')


def inspect(raw, until='coverage', *, survey=None):
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
    if until != 'coverage':
        return dict(results, defects=consolidate(located['projected']))
    return dict(results, defects=consolidate(located['projected']),
                coverage=balance(plan, located['segments'], located['gaps']))
