def union(parts):
    """合并半开区间；空区间与零长区间不占长度，相接即并（[a,b)+[b,c)=[a,c)）。"""
    ordered = sorted((lo, hi) for lo, hi in parts if hi > lo)
    merged = []
    for lo, hi in ordered:
        if merged and lo <= merged[-1][1]:
            if hi > merged[-1][1]:
                merged[-1][1] = hi
        else:
            merged.append([lo, hi])
    return merged


def intersect(left, right):
    """两个已合并区间列表的交集，结果同样合并、排序。"""
    i = j = 0
    overlap = []
    while i < len(left) and j < len(right):
        lo = max(left[i][0], right[j][0])
        hi = min(left[i][1], right[j][1])
        if hi > lo:
            overlap.append((lo, hi))
        if left[i][1] < right[j][1]:
            i += 1
        else:
            j += 1
    return union(overlap)


def subtract(left, right):
    """从已合并区间 left 中挖去 right，返回半开差集。"""
    remains = []
    for lo, hi in left:
        cursor = lo
        for cut in right:
            if cut[1] <= cursor:
                continue
            if cut[0] >= hi:
                break
            if cut[0] > cursor:
                remains.append([cursor, cut[0]])
            cursor = max(cursor, cut[1])
        if cursor < hi:
            remains.append([cursor, hi])
    return union(remains)


def measure(parts):
    return sum(hi - lo for lo, hi in parts)
