# Changelog

All notable changes to the `jiuzhang` SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
with the joint-debug period rules defined in [VERSIONING.md](doc/overview/VERSIONING.md).

## [Unreleased]

### Added

- 新增 `README_EN.md`，提供完整的英文版 SDK 使用手册，并在中英文 README 最上方加入了语言切换链接。
- 新增 `jiuzhang.cloud` 平台型 HTTP 主线：
  - `CloudClient` 支持复杂度估计、任务提交、结果查询和一站式 `run_experiment()`。
  - `HttpTransport` 基于 `httpx` 封装 GET / POST JSON、token header 注入和 HTTP 错误映射。
  - 新增 `demo_cloud.py`，用于联调 Go Mock 天衍平台。
  - 新增 cloud 单元测试，覆盖路径调用、token header 和错误映射。

### Changed

- 隐蔽外部修改服务地址的入口：彻底移除了 `CloudClient` 构造函数中的 `base_url` 参数，同时移除对 `JIUZHANG_BASE_URL` 环境变量的解析，默认统一在代码内硬编码为本地 mock 地址 `"http://127.0.0.1:18081"`。
- 将当前开发主线整理为平台型 HTTP SDK：保留 `jiuzhang.cloud`、`TokenManager`、统一异常与工具模块，移除早期真机直连 TCP 协议线（`hardware` / `sampling` / `protocol` / `transport` / `testkit`）及其测试和旧 demo。
- 移除了 Git 提交校验限制：修改 `code/.pre-commit-config.yaml` 移除了 Git 提交信息格式（Conventional Commit）限制与大文件提交体积（512KB）拦截限制。
- `TokenManager` 的占位 token 规则由 `JZ-` 前缀 + 32 位小写十六进制字符承担，等待后续云平台正式认证规则确定后再集中调整。
- `AGENTS.md` 作为唯一协作说明权威文件，`CLAUDE.md` 改为指向 `AGENTS.md`，避免重复维护。

- **PR-7.1**: 全面对齐 14 个 payload dataclass 与 `doc/应用层消息语义需求草案-v1.0.md`
  §5.x 通用信封定义。SDK 公开 API 与协议 payload 采用**两层独立命名**：
  - SDK Python API 保留业界惯例（`modes` / `squeeze_param` / `shots`）。
  - 协议 payload 字段名严格遵循设计文档原文 —— 驼峰（`sessionId` /
    `heartbeatSec` / `isLast` / `durationMs` / `targetMachineId` 等）、
    学术记号（`Mt` / `r`）、与 `maxMt` / `maxR` / `maxShots`。
  - 每个 payload 显式实现 `to_dict()` / `from_dict()`，负责 Python 蛇形
    属性与 JSON 文档原文之间的双向映射；`asdict_payload()` 改为优先
    委托 `payload.to_dict()`。
  - 新增子结构：`GbsParams` / `ChunkingPolicy` / `SamplingSummary`
    （对应文档 §5.5.1 / §5.5.2 / §5.5.4 的嵌套字段）。
  - 新增 payload：`ConfigureAckPayload`（空 dataclass，文档未规定字段，
    预留扩展点）、`SamplingAckPayload`（`accepted: bool`）。
