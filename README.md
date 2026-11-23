# 轨检里程复位台

轨道巡检员用它把列车测距回填到各链的标称里程。覆盖长度按计划轨段取并集，掉线窗口、倒走报文和断链两侧可分开复核。

使用 `docker compose up --build`，打开 `http://localhost:18462/`。本机可安装 `requirements.txt` 后运行 `flask --app app.main:create_app run --port 18462`，执行 `pytest -q` 验证。归档数据保存在 `TRACK_DB` 指向的 SQLite 文件内，修改路径可使用一个空档案库。

从首页的夜巡原始报文开始，依次查看报文采信、基点匹配、坐标复位、缺陷归并和覆盖对账。选择标定对照报文可以复核完整覆盖。进入批次页归档，重复提交相同输入可取回同一批次，再从签发页下载证据单。前五项 API 支持 GET 读取样例，也支持 POST 提交 `{"csv":"…"}` 自有报文。

[字段和边界](docs/DATA-DICTIONARY.md) · [模块与回归登记](docs/DEPTH.md)
