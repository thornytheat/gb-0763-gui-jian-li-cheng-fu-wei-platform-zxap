# 深度登记 轨检里程复位台

中型项目。巡检员跨断链复算里程，核对计划覆盖并签发证据。

## 功能模块

| 模块 | 使用者动作 | 入口 | 核心文件 | 测试 |
|---|---|---|---|---|
| M1 轨检报文采信 | 查分段与隔离 | `GET/POST /api/capture` | `app/capture/scan.py` `app/capture/resolve.py` | `tests/test_capture.py` |
| M2 基点匹配 | 查等级和冲突点 | `GET/POST /api/anchors` | `app/anchors/match.py` | `tests/test_anchors.py` |
| M3 区间坐标复位 | 按链复核标称坐标 | `GET/POST /api/chainage` | `app/chainage/interpolate.py` `app/chainage/segments.py` | `tests/test_chainage.py` |
| M4 缺陷投影合并 | 查同链缺陷群 | `GET/POST /api/defects` | `app/defects/cluster.py` | `tests/test_defects.py` |
| M5 轨段覆盖对账 | 定位覆盖缺口和重叠 | `GET/POST /api/coverage` | `app/coverage/balance.py` `app/coverage/intervals.py` | `tests/test_coverage.py` |
| M6 批次留档复跑 | 运行并找回原始快照 | `POST /api/runs` `GET /api/runs/{id}/adjudications` | `app/archive/save.py` `app/archive/storage.py` | `tests/test_archive.py` |
| M6a 维修项销项 | 交班前销到已验的一截 | `GET/POST /api/repairs` | `app/repairs/closeout.py` | `tests/test_closeout.py` |
| M7 巡检证据签发 | 签发并验证证据件 | `POST /api/runs/{id}/issue` | `app/seals/issue.py` `app/seals/packet.py` | `tests/test_seals.py` |

## 陷阱登记

| TRAP | 现象 | 朴素实现会怎样 | 本项目处理 | 处理位置 | 测试 |
|---|---|---|---|---|---|
| TRAP-02 | 脏样例带 BOM | 首列错误 | 去 BOM | `app/capture/dialect.py` | `tests/test_capture.py::test_bom` |
| TRAP-04 | 分段表头 | 被算作报文 | 单独计分段 | `app/capture/scan.py` | `tests/test_capture.py::test_sections` |
| TRAP-05 | 行尾余列 | 错列通过 | 原行隔离 | `app/capture/scan.py` | `tests/test_capture.py::test_width` |
| TRAP-07 | 短横哨兵 | 误当 0 | 标明缺字段 | `app/capture/event.py` | `tests/test_capture.py::test_sentinel` |
| TRAP-11 | 两时区表示同一事件 | 重复计数 | 归到 UTC 后去重 | `app/capture/event.py` | `tests/test_capture.py::test_offset_collapses_repeat` |
| TRAP-13 | 倒序报文 | 丢失合法事件 | 迟到窗口并标秒数 | `app/capture/resolve.py` | `tests/test_capture.py::test_late_window` |
| TRAP-14 | 同编号异值 | 后写覆盖 | 同组隔离 | `app/capture/resolve.py` | `tests/test_capture.py::test_conflict_keeps_both_sources` |
| TRAP-19 | 同基点多等级 | 文件顺序决定结果 | 高等级优先，同等级冲突留缺 | `app/anchors/match.py` | `tests/test_anchors.py::test_best_grade_is_order_independent` |
| TRAP-23 | 正好落在断链处 | 重复投影或误落 | 时间和测距均左闭右开 | `app/chainage/interpolate.py` | `tests/test_chainage.py::test_cut_belongs_to_next_span` |
| TRAP-33 | 复巡只走过维修项的一截 | 整项一起销漏验，等全段走完又耽误交班 | 按维修后覆盖与归并报缺共同裁定，销到段内第一处报缺 | `app/repairs/closeout.py` | `tests/test_closeout.py::test_partial_repair_closes_verified_stretch` |
| TRAP-34 | 用维修前覆盖销项 | 旧巡检冒充修复后复核 | 只认维修完成时刻之后的复位区段 | `app/repairs/closeout.py` | `tests/test_closeout.py::test_pre_repair_coverage_cannot_close` |
| TRAP-35 | 迟到记录在已销位置重新报缺 | 该段已被销项却漏修 | 缺陷群随重算纳入该观测，从已销里扣回、恢复待修 | `app/repairs/closeout.py` | `tests/test_closeout.py::test_late_recheck_restores_closed_stretch` |
| TRAP-36 | 同批重跑重复销项 | 裁定翻倍 | 归档键含维修项，重跑命中运行键取回原裁定 | `app/archive/save.py` | `tests/test_closeout.py::test_rerun_same_batch_does_not_double_close` |

夜巡样例计划 600000 mm，已映射 400000 mm，掉线缺证 200000 mm。重复巡检 100000 mm 单列。档案事务不会发布半份快照。维修项销项只认维修后覆盖与归并后的报缺，复巡报缺处恢复待修；累计可销与待修之和等于维修项总长。