- **PR-7.1**: 逐 payload 修正：
  - `HelloPayload`：`token_id` / `sdk_version` / `client_info` →
    `token` / `target_machine_id` / `capabilities`（移除 `sdk_version`，
    新增 `targetMachineId`）。
  - `HelloAckPayload`：`session_id` / `server_info` →
    `accepted` / `session_id` / `heartbeat_sec` / `limits`（补 `accepted` /
    `heartbeatSec`，移除 `server_info`）。
  - `Limits`：`max_modes` / `max_squeeze_param` / `max_shots` + min_* →
    `max_shots` / `max_mt` / `max_r`（移除文档未规定的 min_* 字段；
    `max_mt` / `max_r` 对应 GBS 论文记法）。
  - `ConfigureGbsPayload`：扁平 → 嵌套 `{"gbs": GbsParams}`。
  - `ReadyPayload`：`accepted` / `config_id` → `ready: bool`。
  - `StartSamplingPayload`：`config_id` 移除；新增 `chunking: ChunkingPolicy`。
  - `SampleChunkPayload`：`chunk_index` / `shots_in_chunk` / `samples` →
    `format` / `encoding` / `index` / `is_last` / `shots` / `data`。
  - `SamplingDonePayload`：`total_shots` / `total_chunks` →
    `ok` / `summary: SamplingSummary`。
  - `ByePayload`：默认值 `"client_disconnect"` → `"NORMAL"`（对齐文档枚举）。
  - `ByeAckPayload`：补 `closed: bool` 字段。
- **PR-7.1**: 同步更新 `testkit/simulator_server.py` 的 `DEFAULT_LIMITS`
  以使用新的字段命名。
- **PR-7.1**: `tests/unit/test_messages.py` 全部用例重写：
  - 47 条新增用例覆盖每个 payload 的 `to_dict` / `from_dict` / round-trip
  - 显式断言驼峰 JSON 字段名（如 `sessionId` 而非 `session_id`）
  - 嵌套 dataclass 完整往返（Limits / GbsParams / ChunkingPolicy /
    SamplingSummary）
  - Envelope ↔ payload 协同往返用例

### Added

- **PR-8**: `ProtocolSession` 协议会话与状态机完整实现：
  - 7 个状态（CLOSED / HANDSHAKING / READY / CONFIGURING / SAMPLING /
    CLOSING / FAILED）+ 显式迁移表 `_TRANSITIONS`，非法迁移立即抛
    `InternalError`。
  - 公开方法：`hello(token, target_machine_id)`、`configure_gbs(mt, r)`、
    `start_sampling(shots)`、`bye()`。各方法内部走"状态转移 → 编码 Envelope
    → Correlator 配对 → 解析响应"流程。
  - 后台接收线程 `_receiver_loop`：从 Transport 持续读帧、解码 Envelope、
    按 `requestId` 分发给 Correlator；SAMPLE_CHUNK 缓冲到
    `_collected_chunks`；无 requestId 的服务端推送（如未匹配的 ERROR）
    交由特殊处理路径。
  - 心跳自动管理：握手成功后启动 HeartbeatThread（间隔来自
    `HELLO_ACK.heartbeatSec`），bye / FAILED 时停止。
  - ERROR → SDK 异常映射：`_raise_from_error` 依据 `errors.ERROR_CODE_TO_EXCEPTION`
    从 ErrorPayload 还原对应异常类型。
- **PR-8**: `tests/unit/test_session.py` — 10 条集成测试：
  - 自带 `_MockServer` 最小 TCP 协议 server，按规范自动回复
    HELLO_ACK / READY / SAMPLE_CHUNK × N + SAMPLING_DONE / BYE_ACK /
    HEARTBEAT_ACK
  - 状态机：初始 / configure-before-hello / bye-before-hello 非法迁移
  - 握手：成功 / 服务端 ERROR → TokenInvalidError / 超时
  - 配置：成功并维持 READY
  - 采样：多块 SAMPLE_CHUNK 聚合 + SAMPLING_DONE 收尾
  - 断连：bye → BYE_ACK → CLOSED
  - 端到端：完整 hello → configure → sample → bye 生命周期

### Coverage

- 测试总数：162 → **233**（+ 71：PR-7.1 + 47，PR-8 + 10，PR-9 + 14）
- 覆盖率：93% → **86%**（新增大量实现代码，部分路径需端到端 server 才能覆盖）
- `protocol/messages.py`：100%
- `protocol/session.py`：0% → 82%
- `auth/token_manager.py`：0% → 100%
- `sampling/gbs_sampler.py`：部分覆盖（类型校验路径已覆盖）

