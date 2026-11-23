from collections import defaultdict

from app.config import MERGE_MM


def consolidate(projected):
    channels = defaultdict(list)
    for point in projected:
        channels[point['chain'], point['ref']].append(point)
    clusters = []
    for (chain, kind), points in sorted(channels.items()):
        for event in sorted(points, key=lambda point: (point['station_mm'], point['event_id'])):
            station = event['station_mm']
            if not clusters or (clusters[-1]['chain'], clusters[-1]['kind']) != (chain, kind) or (
                station - clusters[-1]['start_mm'] > MERGE_MM
            ):
                clusters.append({'chain': chain, 'kind': kind, 'start_mm': station, 'end_mm': station,
                                 'members': [], 'sources': [], 'observations': []})
            cluster = clusters[-1]
            cluster['end_mm'] = station
            cluster['members'].append(event['event_id'])
            cluster['sources'].append(event['line'])
            # 保留逐条复位观测，销项要按报缺位置与维修时刻切开覆盖。
            cluster['observations'].append({'station_mm': station, 'event_id': event['event_id'],
                                            'line': event['line'], 'run': event['run'],
                                            'at': event['at']})
    return {'observations': len(projected), 'clusters_count': len(clusters), 'clusters': clusters,
            'merged': len(projected) - len(clusters)}
