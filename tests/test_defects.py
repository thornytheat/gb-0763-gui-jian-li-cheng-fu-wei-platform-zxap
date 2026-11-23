from app.defects.cluster import consolidate


def test_real_members(dirty):
    assert dirty['defects']['clusters'][1]['members'] == ['p1','p2','rp']


def test_member_sources(dirty):
    assert dirty['defects']['clusters'][1]['sources'] == [8,9,22]


def test_no_transitive_spread(dirty):
    p = dirty['chainage']['projected'][0]
    points = [dict(p, station_mm=n, event_id=str(n)) for n in (0,5000,5001)]
    assert [r['members'] for r in consolidate(points)['clusters']] == [['0','5000'],['5001']]


def test_other_branch_not_merged(dirty):
    p = dirty['chainage']['projected'][0]
    assert consolidate([p, dict(p, chain='ANOTHER')])['clusters_count'] == 2


def test_other_defect_type_not_merged(dirty):
    p = dirty['chainage']['projected'][0]
    assert consolidate([p, dict(p, ref='崩边')])['merged'] == 0


def test_empty_cluster():
    assert consolidate([]) == {'observations':0,'clusters_count':0,'clusters':[],'merged':0}