### Added (PR-9)

- **PR-9**: Domain 三核心类业务方法体完整实装：
  - `TokenManager.validate_token()`：`JZ-` + 32 位 hex 正则校验；
    通过返回 `make_result(data={tokenId, format})`；失败抛
    `TokenInvalidError`。新增 `masked_token` 脱敏属性。
  - `PhotonicMachine.connect()`：创建 TcpTransport → `session.hello()` →
    缓存 session；失败时 `transport.close()` 保证不泄漏。
  - `PhotonicMachine.disconnect()`：READY 时发 BYE；非 READY（如 FAILED）
    时显式停 receiver / heartbeat；finally 中 close transport。
  - `PhotonicMachine.__enter__/__exit__`：支持 `with machine:` 语法。
  - `GaussianBosonSampler.init_status()`：类型校验（bool 不被视为 int）+
    范围校验（modes vs max_mt，squeeze_param vs max_r）。
  - `GaussianBosonSampler.run(shots)`：类型 + 范围校验 → `configure_gbs` →
    `start_sampling` → 校验 `ok=False` → 校验 shape → `numpy.ndarray`。
- **PR-9**: `tests/unit/test_domain.py` — 14 条用例覆盖：
  - TokenManager：合法 / 非法前缀 / 过短 / 大写 / 非 hex / 空串 / 脱敏格式
  - GaussianBosonSampler：bool modes / bool shots / str squeeze_param 类型拒绝
  - PhotonicMachine：disconnect-before-connect / is_connected / _get_session

### Fixed (PR-9 Review)

- **Review-1**: `connect()` 握手失败时 `transport.close()` 保证释放。
- **Review-2**: `connect()` 防护改为检查 `_session` / `_transport` 非空
  （覆盖 FAILED 残留场景），而非仅检查 `is_connected`。
- **Review-3**: `run()` 校验 `SAMPLING_DONE(ok=False)` + shape 不匹配。
- **Review-4**: `_validate_type()` 拒绝 bool 穿透 int。
- **Review-5**: `disconnect()` 在 FAILED 状态下显式停 receiver / heartbeat。
- **Review-6**: `run()` 在 `configure_gbs` 前也校验 modes / squeeze_param
  （不依赖调用方先调 `init_status()`）。

### Release

- **chore(release)**: bump 版本号到 `0.1.0a9`。

## [0.1.0-alpha.7] - 2026-05-14

骨架阶段中后期累计 release：PR-2 ~ PR-7 业务实现就位。L1 Domain 异常体系
与返回结构 / 日志、L2 Protocol 信封编解码 / 14 种消息 / Correlator /
HeartbeatThread、L3 Transport 阻塞 TCP 传输全部完成；L1 Domain 三核心
类（TokenManager / PhotonicMachine / GaussianBosonSampler）的方法签名
+ 参数缓存已就位，业务方法体（端到端握手、采样调度）留给 PR-8 / PR-9。

### Added

- **PR-2**: `JiuzhangError.__init__` 与 `to_result()` 完整实现。所有 8 个具体
  异常子类（`TokenInvalidError` / `TokenExpiredError` / `PermissionDeniedError`
  / `InvalidParameterError` / `MachineOfflineError` / `MachineBusyError` /
  `TimeoutError` / `InternalError`）的 `default_code` 与
  `errors.ERROR_CODE_TO_EXCEPTION` 映射闭环。
- **PR-2**: 异常类单元测试套件 `tests/unit/test_exceptions.py`，新增 29 条
  用例覆盖字段缺省、显式注入、`details` 浅拷贝隔离、`to_result` 统一结构、
  子类 `default_code` 自洽、错误码↔异常映射闭环等场景。
