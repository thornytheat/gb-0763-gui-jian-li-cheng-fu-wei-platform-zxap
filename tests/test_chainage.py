from app.chainage.interpolate import restore


def test_cut_belongs_to_next_span(dirty):  # TRAP-23
    data = dirty['chainage']
    assert next(p['chain'] for p in data['projected'] if p['event_id']=='p4') == 'UP-B'
    assert next(p['reason'] for p in data['unmapped'] if p['event_id']=='break') == 'BREAK'


def test_downward_station(dirty):
    p = next(p for p in dirty['chainage']['projected'] if p['event_id']=='dp')
    assert (p['station_mm'], p['chain'], p['anchor_lines']) == (470000, 'DN-A', [17,18])


def test_no_extrapolation(dirty):
    assert dirty['chainage']['unmapped'][-1]['reason'] == 'NO_BRACKET'


def test_loss_and_reversal(dirty):
    expect = {'p3':'ODO_REVERSAL', 'loss':'SIGNAL_GAP'}
    assert {p['event_id']:p['reason'] for p in dirty['chainage']['unmapped'] if p['event_id'] in expect} == expect


def test_exact_right_odometer_disallowed(dirty):
    point = dict(dirty['chainage']['projected'][0], odo_mm=100000)
    result = restore([point], dirty['anchors']['anchors'])
    assert result['unmapped'][0]['reason'] == 'OUTSIDE_ODO'


def test_requires_full_anchor_pair(dirty):
    point = dirty['chainage']['projected'][0]
    assert restore([point], [dirty['anchors']['anchors'][0]])['unmapped'][0]['reason'] == 'NO_BRACKET'
