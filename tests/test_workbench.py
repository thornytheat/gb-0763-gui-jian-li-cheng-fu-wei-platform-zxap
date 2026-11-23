def test_evidence_screens(client):
    for path, marker in [('/', '掉线缺口'),('/work/chainage','双基点复位'),('/work/anchors','基点取舍'),
                         ('/work/capture','隔离报文'),('/work/defects','归并检点'),
                         ('/work/repairs','维修项销项'),('/work/runs','归档报文')]:
        assert marker in client.get(path).get_data(as_text=True)