- **PR-3**: `result.make_result()` 完整实现 — 统一返回结构工厂函数，
  `code` 缺省为 `"OK"`，`timestamp` 缺省为当前毫秒时间戳，`data` 浅拷贝
  隔离（调用方后续修改原 dict 不影响返回结果）。
- **PR-3**: `logging_utils.get_logger()` 完整实现 — `jiuzhang.*` 命名空间下
  的 logger 工厂；根 logger 自动挂载 `NullHandler`（幂等），允许调用方
  通过标准 `logging` 配置接管；自动归一化 ``"jiuzhang.foo"`` 形式的入参，
  避免双重前缀。
- **PR-3**: `tests/unit/test_result.py` + `tests/unit/test_logging_utils.py`，
  新增 19 条用例覆盖命名空间归一、`NullHandler` 幂等挂载、传播链遍历等。
- **PR-4**: `Envelope.to_dict / to_json / from_dict / from_json` 完整实现：
  - JSON 编码使用 `ensure_ascii=False` 保留中文，`separators=(",", ":")` 紧凑输出。
  - `from_dict` 严格校验：拒绝非 dict 输入、缺失 `type`、未知 `MessageType`、
    `payload` 非 dict、`timestamp` 非 int（含拒绝 `bool` 边界）。
  - 校验失败统一抛 `InvalidParameterError`，与 SDK 异常体系对齐。
  - `payload` 字段在 to/from 双向均做浅拷贝隔离。
- **PR-4**: `messages.asdict_payload(payload)` 工具函数 — 基于
  `dataclasses.asdict` 递归展开为 JSON-friendly dict，支持嵌套（如
  `HelloAckPayload` 中的 `Limits`）。
- **PR-4**: `tests/unit/test_envelope.py` + `tests/unit/test_messages.py`，
  新增 41 条用例覆盖 12 种 `MessageType` 枚举往返、Envelope JSON 编解码、
  to/from 字段校验、字节串/字符串两种 from_json 输入、嵌套 Limits 往返、
  与 12 种 payload dataclass 的协同序列化。

### Changed

- **PR-4.1**: 修复 `Envelope` 与 `doc/应用层消息语义需求草案-v1.0.md` §6.1
  通用信封定义的偏差：
  - **补齐缺失字段**：新增 `v`（协议版本，默认 `"1"`）、`job_id`（平台任务 ID，
    序列化为 `jobId`）、`meta`（可选扩展字段 dict，常见键含 `traceId` /
    `client`）。
  - **线上字段命名改为驼峰**：`to_dict` / `from_dict` 改用 `requestId` /
    `sessionId` / `jobId` 与文档原文对齐；Python 端属性保持 PEP 8 蛇形命名
    （`request_id` / `session_id` / `job_id`）。
  - **`trace_id` 重构为便利属性**：从顶级 dataclass 字段下沉到
    `meta["traceId"]`，通过 `@property` 暴露。
  - **新增校验**：`meta` 非 dict、`v` 非字符串均触发 `InvalidParameterError`。
  - **`PROTOCOL_VERSION` 常量**：模块级公开常量，固定为 `"1"`。
- **PR-4.1**: 补齐 `MessageType` 缺失的两种类型 `CONFIGURE_ACK` /
  `SAMPLING_ACK`（与设计文档 §6.2 一致，共 14 种）。
- **PR-4.1**: 同步更新 `test_envelope.py`（新增 `v` / `jobId` / `meta` /
  驼峰命名 / `trace_id` 属性的用例）与 `test_smoke.py`
  的 `MessageType` 完整集合断言。

### Added (续)

