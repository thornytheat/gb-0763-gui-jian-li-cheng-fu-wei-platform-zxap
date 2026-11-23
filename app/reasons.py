REASONS = {
    'WIDTH': '报文列数不一致', 'EMPTY_ROW': '空白报文', 'MISSING': '字段为空或为哨兵',
    'FORMAT': '时间、测距或类别无效', 'ID_CONFLICT': '事件编号对应多份互斥报文',
    'LATE_LIMIT': '迟到超出接纳窗口', 'UNKNOWN_MARK': '测绘基点未登记',
    'LOW_GRADE': '同基点已有更高采信级别', 'ANCHOR_TIE': '同等级基点发生冲突',
    'ANCHOR_REPEAT': '同位置同时间的基点重复', 'BREAK': '两个基点之间跨断链',
    'SIGNAL_GAP': '两端校准时间间隔超限', 'ODO_REVERSAL': '测距计倒走',
    'NO_BRACKET': '缺少完整校准区间', 'OUTSIDE_ODO': '测距不在校准范围',
    'NO_COVERAGE': '计划轨段缺少有效双基点区间',
    'NOT_COVERED': '复巡未覆盖到该段，仍待修',
    'PRE_REPAIR_ONLY': '仅有维修前覆盖，不能销项',
    'DEFECT_REPORTED': '复巡仍在报缺，恢复待修',
    'NO_SAMPLE': '样例不存在', 'BAD_CSV': '报文文件无法解码或解析',
    'EMPTY_FILE': '文件没有内容', 'BLANK_FILE': '文件只有空白行', 'HEADER_ONLY': '文件只有表头',
    'BAD_HEADER': '报文字段与登记不一致', 'BAD_BODY': '提交参数无效', 'BAD_REPAIR': '维修项记录无效',
    'RUN_MISSING': '归档批次不存在', 'NOT_ISSUED': '批次尚未签发',
}


def evidence(code, *events):
    return {'reason': code, 'label': REASONS[code], 'sources': [item['line'] for item in events]}
