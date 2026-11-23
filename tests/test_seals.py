from app.seals.packet import fingerprint


def run_path(client):
    return '/api/runs/' + client.post('/api/runs', json={'sample':'dirty'}).json['run_id']


def test_unsigned_cannot_download(client):
    response = client.get(run_path(client)+'/export')
    assert (response.status_code,response.json['error']) == (409,'NOT_ISSUED')


def test_issue_idempotent(client):
    path = run_path(client)+'/issue'
    first = client.post(path).json
    assert client.post(path).json == dict(first, reused=True)


def test_attachment_fingerprint(client):
    path = run_path(client)
    seal = client.post(path+'/issue').json['seal']
    result = client.get(path+'/export')
    assert result.headers['Content-Disposition'].startswith('attachment;')
    assert result.json['verified'] and fingerprint(result.json['evidence']) == seal


def test_missing_run(client):
    response = client.post('/api/runs/nope/issue')
    assert (response.status_code,response.json['error']) == (404,'RUN_MISSING')


def test_input_to_evidence(client):
    path = run_path(client)
    client.post(path+'/issue')
    packet = client.get(path+'/export').json['evidence']
    assert packet['chainage']['projected_count'] == 6
    assert packet['coverage']['missing_mm'] == 200000
    assert len(packet['isolated']) == 5


def test_issue_page_selects_run(client):
    run_id = run_path(client).split('/')[-1]
    page = client.get(f'/work/issue?run={run_id}').get_data(as_text=True)
    assert f'value="{run_id}" selected' in page