- **PR-5**: `TcpTransport` 完整实现 — 基于阻塞 `socket` 的 TCP 传输：
  - `connect(host, port, timeout)`：通过 `socket.create_connection` 建连，
    `ConnectionRefusedError` / `socket.gaierror` 映射为 `MachineOfflineError`，
    超时映射为 SDK 的 `TimeoutError`。
  - `close()`：幂等，连续调用、未连接调用均不抛错；先 `shutdown(SHUT_RDWR)`
    再 `close`，OSError 一律忽略。
  - `send_frame(payload)`：写入 `<4 字节大端 length> + payload`，
    payload 超过 `MAX_FRAME_SIZE`（16 MiB）抛 `InternalError`；
    未连接发送抛 `InternalError`。
  - `recv_frame(timeout)`：精确读 4 字节 length 前缀 + length 字节 body；
    支持整次调用的总超时（基于 `time.monotonic` 单调时钟的 deadline）；
    长度前缀越界、对端关闭、socket OSError 一律抛 `InternalError`，
    超时抛 SDK `TimeoutError`。
  - `is_connected()`：返回 `sock is not None`；不主动探测对端状态。
  - 私有辅助 `_recv_exact(n, deadline)`：循环 `recv` 到精确字节数，
    每次按 deadline 计算剩余超时；处理短读、对端 EOF。
  - 引入模块级常量 `MAX_FRAME_SIZE = 16 MiB`、`LENGTH_PREFIX_BYTES = 4`。
  - 线程安全：`_send_lock` 与 `_recv_lock` 分离，允许"一个线程 send /
    另一个线程 recv"的并行使用模式。
- **PR-5**: `tests/unit/test_tcp_transport.py` — 21 条用例覆盖：
  - 连接成功 / 端口不可达（兼容 Linux 拒绝与 Windows SYN 超时）/
    DNS 失败 / 重复 connect
  - 关闭幂等性（未连接 / 已连接 / 重复关闭）
  - 发送：空 payload / 超长拒绝 / 未连接拒绝
  - 接收：未连接拒绝 / 超时 / 对端关闭 / 长度越界
  - 往返：ASCII / 中文 UTF-8 / 二进制 / 多帧串行 / 64 KiB 大帧
  - 多线程：主线程 send / 子线程 recv 并行
  - 测试自带 `_EchoServer` 最小 loopback echo TCP server，
    不依赖更高层的 `SimulatorServer`。
- **PR-6**: `Correlator` 请求/响应配对器完整实现：
  - `register()`：分配 UUID4 `request_id`，创建 `threading.Event` 等待槽。
  - `fulfill(request_id, response)`：按 ID 匹配并唤醒等待方；未找到返回
    `False`（可能已超时被回收）。
  - `wait(request_id, timeout)`：阻塞等待响应；超时抛 SDK `TimeoutError`，
    未登记抛 `InternalError`；无论成功/超时均清理 slot（避免内存泄漏）。
  - `cancel(request_id)`：取消等待并释放 slot，唤醒正在 wait 的线程；
    不存在的 ID 静默忽略。
  - `pending_count` 属性：跟踪当前等待中的请求数。
  - 线程安全：内部 `threading.Lock` 保护 slot 字典。
- **PR-6**: `tests/unit/test_correlator.py` — 16 条用例覆盖：
  - register 唯一性 / pending_count 递增
  - fulfill 成功匹配 / 不存在返回 False / 已消费返回 False
  - wait 正常唤醒 / 超时 / 未登记 / slot 清理
  - cancel 移除 slot / 不存在静默 / 唤醒阻塞中的 waiter
  - 多线程：单 waiter fulfill / 10 并发 waiter 乱序 fulfill
- **PR-7**: `HeartbeatThread` 心跳后台线程完整实现：
  - 基于 daemon 线程 + `threading.Event` 的极简并发模型，不引入 asyncio。
  - 通过注入 `send_fn` / `recv_fn` 回调与传输层交互，不直接持有
    Transport 或 ProtocolSession 引用——降低耦合，便于测试。
  - `start()`：启动后台线程；重复调用抛 `InternalError`。
  - `stop(timeout)`：通过 Event 通知线程退出，线程在 `event.wait(interval)`
    处立即响应停止信号，不需要等完整个间隔。
  - `is_alive()`：查询线程是否仍在运行。
  - `sequence` 属性：已发送的心跳序号（从 0 起递增）。
  - `consecutive_failures` 属性：当前连续失败次数。
  - 失败处理：send_fn / recv_fn 抛异常时 `consecutive_failures` 递增；
    成功一次归零；达到 `max_failures` 时触发 `on_failure` 回调并自行退出。
