from app.inputs import sample
from app.capture.scan import scan


def test_bom(dirty):  # TRAP-02
    assert sample('dirty').startswith(b'\xef\xbb\xbf')
    assert dirty['capture']['events'][0]['event_id'] == 'a0'


def test_sections(dirty):  # TRAP-04
    assert (dirty['capture']['sections'], dirty['capture']['input_rows']) == (2, 28)


def test_width(dirty):  # TRAP-05
    assert [(r['line'], r['raw'][-1]) for r in dirty['capture']['rejects'] if r['reason']=='WIDTH'] == [(28, '余列')]


def test_sentinel(dirty):  # TRAP-07
    assert dirty['capture']['reasons']['MISSING'] == 1
    assert 'missing' not in {r['event_id'] for r in dirty['capture']['events']}


def test_offset_collapses_repeat(dirty):  # TRAP-11
    assert dirty['capture']['repeated'] == [{'line': 30, 'kept_line': 8}]
    assert next(r['at'] for r in dirty['capture']['events'] if r['event_id']=='p1') == '2026-11-22T00:00:10+00:00'


def test_late_window(dirty):  # TRAP-13
    assert next(r['late_s'] for r in dirty['capture']['events'] if r['event_id']=='p1') == 530
    assert dirty['capture']['reasons']['LATE_LIMIT'] == 1


def test_conflict_keeps_both_sources(dirty):  # TRAP-14
    assert [row['sources'] for row in dirty['capture']['rejects'] if row['reason']=='ID_CONFLICT'] == [[25,26],[25,26]]


def test_three_empty_states(client):
    from app.capture.dialect import FIELDS
    for text, code in [('', 'EMPTY_FILE'), ('\n', 'BLANK_FILE'), (','.join(FIELDS), 'HEADER_ONLY')]:
        response = client.post('/api/capture', json={'csv': text})
        assert (response.status_code, response.json['error']) == (422, code)


def test_clean_accepts_every_row():
    result = scan(sample('clean'))
    assert (result['accepted'], result['isolated'], result['duplicates']) == (13, 0, 0)
