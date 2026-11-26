# 潮间带跑道志愿巡查时间窗

潮渡海堤跑团的带队值班席。按日历确认的潮窗排班，在指定检查点登记到场，遇临时道路封闭则等负责人解除。

## 现场工作与联系人

模拟客户为潮渡海堤跑团。日历潮窗、路线约束、相位相似时段、志愿者领班；跨午夜窗口统一归一，封闭路段禁止签到。

- 路线档案 `trail_routes`，字段为 `name`（堤线名称）、`checkpoint`（扫码检查点）、`max_leads`（每潮窗带队名额）、`active`（开放排班）。模型约束位于 `backend/domain/trail_routes_model.py`，规则位于 `trail_routes_service.py`。
- 潮窗日历 `patrol_windows`，字段为 `route`（路线）、`opens`（签到起点 UTC+8）、`closes`（签到截止 UTC+8）、`opening_minute`（日内相位分钟）、`minutes`（窗口时长）、`phase`（日历相位）、`tag`（来源凭证）。模型约束位于 `backend/domain/patrol_windows_model.py`，规则位于 `patrol_windows_service.py`。
- 路线限制 `trail_notices`，字段为 `route`（路线）、`begins`（封闭开始 UTC+8）、`until`（封闭结束 UTC+8）、`reason`（封闭缘由）、`status`（限制状态）。模型约束位于 `backend/domain/trail_notices_model.py`，规则位于 `trail_notices_service.py`。
- 带队与签到 `lead_shifts`，字段为 `window`（关联潮窗）、`lead`（带队员）、`contact`（队内联络号）、`on_site`（到场时间 UTC+8）、`checkpoint`（签到检查点）、`state`（交接状态）。模型约束位于 `backend/domain/lead_shifts_model.py`，规则位于 `lead_shifts_service.py`。

团队为模拟的8 人联络组，负责跑团沿堤路段的志愿巡查。

领队在潮历、路段群消息和扫码签到表之间切换。午夜前后时段容易错配，临时封路容易漏看，同潮窗的带队名额容易重复占用。

潮历和路段通告进值守桌，志愿者交回带检查点与时刻的签到单给跑团协调员。

### 一天的业务操作

1. 18:00 秦理登记东岸潮尺环线 TR-A 的入口 GATE-EAST。
2. 18:30 温河从演练日历抄录 2090-12-14 23:58 至 12-15 00:36 的潮窗。
3. 18:40 使用潮相位圆周坐标查找到 W-NOV-30 作为领班交接参考。窗口起点分别是 23:58 和 00:02，只跨午夜相差 4 分钟。
4. 19:00 为 WINDOW-QA 登记唯一领班 SHIFT-QA。
5. 21:00 秦理录入 00:05–00:20 护栏换岗封闭。
6. 00:11 温河在 GATE-EAST 签到被暂时拦截，领班名额继续保留。
7. 00:11 秦理确认护栏已撤，解除通知。温河重新签到，负责人随后签回。

## 启动

```sh
cp .env.example .env
docker compose up -d --build --wait
docker compose exec -T backend python -m scripts.seed_demo
```

打开 `http://127.0.0.1:18305`。FastAPI OpenAPI 在 `http://127.0.0.1:19305/docs`。
Compose 运行 Nginx、Python FastAPI、独立 Redis 消费进程、SQL 数据库和 Redis，SQL 与 Redis 使用命名卷。
本机开发时，在 Python 3.11 环境安装 `backend/requirements.txt` 后从 backend 目录运行 `uvicorn core.app:app`。须提供 `DATABASE_URL`、`REDIS_URL`、`JWT_SECRET`，`SEED_DEMO` 控制演示初始化。

| 演示账号 | 权限 |
|---|---|
| operator@demo.test | 提交领域记录和计算请求 |
| reviewer@demo.test | 提交记录并执行有业务约束的复核操作 |
| viewer@demo.test | 浏览业务台账 |

三个本地演示账号均使用 `DemoC0de!2026`。角色在 `backend/core/roles.py` 和 `frontend/src/store.js` 中声明。计算状态在 worker、queueing、API 和同一前端 store 中使用。

## 页面与接口

| 业务任务 | FastAPI 路由 | 页面 |
|---|---|---|
| 路线档案 | `/trail_routes` /trail_routes/register-route，/trail_routes/pause-route | `frontend/src/pages/trail_routes.js` |
| 潮窗日历 | `/patrol_windows` /patrol_windows/register-window，/patrol_windows/compare-phase | `frontend/src/pages/patrol_windows.js` |
| 路线限制 | `/trail_notices` /trail_notices/post-closure，/trail_notices/lift-closure | `frontend/src/pages/trail_notices.js` |
| 带队与签到 | `/lead_shifts` /lead_shifts/assign-lead，/lead_shifts/check-in，/lead_shifts/hand-back | `frontend/src/pages/lead_shifts.js` |

SQL 实体与约束在 `backend/domain` 下维护。前端使用原生 ES modules。核心算子为 周期正余弦距离。圆周距离为将开始分钟映射到单位圆后的欧氏弦长，再加绝对窗口时长差/180。仅比较同线路、同相位、已发生在目标潮窗之前的日历样本。

日期和点位为虚拟演练数据。UTC+8 日历用于跨午夜排班和历史相似性，不读取实测潮高，也不作可通行性判断。签到允许录入演练时钟以重放流程。

[MIT](LICENSE)