- **PR-7**: `tests/unit/test_heartbeat.py` — 13 条用例覆盖：
  - 生命周期：start/stop / 重复 start / stop 前 start / stop 打断长间隔
  - 发送：sequence 递增 / recv_fn 在 send_fn 后调用 / None fn 不报错
  - 失败：连续失败递增 / on_failure 触发 / 成功重置计数 / recv_fn 失败也计入
  - 线程属性：daemon / 线程名

### Fixed

- **PR-7-fix**: `HeartbeatThread.stop()` 在 `join(timeout)` 超时后保留
  `_thread` 引用 —— 之前无条件清空可能掩盖"心跳线程未真正退出"的隐患，
  让后续 `start()` 误以为可以重新启动；改为仅当 `thread.is_alive()` 返回
  `False` 时才清空，否则保留让重启检查能立即抛错。

### Release

- **chore(release)**: bump 版本号到 `0.1.0a7`（`version.py` /
  `pyproject.toml` / `uv.lock` / `test_smoke.py` 同步落地），打 git tag
  `v0.1.0-alpha.7`。

### Coverage

- 测试总数：13 → 162（+ 149）
- 覆盖率：65% → 93%
- `transport/tcp.py`：0% → 91%
- `protocol/correlator.py`：0% → 100%
- `protocol/heartbeat.py`：0% → 100%
- `exceptions.py`：81% → 100%
- `result.py` / `logging_utils.py`：0% → 100%
- `protocol/envelope.py` / `protocol/messages.py`：0% → 100%

## [0.1.0-alpha.0] - 2026-05-12

### Added

- Project scaffolding: src-layout under `code/src/jiuzhang/`.
- `pyproject.toml` with the `uv` + `ruff` + `mypy` + `pytest` toolchain.
- Package skeleton aligned with the four-layer architecture
  (Domain / Protocol / Transport / Backend) defined in
  [doc/SDK 架构设计-v0.1.md](./doc/SDK%20架构设计-v0.1.md).
- Public API placeholders in `jiuzhang.__all__`: `TokenManager`,
  `PhotonicMachine`, `GaussianBosonSampler`, `JiuzhangError` and the
  exception hierarchy.
- Pre-commit hooks: `ruff format`, `ruff check`, `mypy`,
  and Conventional Commits message validation.
- Versioning policy ([VERSIONING.md](doc/overview/VERSIONING.md)) and release SOP
  ([RELEASING.md](doc/overview/RELEASING.md)).
- This `CHANGELOG.md`, following Keep a Changelog 1.1.0.

### Notes

- This is a **scaffolding-only** release. No business logic is implemented;
  all public methods raise `NotImplementedError("v0.1.0 待实现")`.
- Public API surface is **not yet frozen**; it will be frozen at `v0.1.0`.

---

<!--
Versioning Reminder (see VERSIONING.md):

  - 0.1.0-alpha.x  → scaffolding phase, API may change.
  - 0.1.0          → frozen baseline; only PATCH bumps until v0.2.0.
  - 0.2.0          → real-machine integration; breaking changes allowed
                     with at least 1-week written notice to integrators.
  - 1.0.0          → production release.

Conventional Commits map to changelog sections as follows:

  - feat:      → Added
  - fix:       → Fixed
  - refactor:  → Changed (only if it alters public behaviour)
  - perf:      → Changed
  - docs:      → (not listed unless user-facing)
  - chore:     → (not listed)
  - BREAKING CHANGE footer → Breaking section + MAJOR/0.x MINOR bump
-->
