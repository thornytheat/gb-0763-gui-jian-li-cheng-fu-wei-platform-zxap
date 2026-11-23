from app.anchors.match import match
from app.anchors.register import survey_book


def test_best_grade_is_order_independent(dirty):  # TRAP-19
    events = dirty['capture']['events']
    marks, _ = survey_book()
    result = match(list(reversed(events)), marks)
    assert result['anchors'] == dirty['anchors']['anchors']
    assert next(a['sources'] for a in result['discarded'] if a['reason']=='LOW_GRADE') == [23,3]


def test_unregistered_mark(dirty):
    assert dirty['anchors']['discarded'][0]['sources'] == [24]
    assert dirty['anchors']['discarded'][0]['reason'] == 'UNKNOWN_MARK'


def test_top_tie_leaves_no_point(dirty):
    original = dirty['anchors']['anchors'][0]
    result = match([original, dict(original, line=78, odo_mm=1)], survey_book()[0])
    assert result['matched'] == 0
    assert result['discarded'][0]['reason'] == 'ANCHOR_TIE'


def test_identical_mark_uses_first_line(dirty):
    original = dirty['anchors']['anchors'][0]
    result = match([dict(original, line=78), original], survey_book()[0])
    assert result['discarded'][0]['sources'] == [78,2]


def test_other_train_retains_own_calibration(dirty):
    assert [a['run'] for a in dirty['anchors']['anchors'] if a['ref']=='A0'] == ['R7','R9']


def test_unknown_sample_rejected(client):
    result = client.get('/api/anchors?sample=wrong')
    assert (result.status_code, result.json['error']) == (404, 'NO_SAMPLE')
