from app.config import REVISION
from app.manifest import canonical, digest


def packet(snapshot):
    manifest, stages = snapshot['manifest'], snapshot['stages']
    return {'document': '轨检证据单', 'revision': REVISION, 'manifest': manifest,
            'source_events': stages['capture']['events'], 'isolated': stages['capture']['rejects'],
            'duplicate_events': stages['capture']['repeated'], 'anchor_review': stages['anchors'],
            'chainage': stages['chainage'], 'defects': stages['defects'], 'coverage': stages['coverage']}


def fingerprint(document):
    return digest(canonical(document))
