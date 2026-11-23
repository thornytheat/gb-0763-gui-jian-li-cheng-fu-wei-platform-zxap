from app.capture.scan import scan
from app.capture.dialect import FIELDS


def test_multiline_record_preserves_next_line():
    source = ('\ufeff' + ','.join(FIELDS) + '\r\n'
              'a,R,defect,2026-01-01T00:00:00Z,0,"裂\r\n纹",1\r\n'
              'b,R,defect,2026-01-01T00:00:01Z,1,擦伤,2\r\n')
    output = scan(source.encode())
    assert [(e['line'], e['ref']) for e in output['events']] == [(2,'裂\r\n纹'), (4,'擦伤')]


def test_gb18030_with_reordered_fields():
    source = 'ref,event_id,odo_mm,run,at,kind,grade\n裂纹,001,5,R,2026-01-01T00:00:00-01:00,defect,2\n'
    row = scan(source.encode('gb18030'))['events'][0]
    assert (row['event_id'], row['ref'], row['at']) == ('001','裂纹','2026-01-01T01:00:00+00:00')
