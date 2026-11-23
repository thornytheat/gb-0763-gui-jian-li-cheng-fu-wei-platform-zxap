from app.coverage.balance import balance
from app.coverage.intervals import union


def test_conservation(dirty):
    result = dirty['coverage']
    assert result['planned_mm'] == result['mapped_mm'] + result['missing_mm'] == 600000


def test_duplicate_coverage(dirty):
    assert (dirty['coverage']['mapped_mm'], dirty['coverage']['overlap_mm']) == (400000,100000)


def test_gap_explained(dirty):
    assert dirty['coverage']['missing_parts'] == [dict(chain='UP-B', start_mm=2100000, end_mm=2300000,
                                                      reasons=['SIGNAL_GAP'], sources=[5,6])]


def test_unplanned_chain_does_not_credit(dirty):
    result = balance([dict(chain='NONE',start_mm=1000000,end_mm=1100000)], dirty['chainage']['segments'], [])
    assert (result['mapped_mm'], result['missing_mm']) == (0, 100000)


def test_touching_and_contained():
    assert union([(0,7),(7,10),(1,2),(19,19)]) == [[0,10]]


def test_clean_api(client):
    result = client.get('/api/coverage?sample=clean').json
    assert (result['mapped_mm'], result['missing_parts']) == (600000,[])
