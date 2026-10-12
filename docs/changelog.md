---
title: 📝 更新日志
order: 45
---

# Changes

本页由 git 历史自动生成，收录自 `v3.11.3` 以来的 68 个 PR（最近更新 2026-10-12）。
完整提交历史见 [GitHub Commits](https://github.com/SanaeMio/Bangumi-syncer/commits/main)。

::: tip 关于本页
「版本亮点」由人工维护（`docs/changelog-highlights.md`），收录实测数据、设计取舍与升级注意事项；「提交明细」由 `.github/workflows/changelog.yml` 在合并进 `main` 后自动生成，**请勿手工编辑本页的提交明细部分**—— 下次生成会覆盖。
如需修正条目措辞，请修改对应的提交信息或 PR 标题。
:::

# 版本亮点

## 3.11.3 之后（未发布）

### ✨ 新功能

- 匹配裁决层（Arbiter）：`[matching]` 段新增 `arbiter_enabled` 与各来源权重，由「单阈值」改为「分数够不够 + 领先第二名多少」双阈值门控，240 条归档用例实测精确率 95.9% → 99.0%（错命中 9 → 2，覆盖率 92.5% → 85.8%）。**默认关闭**，开启后不推翻季度/媒体类型/关联条目改选；配置页「匹配裁决层」卡片可调开关、双阈值与各来源权重 [#255](https://github.com/SanaeMio/Bangumi-syncer/pull/255)
- 拒绝待确认候选时记入标题级负样本黑名单，下次自动匹配命中同一 subject 时降级为漏标（宁可漏标不能错标）；自定义映射为显式意图，不受黑名单约束 [#15](https://github.com/SanaeMio/Bangumi-syncer/issues/15) [#255](https://github.com/SanaeMio/Bangumi-syncer/pull/255)
- 封面批量解析优化：已配置 Bangumi 账号时优先从「在看」收藏列表一次性提取封面（覆盖时间线绝大多数条目），未命中的条目再逐个调用 API 兜底（不再走 Archive 短路，确保返回图片字段），结果缓存 24 小时
- 新增 ECH（加密 Client Hello）支持：`[dev]` 段新增 `ech_mode` / `ech_doh_url` / `ech_doh_use_proxy` / `ech_hosts` / `ech_ech_config` 五项配置，可加密 Bangumi 各域名的 TLS Client Hello 以应对 SNI 探测/封锁；DoH 获取失败或配置无效时自动降级为普通 TLS，不影响同步
- 日志分级：新增 `[dev] log_level` 配置（默认 `INFO`，可用 `LOG_LEVEL` 环境变量覆盖），低于阈值的日志不再写入控制台/日志文件
- 请求/批次关联：HTTP 请求经 `X-Request-ID` 生成/透传 `[req:...]` 标签，一次同步一个 `[run:...]` 标签，批量补发一轮一个 `[batch:...]` 标签，同步记录同时落库 `run_id` / `batch_id`，可串联一次完整调用链
- 新增 MCP 工具（只读 + 写配置），支持通过 Model Context Protocol 读写配置 [#257](https://github.com/SanaeMio/Bangumi-syncer/pull/257) [#258](https://github.com/SanaeMio/Bangumi-syncer/pull/258) [#259](https://github.com/SanaeMio/Bangumi-syncer/pull/259)
- 通知系统收敛为单一实现：删除旧版 Notifier 及其 mixin，事件专属字段统一收敛到 `notification_registry` 注册表 [#266](https://github.com/SanaeMio/Bangumi-syncer/pull/266)

### 🐛 Bug 修复

- 修复全角标题匹配失败：归一化入口补齐 Unicode NFKC（索引侧本就做了 NFKC，查询侧没做），240 条归档用例命中率 88.8% → 97.9% [#255](https://github.com/SanaeMio/Bangumi-syncer/pull/255)
- 修复跨季匹配选到集数更多的前作：收紧媒体类型改选触发条件，并删除「按 eps 最大择优」（`凡人修仙传` 81 集盖过 `凡人修仙传 新年番` 48 集） [#255](https://github.com/SanaeMio/Bangumi-syncer/pull/255)
- 修复 bangumi-data 命中不校验放送日期导致的错标：与请求日期相差超过 365 天时改为未命中，交由 Archive / API 继续解析（宁可漏标不能错标） [#4](https://github.com/SanaeMio/Bangumi-syncer/issues/4) [#255](https://github.com/SanaeMio/Bangumi-syncer/pull/255)
- 修复集数定位误用「衍生」关系边：`鬼灭之刃` 第 28 集曾错标到 `鬼灭广播`（广播节目，89 集），现排除该边；同时补上 `favorite` 字段的反序列化 [#255](https://github.com/SanaeMio/Bangumi-syncer/pull/255)
- 修复类型冲突时同名动画漏标：archive 精确匹配只命中真人剧时（`凡人修仙传` 动画条目均带后缀），补召回同名动画候选 [#255](https://github.com/SanaeMio/Bangumi-syncer/pull/255)
- 修复 infobox 花括号别名列表未解析：98.9% 的 `别名` 字段使用花括号 block 格式却只识别 bullet，导致别名被当作一整个脏字符串，含空格的别名永远匹配不上（需重建 FTS5 索引生效） [#16](https://github.com/SanaeMio/Bangumi-syncer/issues/16) [#255](https://github.com/SanaeMio/Bangumi-syncer/pull/255)
- 修复空白原始标题（Emby 缺 `OriginalTitle` 时传入 `" "`）顶掉正确匹配分支的问题，emby/plex 源头统一为 `None` [#255](https://github.com/SanaeMio/Bangumi-syncer/pull/255)
- 修复通知在删除规则后仍广播到所有渠道：无 `notify-rule` 时改为**停发外部渠道**（仅写站内信），渠道不再兜底按自身 `types` 订阅，规则成为发布的唯一闸门
- 修复无专属字段的类型仍把 `__type_fields__` 哨兵字面量发给接收端；自定义模板不再被静默追加字段 [#266](https://github.com/SanaeMio/Bangumi-syncer/pull/266)
- 修复邮件正文集号格式不统一：统一为 `{ep_label}`，无集数信息时省略而非输出 `S00E00` [#266](https://github.com/SanaeMio/Bangumi-syncer/pull/266)
- 修复显式映射仍被跨季改选（issue #267）；修正「自动推算」的 offset 语义 [#268](https://github.com/SanaeMio/Bangumi-syncer/pull/268)
- 修复续作被解析成上一季：季号参与 bangumi-data 匹配判决 [#269](https://github.com/SanaeMio/Bangumi-syncer/issues/269) [#270](https://github.com/SanaeMio/Bangumi-syncer/pull/270)

### ⚠️ 升级注意

- 通知渠道配置中「自定义模板文件路径」填写的是**模板名**（如 `fancy`），不是文件路径；模板一律放在 `templates/notifications/<channel>/` 下。升级后请确认路径写法 [#266](https://github.com/SanaeMio/Bangumi-syncer/pull/266)
- 若自定义了 Webhook 模板且未写 `"extra": "__type_fields__"`，追番总结等事件将**不再自动附加**其专属字段（这是有意收紧，避免向严格接收端塞入未声明的键）
- 旧版 Notifier 已删除，历史上依赖它的第三方脚本/集成需要改用事件注册表

# 提交明细

## 2026-10-12

### [refactor(notify): 通知系统收敛为单一实现，修复内容丢失与邮件注入](https://github.com/SanaeMio/Bangumi-syncer/pull/266)

- `de83d23` docs(notification): 修正追番总结示例里的 episode，并加测试防再次脱节
- `79209c3` fix(notify): 邮件正文集号统一为 {ep_label}，无值时省略
- `fcd05dd` docs(notify): 清理架构图中残留的 Notifier 引用，忽略本地 rrr/ 目录
- `fc2e42d` fix(notify): 自定义模板不再被静默追加字段，测试端点按 id 精确测试
- `d608d13` fix(notify): 恢复 per-type 标题信息，修复嵌套哨兵泄漏与 except 过宽
- `aae752d` fix(notify): 无专属字段的类型不再把 __type_fields__ 哨兵字面量发给接收端
- `6aaebf9` fix(notify): 邮件 HTML 转义防注入；纯文本正文改用专用 .txt 模板
- `ed827b9` docs(notify): 自定义模板标注为高阶操作并显著提示，重构文档结构
- `da7b7b7` docs(notify): 说明事件专属字段与标题来源，补充升级提示
- `b037900` refactor(notify): 删除旧版 Notifier 及其 mixin，收敛为单一通知实现
- `1c3d5b5` refactor(notify): 测试端点统一走 Channel.send，为移除旧 Notifier 铺路
- `66ff636` fix(notify): 类型专属字段收敛到注册表，修复通用模板丢弃追番总结正文

### [feat(mcp): 新增 MCP 工具（只读 + 写配置）并加固配置写入](https://github.com/SanaeMio/Bangumi-syncer/pull/259)

- `fe6cc27` fix(config,mcp): 关闭 ConfigParser 插值，拒绝连字符键名
- `2058839` fix(mcp): 禁止 MCP 写入 [bangumi] 段，避免被迁移为数据库账号
- `e0b3b22` fix(mcp): update_config 与 get_logs 加固，修复凭据可写与合法键误拒
- `4b9c8a3` refactor(config): set_config 收敛为纯格式校验，移除 fail-closed
- `3896dab` feat(mcp): 新增 MCP 工具（只读 + 写配置）并加固配置写入

### [feat(mapping): 集数分段映射与显式绑定不跨季改选（#267）](https://github.com/SanaeMio/Bangumi-syncer/pull/268)

- `d280e5a` fix(mapping): 修正「自动推算」的 offset 语义，只校验改动过的 subject_id
- `66df6c4` docs(mapping): 新增「一集拆多集」场景（含 episodes_of 截断的静默陷阱）
- `092c285` docs(mapping): 补齐集数分段的场景与写法（含一个静默失效的坑）
- `ff26659` refactor(mapping): 移除已无调用点的 get_segments_for
- `065aadd` fix(mapping): 修复显式映射仍被跨季改选（issue #267 未真正解决）
- `d9bdf43` docs(mapping): 拆为三页（操作 / 正则进阶 / 正则入门）并补充分段与风险提示
- `ab33d3c` test(episode-resolve): 固定 media_type 分派口径（movie vs real_action）
- `8c25679` fix(config): 移除不可能生效的裁决权重旋钮 weight_custom_mapping / weight_bangumi_data
- `af3b1a7` feat(mapping): 正则规则支持 season 限定
- `18324a1` test(multi-account): 固定多账号扇出复用同一全局剧集 ID 的不变量
- `cc00b0a` refactor(validation): subject_id 校验抽为共享实现，映射写入前也校验
- `1df972b` test(mapping): 固定 _find_multi_season_episode 的季号语义并说明其为有意设计
- `55a6fa8` refactor(blacklist): 屏蔽词豁免统一委托 mapping_service.matches_any
- `40cdb8e` feat(mapping): 映射弹窗支持场景选择式集数分段编辑
- `726c05a` fix(mapping): 修复屏蔽词豁免因 find_mapping 返回值变更而静默失效
- `e3cee26` refactor(mapping): 移除本次改动引入的未使用缓存字段
- `5449438` test(mapping): 补齐映射分段与写保护的端到端接缝测试
- `36dc5ab` feat(mapping): 显式绑定禁用跨季改选并打通集数分段执行链路
- `e571dd6` fix(mapping): 修复映射写回丢数据并支持集数分段对齐

### [fix(archive): TV 番剧自动归档改用收藏响应内嵌的 subject.eps 判定总集数](https://github.com/SanaeMio/Bangumi-syncer/pull/271)

- `b865834` fix(archive): TV 番剧自动归档改用收藏响应内嵌的 subject.eps 判定总集数

### [fix(matching): 季号参与 bangumi-data 匹配判决，修正续作被解析成上一季](https://github.com/SanaeMio/Bangumi-syncer/pull/270)

- `136f965` fix(matching): 季号参与 bangumi-data 匹配判决，修正续作被解析成上一季

## 2026-10-10

### [feat(config): 新增 [dev] mcp_base_url 配置项并修复下划线段名敏感字段判定](https://github.com/SanaeMio/Bangumi-syncer/pull/258)

- `641ac85` feat(config): 新增 [dev] mcp_base_url 配置项与敏感字段判定修复

## 2026-09-24

### [chore: 升级 FastAPI/FastMCP 依赖并同步文档格式化与开发环境清理](https://github.com/SanaeMio/Bangumi-syncer/pull/257)

- `a2d2c27` chore: 升级 FastAPI/FastMCP 依赖并同步文档格式化与开发环境清理

### [refactor: 匹配管线准确性 + 同步详情可观测性（#255 后续）](https://github.com/SanaeMio/Bangumi-syncer/pull/256)

- `d912b15` docs(testing): 补充手动触发测试的使用方法与场景
- `86dbe19` fix(blacklist): 映射优先判定带上真实 season，避免跨季绕过屏蔽词
- `4227a2a` refactor(media-type): 采信媒体源的权威类型，重写 fongmi 的文件名结构判定
- `7820ae3` refactor(blacklist): 屏蔽关键词与 title_blacklist 合并为单一 DB 关键词表
- `579e46c` refactor(matching): 执行门集中登记 + 同步详情补全改选/路径/子步骤
- `6813148` feat(matching): 季号不符时扣分，修「第二季被第三季抢走」
- `2116c48` feat(episodes): 集数一致性校验，拦脏值而不误伤跨季连续编号
- `56ec586` feat(episodes): 按官方公式解析「条目内集数」，修国漫大番漏标
- `8ff4bfb` perf(bangumi-api): 实例缓存上限 200 → 1000
- `c7fe975` fix(episodes): 修复续集链遍历的原地空转（同步线程卡死烧 CPU）

## 2026-09-21

### [refactor(matching): 匹配管线契约层 + 裁决层 + 行为基线工具](https://github.com/SanaeMio/Bangumi-syncer/pull/255)

- `2d01a5e` test(config): 强制配置项三件套，补齐实际缺口
- `beacf2b` docs(config): 重写配置说明，覆盖 config.example.ini 全部配置项
- `8c7d311` feat(config): 配置页补上「匹配裁决层」卡片
- `77bf7d6` style(matching): Ruff 格式化与未使用导入清理
- `dda68d3` docs: 记录匹配管线变更并清理失效引用
- `9c96330` test(golden): 基线检查改为手动脚本
- `3b7a1b6` fix(matching): 黑名单查询容错，避免吞掉歧义通知
- `8a5bde0` feat(matching): 拒绝待确认候选时记入标题级黑名单
- `ffc2ebb` fix(archive): 解析 infobox 中的花括号别名列表
- `335dede` feat(matching): bangumi-data 命中增加日期硬护栏
- `40e3f23` refactor(regex): 共享标题正则收敛到 app/utils/title_patterns.py
- `08959d5` refactor(constants): 去重同目的常量
- `4df5364` refactor(constants): 收藏与条目类型码全量改用常量
- `ea54811` refactor(constants): 清除残留的硬编码类型码
- `76d97be` harden(constants): 补齐具名常量并加死代码护栏
- `14da3b6` feat(archive): platform 数字编码分域解码（调用点暂未接入）
- `ff3cd09` fix(archive): 类型冲突时补召回同名动画候选（凡人修仙传漏标）
- `68f6632` fix(archive): 排除「衍生」边参与集数定位 + 反序列化 favorite
- `e1bf515` fix(matching): 入口 NFKC 补齐 + 收紧媒体类型改选触发条件
- `13b09f7` feat(matching): 落地裁决层 P3（Arbiter + 双阈值门控，默认关闭）
- `9da19e8` refactor(matching): 落地契约层 C1–C4（类型 + 三方 adapter + 候选产出）
- `b92486b` test(golden): 建立匹配管线行为基线
- `0a4e720` perf(bangumi-data): 消除重复 strptime 与未命中路径的二次全表扫描

### [feat(sync): 同步记录按 Bangumi 账号展示同步结果并逐账号通知，规范首选账号与停用控制](https://github.com/SanaeMio/Bangumi-syncer/pull/254)

- `a314803` feat(sync): 同步记录按 Bangumi 账号展示同步结果并逐账号通知，规范首选账号与停用控制

### [chore: Python 3.9 → 3.10 升级](https://github.com/SanaeMio/Bangumi-syncer/pull/251)

- `1fd8d06` ci: 移除 setup-python 的 pip 缓存配置（uv 管理依赖，缓存目录不存在导致 lint 失败）
- `b45d9ad` chore: Python 3.9 → 3.10 升级（不含 MCP 改动）
- `ffe0e93` chore: Python 3.10 环境升级（Dockerfile/CI/版本声明）

## 2026-09-20

### [feat: summary-memory-integration（总结任务接入记忆）](https://github.com/SanaeMio/Bangumi-syncer/pull/246)

- `2ce45f6` fix: 删除/改名改安全顺序（清记忆与迁移前置），运行时同步失败降级为日志
- `05f549f` fix: 增量窗口防御时钟回拨，起点晚于终点时夹紧为单日
- `b10b4fc` fix: 同一任务并发执行保护，手动/cron 冲突时跳过并提示
- `0516972` feat(ui): 触发按钮展示任务执行中跳过提示
- `fb19135` fix: 注入与统计跳过摘要失败占位行，补齐防重跑验证与文档
- `6c96cc9` fix: 摘要提取失败写入消费占位行，避免下次重复总结
- `0f43886` fix: 增量窗口 created_at 按 UTC 转本地日期，修正跨时区窗口错位
- `df7d41d` docs: 澄清记忆/同剧关联配置与预览差异，example.ini 对齐默认值
- `f3dd05d` fix: 记忆清理/改名失败改为抛出，接口显式返回 500
- `dc32797` feat(ui): 测试结果弹窗增加预览与实跑差异提示
- `ae82cc7` chore: 删除 connection 中 6 个从未读取的迁移布尔死标志
- `ba30ea6` test: 合并配置页 tooltip 测试完整版（LLM + summary 弹窗）
- `e63aa9c` feat: 记忆配置前端表单 + 自检脚本 + 用户文档 + 弹窗注释悬浮化
- `f0c61dd` feat: 记忆统计与清理 API + 配置透传 + 校验契约
- `67b83cf` feat: summary 任务接入记忆——增量窗口/消费排除/失败通知

### [fix(archive): 补全 Archive subject 总集数 eps 字段，修复开启 Archive 后整部番标为看过失效](https://github.com/SanaeMio/Bangumi-syncer/pull/253)

- `c0e0830` fix(archive): 补全 Archive subject 总集数 eps 字段

### [fix: 识别上游网关以 200 返回的错误页，避免同步误报成功](https://github.com/SanaeMio/Bangumi-syncer/pull/252)

- `69925a9` fix: 识别上游网关以 200 返回的错误页，避免同步误报成功

## 2026-09-13

### [feat: 支持同一媒体服务器用户名绑定多个 Bangumi 账号并同步全部账号](https://github.com/SanaeMio/Bangumi-syncer/pull/249)

- `5a8342b` fix: 隔离 BangumiApi 实例缓存的账号命名空间
- `8cc19b4` feat: 支持同一媒体服务器用户名绑定多个 Bangumi 账号并同步全部账号

### [fix(matching): 日期择优跳过被拒候选并归一化空白原标题，修复玉响匹配误命中前传](https://github.com/SanaeMio/Bangumi-syncer/pull/248)

- `932fe3c` fix(matching): 日期择优跳过被拒候选并归一化空白原标题

### [feat: summary memory](https://github.com/SanaeMio/Bangumi-syncer/pull/243)

- `1346e82` chore: 删除 services/memory/models.py re-export 空壳
- `d9cff2d` fix: 响应 review——get_records_in_date_range 轻量化 + MemoryEntry 迁至共享层
- `fb0ea23` chore: 删除 connection 中 6 个从未读取的迁移布尔死标志
- `3a6d5ba` feat: 记忆服务层——写入/读取/清理闭环与 SummaryRecord 类型
- `4724b39` feat: Agent 工作记忆存储层——多对多消费标记 + FTS5 + 生命周期

### [refactor: llm 健壮性增强](https://github.com/SanaeMio/Bangumi-syncer/pull/244)

- `2ce033a` fix: 参数类 400 降级识别精确化——无关 400 走终态快速失败
- `8858cd8` chore: LLM 连通性测试降延迟 + 配置页 LLM 卡片注释悬浮化
- `027ba19` refactor: OpenAI 兼容 provider 支持 reasoning_effort 与 stop_reason
- `2951e5d` refactor: LLM 客户端健壮性增强——参数类 400 降级重试与终态错误不重试

### [fix(ui): 让原生 select 下拉菜单跟随明暗主题配色](https://github.com/SanaeMio/Bangumi-syncer/pull/250)

- `7a909779` fix(ui): 让原生 select 下拉菜单跟随明暗主题配色

## 2026-09-05

### [fix: 跨季链查找按季编号定位目标季修复Re0第四季夺还篇匹配错误](https://github.com/SanaeMio/Bangumi-syncer/pull/241)

- `237f3e6c` fix(cross-season): 未命中日志按 target_season 区分集数语义
- `555ff61d` fix(cross-season): 季定位未命中时不再回退全局 sort
- `8ffd76ec` docs: 去除跨季定位相关注释中的迭代表述
- `cd5917ba` docs(tests): 测试类注释改为描述函数当前行为
- `1feebc31` refactor(episodes): _extract_season_number 委托 extract_explicit_season
- `175f1d1d` style: 将测试文件 Optional 注解改为 X | None 以通过 ruff UP045
- `3435cb40` fix: 跨季链查找按季编号定位目标季条目避免误命中错误季

### [fix(archive): 在数据边界补全 Archive episode 季内话数 ep 字段修复逃跑殿下第二季匹配错误](https://github.com/SanaeMio/Bangumi-syncer/pull/242)

- `3b18de3a` docs(archive): ep 补全注释改为描述下游机制而非迭代表述
- `d45af5a9` test(archive): 补充 ep 补全的边缘场景用例
- `145c5c97` fix(archive): sort 每季重置时不补全 ep，保留季边界检测
- `f0ab7111` fix(archive): sort 为 NULL 时补全 ep 不抛异常
- `48e61075` fix(archive): 在数据边界补全 Archive episode 季内话数 ep 字段

## 2026-08-29

### [fix: 修复指定 release_date 时部分匹配扫描被过早截断](https://github.com/SanaeMio/Bangumi-syncer/pull/240)

- `b2f39e31` fix: 修复指定 release_date 时部分匹配扫描被过早截断

## 2026-08-28

### [fix: 修复配置备份接口路径穿越问题](https://github.com/SanaeMio/Bangumi-syncer/pull/239)

- `32e48459` fix: 修复配置备份接口路径穿越问题

## 2026-08-23

### [feat: Support anthropic](https://github.com/SanaeMio/Bangumi-syncer/pull/235)

- `4473067b` 思考模式最大token 自动抬高 && 鉴权 header 双发
- `2b171637` API 层增加枚举校验
- `75110985` 修改文档描述，支持 anthropic 以及思考强度
- `35887bad` 清理注释
- `81671f1e` 删除常量
- `79a1dcf7` 停止追踪specs
- `0cf82889` 停止追踪 specs
- `bbd98971` 停止追踪 specs
- `407ee97b` 常量
- `2501d8c4` 重构常量 & review 代码并修复
- `3a53bde1` 增加 anthropic provider
- `79d215ac` 修复测试用例类提示
- `b700727c` 修改测试用例类型提示
- `3c58a8ad` 存档 phase1
- `18a31625` 增加 e2e 及anthropic 的 provider 的测试用例
- `32a162a1` 测试用例
- `470df1ef` 配置案例增加思考强度和provider
- `64023f14` 支持 anthropic 的provider
- `6bf3b283` llm config的 api 传递的字段增加”思考强度“和 provider
- `1d20d7fc` 抽取重构 openai 作为 phase 2.2
- `d01b3945` 抽取工具调用作为 phase2.1
- `e215d98d` 抽取常量作为 phase1.1
- `f0222027` 更正 phase1
- `0238677e` 增加开发细节
- `f2fa267b` BDD 角度追加测试计划
- `76163c66` 追踪 specs

## 2026-08-17

### [fix(notification): 通知渠道可用变量提示对齐并补全](https://github.com/SanaeMio/Bangumi-syncer/pull/233)

- `3821b167` docs: 通知配置文档补充 AI 追番总结占位符
- `471c9b1b` fix(notification): 通知渠道可用变量提示对齐并补全

### [refactor: 重构fts缓存、匹配管线、优化bangumi-data性能、引入BK-tree 和trigram OR模糊算法。](https://github.com/SanaeMio/Bangumi-syncer/pull/232)

- `47c330a7` feat(records): 重写同步记录详情页并补全各 step 结构化 inputs/outputs
- `6a94f76d` refactor(sync): 执行阶段改为结果链传参，step 不再写 ctx 字段
- `da582e31` refactor(trace): 提取 _record_trace 字段填充为 MatchTrace.record_step
- `e55939a1` refactor(sync): 执行阶段管线化，新建 SyncPipeline 第二段管线
- `2c419ac0` fix(matching): 移除 bgm.last_match_method/last_hit_source 死状态，改 ctx.archive_hit + out_meta 显式传递
- `3d00b2b5` fix(trace): MatchTrace.finish() 幂等化，避免管道与外层重复结算
- `2f9b26b6` fix(matching): 守卫 _media_type_reselect 中 picker 返回 None 的场景
- `8b1a4b0e` fix(bangumi-data): 细粒度缓存失效 + 对称重建 + 双重检查锁，根治配置刷新重建风暴
- `8386f098` feat(ui): 跨季链命中路径区分展示（链/同IP改编·归档/在线）
- `bba1a34d` feat(api): 跨季链查找追加同 IP 改编兜底（动画↔真人剧同名场景）
- `3d4ed01d` fix(archive): FTS 自愈构建加锁防并发踩踏 + 重试回写测试
- `ed186aaf` docs(archive): BK-tree 内存/构建时间随标题数线性增长的说明
- `66ad8879` fix(match): bangumi_id_found 通知移到集数解析成功后
- `bd2e0f5b` fix(match): trace.normalized_title 回写修复
- `1bc5d9bd` fix(match): _pick_related_subject 恢复 subject type 过滤
- `7bfa8f81` fix(test): 放送日历测试改用调度器时区日期
- `d6326e56` fix(notify): 追番总结类型动态附加 + 订阅按 id 精确匹配
- `39d12550` fix(log): 兼容 stdlib 风格 % 占位符格式化
- `b37498a1` fix(match): real_action 搜索类型修正为 SUBJECT_TYPE_REAL(6)
- `afad5bf6` refactor(match): D-3 + D-4 + D-5 死代码清理
- `e2590364` fix(match): P2-1 + P2-2 + P2-4 + P2-6 轻微问题批量修复
- `70504ba1` fix(match): P1-5 + P1-6 + P2-5 跨季查找降级与空 sorts 处理
- `31847fc2` fix(match): P1-4 bgm_search 子 step trace 回写主 trace
- `4ac2deca` fix(match): P1-3 VariantFallbackSearchStep 全 miss 保留低相似度候选
- `140ecb8d` fix(match): P1-1 + P1-2 + P2-3 candidates/置信度时序对齐
- `2549769e` fix(match): P0-3 + D-2 get_target_season_episode_id 返回类型与死逻辑
- `cb63f357` fix(match): P0-2 + D-1 _pick_related_subject 死代码与 type 字段语义不一致
- `aa7ba5c4` fix(match): P0-1 API 命中时 final_match_method_detail 透传变体方法
- `d7656175` fix(match): archive 命中真人剧时降级 API 搜索并改选动画版
- `d434dc10` fix(match): 跨季查找 archive 空链降级 — 修复凡人修仙传 S01E81 同步失败
- `bae7cafa` feat(match): 阶段五 ArchiveShortcutStep 独立 + search() 读写分离
- `e12ed777` feat(match): 阶段四 SyncOrchestrator 编排器收敛 + BangumiSearchPort 只读端口
- `7cef1261` test(match): 阶段三 step 单测与 Injectable 单例隔离修复
- `5bab23ef` feat(match): 阶段三 _find_subject_id 接入 MatchPipeline 编排器
- `d034d441` feat(match): stage3 steps
- `ff5230fe` feat(match): 阶段二第二步 bgm_search 拆为4个step薄包装
- `d459ffcc` feat(match): 阶段二第一步 bgm_search 接入边界 step SearchResetStep/SearchFinalizeStep
- `0f72c812` feat(ui): 同步详情页匹配方式徽章展示与失败状态判断修复
- `de0787a0` fix(match): 跨季链命中补设匹配方式 + 重试成功回写匹配字段
- `cb5d84d8` feat(match): 匹配管道骨架阶段一 Context/Result/Pipeline + 单测
- `51164a39` feat(match): MatchTrace 新增 final_match_method_detail 细粒度匹配方式字段
- `caaf39e6` feat: 配置页新增BK-tree 开关
- `02b45985` chore: 补充 archive 配置示例与测试适配
- `b02a26ec` feat: bangumi_api 搜索/关系/归档捷径重构
- `1b9b54da` feat: archive FTS 模糊查询与别名匹配（bk-tree 索引/候选评分）
- `25fc0f72` feat: archive 标题归一化增强（搜索变体/媒体前缀/季集后缀/相似度评分）

## 2026-08-16

### [fix: Logger 一次性兼容 stdlib % 格式化](https://github.com/SanaeMio/Bangumi-syncer/pull/231)

- `ab9b2ff2` perf: 优化调度器日志打印
- `613a13dd` perf: 优化调度器日志打印
- `8296a112` fix: Logger 一次性兼容 stdlib % 格式化

### [fix(notification): 追番总结通知类型按任务动态展示，修复订阅匹配方向](https://github.com/SanaeMio/Bangumi-syncer/pull/229)

- `fc163643` test: 追番总结通知类型动态展示与精确匹配测试
- `670c6907` fix(notification): 追番总结通知类型按任务动态展示，修复订阅匹配方向

### [fix: 放送日历测试改用调度器时区，修复跨时区 flaky](https://github.com/SanaeMio/Bangumi-syncer/pull/230)

- `03999433` fix: 放送日历测试改用调度器时区，修复跨时区 flaky

## 2026-08-15

### [fix: bangumi-data 配置刷新后 TMDB 映射未重建，修复 Trakt 多季匹配失效](https://github.com/SanaeMio/Bangumi-syncer/pull/228)

- `0a07d55c` test: reload_config 清空后 TMDB 映射懒重建的测试
- `61458d6d` fix: bangumi-data 配置刷新后 TMDB 映射懒重建

## 2026-08-14

### [feat(trakt): 支持 OAuth2 Bearer 凭证模式与邮箱一键登录，规避 Trakt 应用创建/授权限制](https://github.com/SanaeMio/Bangumi-syncer/pull/226)

- `4f9f8d3f` fix(trakt): 按 review 字面要求隐藏 Bearer 授权入口并移除 access_token 契约
- `94083d2c` fix(trakt): 处理 review：并发安全、凭证切换与日志脱敏
- `ea3498e5` feat(trakt): 支持邮箱+验证码一键登录自动获取 Bearer 凭证
- `207a6a18` refactor(trakt): 凭证模式拆分为独立设置卡片并支持按需显示
- `1582c04d` feat(trakt): 支持 OAuth2 Bearer 凭证模式与同步中 401 自动刷新重试

### [fix: 修复升级时迁移配置的一些问题](https://github.com/SanaeMio/Bangumi-syncer/pull/227)

- `f605ebc0` fix: 修复升级时迁移配置的一些问题

## 2026-08-12

### [feat: 新增支持ECH #216](https://github.com/SanaeMio/Bangumi-syncer/pull/225)

- `399f8aae` fix(ech): DoH 单飞在超时后仍保持；首次查询延长等待以冷启动即用上 ECH
- `c9fef93f` perf(ech): DoH 查询改后台线程，调用方最多等待 1.5s 不阻塞
- `ef5732c2` test(ech): 补 DoH 解析盲区用例（wireformat 回退、多 Answer/CNAME）
- `ca584e6e` fix(tests): 同步测试在无事件循环的 xdist worker 下崩溃
- `632de911` test(ech): 补 utls↔httpx 真实接线断言（不 mock httpx）
- `f07e9549` fix(poster): 多用户模式下按媒体用户名预取「在看」列表
- `2be6eb35` perf(poster): 在看列表预取可达性检查、分页预算与短缓存单飞
- `5598d508` fix(web): CSP 图片域名白名单校验，拒绝配置值注入
- `5e4e7059` fix(api): get_subject 缓存键纳入 use_archive，隔离 Archive 与 API 数据
- `5ff4e433` perf(ech): DoH 查询并发单飞、失败结果短 TTL、utls 前置检查
- `2b48f03f` fix(config): config_schema 登记 ech_ech_config，统一 ECH 默认值到单一真相源
- `1890a473` fix(ech): verify=False 时不注入 ECH 上下文，OAuth 令牌 POST 不跟随重定向
- `2946b454` docs: 配置文档普通用户化改写，新增自建 ECH DoH（Total-ECH）教程
- `f430a600` feat(ech): 默认 DoH 端点切换为阿里公共 DNS，谷歌列为备选方案
- `45ddff60` fix(web): CSP 动态放行外域封面图（lain.bgm.tv 与配置的图片反代域名）
- `e1785e59` feat(poster): 在看列表批量预取封面 URL，未命中条目绕过 Archive 短路兜底
- `6153f876` feat(ech): 命中 ECH 目标域名的请求日志加 [ECH] 前缀
- `5b4cadbd` test(ech): 新增 ech.py 单测并适配受 ECH 改造影响的测试（auth/replay/trakt/schema）
- `8f926b90` feat(ech): BangumiApi/oauth/同步链路接入 ECH——ech_mode 透传、ttps.post 回归工厂统一降级
- `06ca6bdc` feat(ech): ECH 支持核心——utls 依赖、ech.py DoH 提供器、http_client 工厂 ech 参数与 [dev] 配置项

## 2026-08-11

### [refactor: 重构日志、修复一些小问题](https://github.com/SanaeMio/Bangumi-syncer/pull/224)

- `c8544f7f` fix(logging): 配置变更即时失效 log_level/debug_mode 缓存
- `9abe6556` fix: 修复测试
- `911bc38f` fix: 改进匹配逻辑
- `8678ab47` fix: 同步记录重试回填 run_id 并在详情页 head 提供日志跳转链接
- `0e062be3` fix(ci): release-zip if 条件引用 secrets 导致 workflow 无效
- `03ed99a0` refactor(archive): 下沉标题归一化/匹配/批量过滤到 bangumi_archive 模块
- `46a3f6ef` refactor(notification): 抽通用 ChannelHandler 消除 5 渠道 CRUD 重复
- `e5046f63` docs(main): 修正 request_context_middleware 注册顺序注释
- `dba7d525` fix(sync): reset_all_api_unreachable_flags 快照遍历，规避并发写入 RuntimeError
- `e2731a03` fix(bangumi-api): 网络错误时读接口短路返回，避免 AttributeError 中断同步
- `0c6ccd52` test: sync_main_flow 并入 test_sync.py
- `48f8da0a` test: 拆分 smoke 文件到 notification/trakt/logs/proxy
- `082ebe42` test: trakt_models 并入 trakt_sync_service
- `c90117b2` test: 合并 bangumi_api/bangumi_data 家族
- `b8739498` test: 合并 notifier 四文件到 test_notifier.py
- `cf416c56` test: 清理 SyncService 家族重复用例
- `c60d7cfa` test: 合并 security 双文件
- `c3ed0989` test: 合并 router 元数据测试并清理重复
- `a218d016` test: 合并 pages 与 app_release 测试文件
- `a5702f1e` test: 删除零风险重复测试文件，精简测试库
- `0ab778df` test: 隔离测试数据库到临时目录，修复测试污染真实 data/sync_records.db
- `57d21e82` fix(notification): 无通知规则时停发外部渠道通知，规则成为发布唯一闸门
- `d574c78b` feat: 日志页分组卡与同步记录详情展示 run/req/batch 关联 ID
- `9267c4ad` docs: 更新日志分级/轮转/请求批次关联的配置说明与 changelog
- `0f344c63` feat(request): X-Request-ID 请求关联中间件与 [req]/[batch] 日志标签
- `cac76dc8` refactor(logging): 收敛同步路径 INFO 日志，细节下移至 DEBUG
- `07d044fe` chore(logging): 日志轮转阈值由 2MB 调整为 20MB
- `1f9980c6` feat(logging): 新增 [dev] log_level 级别过滤与日志文件轮转保留
- `68740254` feat(core): 新增轻量可注入单例容器（Injectable），服务统一 get/set/reset 钩子
- `6338655b` feat(config): 配置变更回调统一失效进程级缓存，改配置无需重启生效
- `d729c4e1` refactor(database): 抽离幂等补列迁移工具，收敛手写 PRAGMA+ALTER 样板
- `142483c9` docs: 记录 Replay 匹配阶段快速降级与统一复位行为
- `ce164aa4` fix(bangumi-replay): 探测成功后统一复位不可达标记，匹配链路快速降级跳过
- `1d79b392` fix(api): API 不可达时读接口短路跳过重试，bgm_search 网络错误不中断 fallback
- `fa9f35f4` fix(archive): 导入 zip 时逐成员校验路径，阻止 Zip-Slip 路径穿越

## 2026-08-05

### [feat: 新增 Bangumi OAuth 授权与通用 OAuth 抽象层](https://github.com/SanaeMio/Bangumi-syncer/pull/223)

- `718545ce` feat: 内置 Bangumi OAuth 默认应用凭证，支持 GitHub Secrets 构建时注入
- `a206f770` docs: 同步变更
- `eb2c3ab2` fix(bangumi): OAuth 授权后调用 /v0/me 补全 username/nickname/avatar
- `36fed75b` feat(records): 同步记录页为 error/ignored 记录添加「加入屏蔽关键词」按钮
- `40e8413c` feat(config): 屏蔽关键词独立为卡片式 chip 组件
- `7d4e21fd` test: 补充 OAuth 改造与安全修复的测试覆盖
- `aebfba37` refactor: 清理 OAuth 改造后的死代码
- `7ad0d2b0` fix(bangumi_oauth): /start 校验 redirect_uri 白名单并移除响应死字段
- `20976e04` fix(bangumi_replay): 未映射已认证用户返回哨兵空集避免横向越权
- `7a9d3f9b` fix(bangumi): _persist_token docstring 与实现对齐
- `4d9a2b38` feat(ui): OAuth 状态与断开操作迁移到账号列表条目
- `bae85bab` feat(oauth): 动态 Redirect URI 并将 OAuth 按钮迁移到账号列表
- `5fafb6f8` fix(bangumi): OAuth 授权对齐 Trakt，授权后添加新账号到列表而非覆盖激活账号
- `df64be4b` fix(ui): OAuth 授权按钮点击时自动保存表单中的凭证避免空 client_id
- `276e7e3d` fix(oauth): Bangumi OAuth 路由 _require_user 未 await 协程导致认证失效
- `d5e45509` fix(ui): 修复 Bangumi OAuth 授权按钮点击无反应
- `7e88ace8` fix(accounts): 迁移完成后清理 INI 账号段兑现 DB 唯一真相源
- `231f942c` fix(db): access_token/refresh_token 加密存储避免 DB 文件泄露 token
- `81aba8c0` fix(accounts): 多用户模式下空 user_name 不回退激活账号避免数据串号
- `97a539d4` fix(auth): token 续期异常不再静默吞没，改为记录 warning 日志
- `cac3fed5` fix(auth): 令牌刷新添加 per-account/user 并发互斥避免重复调用 OAuth
- `1e7816e9` fix(airing-calendar): 多用户模式下 account 参数越权防护与账号列表隔离
- `6294a366` fix(trakt): 配置响应不再回传 client_secret 明文，改用 configured 标记
- `51b2dd81` fix(oauth): consume_state 检查 rowcount 防 TOCTOU 双重消费 state
- `f5a1d3be` feat(trakt): 授权成功自动追加 user_id 到 media_server_usernames 并提示
- `b44b35a4` fix(config): 跳过遗留 [bangumi] 段避免 access_token 明文泄露与回写分裂
- `9b644e2e` fix(accounts): 中文逗号解析与单用户段迁移条件对齐
- `d5cfc0ca` fix(db): save_account 改用原子 upsert 避免并发 UNIQUE 冲突
- `3a01b220` fix(accounts): 迁移后 is_active 永不持久化导致激活标记丢失
- `d20635f9` fix(episodes): 续集链遍历加 visited 防环避免死循环
- `1c5cc0d5` fix(trakt): OAuth 回调双重消费 state 导致授权必失败
- `7d3fc382` fix(replay): _resolve_user_filter 命名空间错误导致多用户模式空队列
- `bfe115d7` fix(db): _execute_with_lock 异常时主动 rollback 避免事务残留
- `8a2f8616` fix(ui): 修复 Bangumi 账号列表 XSS 与 OAuth 授权流程
- `c96b3706` test: 清理多账户迁移后过时的测试用例
- `fd5df050` feat(ui): 前端 Bangumi 账号列表展示与管理
- `ef16268d` refactor(api): 业务接口适配 DB 账号访问层
- `24f30fc1` feat(api): 新增 Bangumi 账号管理 API 并注册到应用
- `f8c2e227` refactor(core): 移除多账户 INI 处理与 sync.mode 配置
- `6fc680f8` refactor(sync_service): 权限校验与账号配置读取切到 DB
- `666790dd` refactor(api+factory+replay): 账号读取切到 DB 访问层
- `8e31c7d3` refactor(bangumi/auth): 令牌落地与状态查询切到 DB 账号目录
- `4e9caf5d` feat(accounts): 扩展 DB 访问层提供与 INI 同语义方法
- `40ffbfff` feat(db): bangumi_accounts 增加 private 列并对齐仓库层
- `cbedb99d` feat: 新增 Bangumi OAuth 授权与通用 OAuth 抽象层，并引入 SQLite 账号目录
- `54932f2e` feat(match): add confidence threshold to sediment low-similarity matches to pending review
- `19195faf` feat(episodes): enable RelationMixin in prequel traversal + add feature1/2 regression tests
- `6112aacd` feat(bangumi_api): add RelationMixin with Archive shortcut for sequel/prequel series traversal

## 2026-08-01

### [feat: 首页新增我在追番的条目卡片、通知类别、修复一些小问题、重构文档。](https://github.com/SanaeMio/Bangumi-syncer/pull/221)

- `65578e70` style(dashboard): djlint 格式化 dashboard.html
- `6194533e` style(archive): ruff format 修正 _archive.py 格式
- `993634cd` docs(changelog): 修正错误 PR 编号 + 移除 3.11.3 之前条目
- `e7400a70` perf(archive): 启动时为老库补建关键索引 idx_episode_airdate
- `e95df1f9` feat(airing-calendar): 多用户切换 + 移除 only_watching 参数
- `52cce7d0` feat(airing-today): 今日放送补写站内信 + 失败语义对齐"我的追番"
- `6707dfa8` docs: 重构文档结构并修复死链
- `802bc0ca` fix(config-schema): notify-airing-today 段补全 notification_types 关联
- `47754f75` fix(airing-today): 任务失败/超时触发 scheduler_job_failed 通知
- `3e16f5ec` fix(airing): reload_config 异常降级避免 API 500 与调度器报错
- `18608d2f` fix(bangumi-api): 在看列表缓存加锁防止并发竞态
- `8a5a72c7` fix(airing): 今日日期改用调度器配置时区避免跨时区错位
- `bae17e27` fix(bangumi-api): 修正 get/post/put/patch 返回类型注解
- `bf7b953a` fix(bangumi-api): 抽取共享工厂并修复资源泄漏
- `ca3721a5` fix(airing-calendar): catch 分支重置 row.style.display
- `f706ff4a` fix(config): 统一 notify-airing-today.enabled 默认启用语义
- `649dcf71` test(bangumi-api): 修复收藏列表测试 mock 与新实现不匹配
- `2b611064` fix(config): 修复 _bangumi_archive.html 多余 &lt;/div&gt; 导致 Replay/Airing Today 段渲染在 form 外
- `3cc01bd8` fix(airing): 修复在看列表获取与日历卡片展示问题
- `cffa51a6` docs: 补充番剧放送日历与今日放送提醒说明
- `e2b50a14` feat(notification): 新增 airing_today 今日放送定时提醒
- `a3a08cca` feat(dashboard): 新增番剧放送日历视图
- `cc8439b8` feat(api): 新增番剧放送日历 API 端点
- `e48085a6` feat(bangumi-api): 新增用户收藏列表批量查询与在看列表缓存
- `671dd1a8` feat(archive): 新增 episode airdate 索引与按日期范围查询方法

## 2026-07-31

### [fix: 修复导入时白屏、修改下载、导入变更为本地行为、修复导入时没有清空旧库](https://github.com/SanaeMio/Bangumi-syncer/pull/220)

- `f1bb4f7a` fix(archive): 启动时清理 .tmp 残留子目录
- `8213cf13` fix(archive): 上传磁盘检查提前到保存文件前，与下载流程对称
- `643a6df7` fix(archive): 修复 SSE cached 为 None 时 AttributeError + 同 stage 不同 percent 被跳过
- `90651806` fix(archive): SSE 进度去重 + 调整阶段顺序 + 下载节流改 100MB
- `cafcf7d0` fix(archive): 修复导入进度直接跳到 100% 的问题
- `22a1b3ce` fix(archive): 上传导入流程补充磁盘空间检查
- `6c828483` fix(archive): 修复下载阶段前端卡死（进度推送过频+历史日志暴涨）
- `84436e4d` fix(archive): 清空旧库前先 invalidate FTS5 连接，修复 WinError 32
- `76687c30` fix(archive): INSERT → INSERT OR IGNORE 容错 dump 重复主键
- `d2c79d46` perf(archive): 优化导入性能并修复前端白屏
- `c8b4f005` perf(archive): 临时文件统一到 data_dir/.tmp/ 并解压后立即删 zip

### [refactor: 前端重构，对配置、通知、调度器进行基态封装联动](https://github.com/SanaeMio/Bangumi-syncer/pull/219)

- `ddee4b67` fix(ci): e2e-tests 修复 --trace 误用为 pytest 内置选项导致 collected 0 items
- `0049a862` fix: 修复登录测试
- `92f52f94` fix(frontend): P0-P2 前端问题修复 + dashboard.js 抽出
- `b9637dd9` test(e2e): P0-P2 E2E 提速 + 失败捕获 + 补关键用例
- `32d008ca` refactor(frontend): P7b-2 拆分 style.css 按功能分区
- `3d09ed49` refactor(frontend): P7b-1 拆分 app.js 按功能模块
- `6aa1f50b` test(e2e): 引入 Playwright E2E 测试基础设施
- `6ea6f8dc` refactor(notification): 通知系统重构 + 调度器状态卡修复 + 死代码清理
- `5a4b0924` refactor(dashboard): 调度器状态卡复用时间线样式，支持 cron 描述展示
- `1d5ba602` feat(dashboard): 美化调度器状态卡，展示任务名/触发器/下次执行时间
- `aed9fa77` refactor(config): P6 调度器状态卡，侧栏动态展示调度器运行状态
- `0fd8ad02` refactor(config): P2 配置 schema 端点驱动前端默认值，消除散落硬编码字典
- `bb87badd` refactor(notification): P5 通知配置联动收尾 + 清理未使用代码
- `b765066a` refactor(notification): P4.4/P4.5/P4.7 通知配置段重命名 + 统一迁移到 NotificationService
- `057579cb` refactor(config): P6 前端通知类型动态加载，消除硬编码复选框
- `90b59e25` refactor(config): P5 配置保存统一联动改为遍历 SectionMeta 驱动
- `b52633e1` refactor(notification): P4.1/P4.3/P4.6 通知类型注册表 + 统一服务 + 类型 API
- `ebcb6744` refactor(scheduler): P3 引入 SchedulerRegistry 单例统一管理调度器
- `ca3fd8dd` refactor(config): TOC 声明式生成与侧栏阴影裁切修复
- `6e950537` refactor(config): 配置页改为双栏布局，TOC 与操作按钮移至左侧 sticky 侧栏
- `d3f82fbd` refactor(config): P2 引入 ConfigForm 库实现前端自动序列化与配置注入
- `1f8e0297` refactor(config): P1 拆分 config.html 巨石模板为 12 个子模板
- `87e9731c` refactor(config): P0 引入 SectionMeta 注册表作为配置元数据单一真相源

## 2026-07-30

### [refactor(archive): FTS5 trigram 替代内存索引 + 磁盘阈值上调至 4GB](https://github.com/SanaeMio/Bangumi-syncer/pull/217)

- `94974af3` test(archive): 修复 test_path_change_triggers_rebuild 过时注释
- `1179ac6d` docs(archive): 统一磁盘占用口径与阈值下调到 3000MB
- `d8ee946b` refactor(archive): FTS5 查询层改进——aliases 精排、注释修正、清理死代码
- `3a5aa33e` fix(archive): 修复 _build_fts5_index 批量插入逻辑，攒满 _BATCH_SIZE 再插
- `9a01d40d` refactor(archive): 移除死表并按 type 过滤导入，单库体积降至约 0.8GB
- `de12676e` refactor(archive): FTS5 trigram 替代内存索引 + 磁盘阈值上调至 4GB

## 2026-07-29

### [refactor: 将匹配流程重新梳理重构、Replay 、Archive 解耦](https://github.com/SanaeMio/Bangumi-syncer/pull/214)

- `0069d775` fix: 修复测试逻辑
- `246453a1` perf(db): 为 pending 表的 sync_record_id 列添加索引
- `d19833ad` docs(retry): 修正注释 [bangumi-archive] 为 [bangumi-replay]
- `236d3792` refactor(retry): 抽取重试 item 构建逻辑到 sync_service 单一入口
- `50d750c1` fix(replay): trigger_immediate_run 防抖改用 time.monotonic()
- `0fb884d3` fix(replay): 统一补发成功状态语义为 retried 避免统计分裂
- `42053292` refactor(frontend): 抽取公共映射弹窗组件并复用于候选确认
- `e36f140b` docs: 同步本分支改动说明并润色相关文档
- `c819a76e` feat(replay): 入队后立即触发补发调度
- `2a807819` feat(replay): 调度器空队列短路并支持立即触发补发
- `50a010ae` feat(records): 详情模态框驱动数据收起与耗时表交互增强
- `c25f5a81` feat(frontend): match_trace 增强字段前端展示
- `3ed32c11` feat(match_trace): 增强 trace 字段提升排错体验
- `9906f846` refactor(frontend): match_trace 前端统一化改造
- `5a7ca757` feat(pending_candidates): 候选列表按 score 降序排序展示
- `549c4cb3` feat(search): 下调旧版搜索候选过滤阈值从 0.5 到 0.3
- `ccc9a373` feat(match_trace): 候选 score 填充（trace 内候选填入相似度 score 用于排序）
- `13411299` feat(match_trace): bangumi_data 候选回传到 trace
- `aca60695` feat(records): records 页跳转候选详情
- `9fc521b0` feat(candidates): 候选确认即补发（auto_retry）
- `b0df1623` feat(candidates): confirm 时校验 subject_id 有效性
- `a237e009` feat(candidates): 手动指定 Bangumi ID 前端入口（方案A）
- `48afd324` docs: 更新 configuration.md 链接指向独立 replay 文档，README 补充离线容错特性说明
- `844edee3` docs: 拆出独立的 bangumi-replay.md，明确 Replay 与 Archive 解耦但功能互补
- `7474ca76` docs(http_layer): 修正 mark_api_unreachable 过时注释，准确描述读写降级分别由 replay/archive 控制
- `9d9c4b4c` feat(pending_candidates): 关联 sync_record_id 形成候选确认回写闭环
- `c33a85ab` feat(records): sub_status badge 增强，按 message 推断细粒度子状态
- `7a154cc0` feat(retry): 统一重试入口，放开 status 限制并清理 queued 关联 pending 行
- `1c67aef9` feat(replay): 补发事件回写 sync_records 状态形成闭环
- `d26d7ff0` refactor(config)!: 拆分 [bangumi-replay] 独立配置段与 archive 解耦

### [fix(security): 修复 import_local 路径穿越漏洞 (CWE-22)](https://github.com/SanaeMio/Bangumi-syncer/pull/215)

- `3aa0cb11` fix(security): 修复 import_local 路径穿越漏洞 (CWE-22)

## 2026-07-28

### [refactor: 重构前端fetch请求、工具函数收敛、模块化拆分](https://github.com/SanaeMio/Bangumi-syncer/pull/212)

- `b4285fa0` fix: 格式同步
- `03e9e2da` fix(frontend): 修复 apiFetch returnResponse 未生效导致登录页报错
- `7a7c35f0` refactor(frontend): 抽取 format.js + badges.js + table-utils.js
- `e144938a` refactor(frontend): 抽取 setButtonLoading 与 modal-utils
- `354b9397` refactor(frontend): fetch -&gt; apiFetch 补充迁移
- `20e02c21` refactor(frontend): fetch -&gt; apiFetch 第四批迁移
- `99f2ff83` refactor(frontend): fetch -&gt; apiFetch 第三批迁移
- `acaf08c3` refactor(frontend): fetch -&gt; apiFetch 第二批迁移
- `dd957727` refactor(frontend): fetch -&gt; apiFetch 第一批迁移
- `3f47c062` refactor(frontend): 修复 getSourceColor 与 mappings showLoading bug
- `31162e4e` refactor(frontend): 删除 8 处重复 escapeHtml 并统一 showAlert
- `2c2cac19` refactor(frontend): app.js 工具函数升级与死代码清理

### [feat: 集成 bangumi/Archive 离线查询层、优化查询逻辑](https://github.com/SanaeMio/Bangumi-syncer/pull/210)

- `dfe7087e` fix(archive): import_local 临时文件清理加固
- `264691e6` fix(background-tasks): 后台任务统一注册与生命周期管理
- `a55adcf0` fix(replay): 入队 user_name 改用 payload 中的媒体库用户名
- `a8cace88` fix(notifier): 通知冷却维度按 item 粒度细化
- `c5104988` fix(replay): 优化批量补发策略与手动补发计数
- `7a0c1b6a` test: 清理弱断言测试并补 replay_scheduler 单测
- `2f4fe727` refactor(arch): 修复 core↔utils、utils↔services 分层违规
- `7852d1fb` refactor(config): 抽取 BangumiApi 工厂与写映射 helper
- `69d69774` fix(sync): 修复多用户隔离、剧场版降级与队列清理
- `65bd4c6a` test(bangumi-replay): 修复 mock_database fixture 未生效
- `9d99ab1a` fix: 格式同步
- `2b809d32` doc(bangumi-archive): 补全 Replay 待同步队列文档
- `4e71be23` fix(bangumi-replay): 修复 API 探测始终不可达
- `0e305cd3` feat(bangumi-replay): 新增 API 不可达时的离线同步队列与补发
- `077a59b2` fix: 格式同步
- `3c07f027` doc: 新增bangumi/archive文档
- `79882417` feat(fongmi): 批量设备扫描日志降噪
- `45625061` feat(sync): 新增 archive 匹配方式到同步记录详情步骤
- `bc8bf404` fix(config): bangumi-archive 段被误归入多账号导致前端读不到 enabled 状态
- `b78b0cf7` fix(api): _find_episode_by_sort 优先 archive 短路避免对长篇动画走 API
- `599f02d3` fix(archive): _load_config 自动迁移 data_dir 到 archive 子目录
- `4f943305` fix(sync): season&gt;1 且标题无季度信息时启用改选逻辑
- `73e243e2` feat(archive): 数据目录迁移到 ./data/archive 并清理旧索引缓存
- `ee9c7f47` feat(database): 迁移 sync_records.db 默认路径到 data/
- `46384f9b` feat(archive): 接入 try_find_sequel_chain 到 _walk_chain_for_episode 消除孤儿方法
- `a80b36c7` fix(archive): 修复 try_get_episodes/try_get_related_subjects 在 archive 不完整时静默返回空数据
- `6d431af6` feat(api): 扩展 bgm_search 变体生成提升 API 路径匹配率
- `efbc08a4` fix(tests): 显式关闭 sqlite 连接修复 Windows 临时目录清理失败
- `5448d813` fix: 修复集匹配季度边界检测与续集链计数
- `6d1ffc49` feat: archive集成查询、优化匹配
- `f0ac1bd6` fix(tests): conftest 优先用 config.example.ini 而非 config.ini
- `c9d631b8` fix(tests): 修复 bangumi-archive.enabled=True 卡死测试 + asyncio.run 污染事件循环
- `cad3da83` perf(bangumi-archive): 标题索引后台构建 + 磁盘缓存，消除首次查询 111s 阻塞
- `5abe297f` perf(sync): BangumiApi 实例按用户缓存，避免重复构造 httpx.Client
- `9dcdbfb9` fix(bangumi-archive): 第二期 B3 search_old 短路 + 测试隔离修复
- `1b57fef3` feat(bangumi-archive): 第二期 B2 标题索引 + search 短路接入
- `a0a6dc97` feat(bangumi-archive): 自实现 wiki-parser 解析 infobox 为 API 兼容格式
- `b75bbffc` feat(bangumi-archive): 第二期 A2-A4 Archive 短路接入业务读路径
- `be18a30b` feat(bangumi-archive): 集成 bangumi/Archive 离线查询层第一期基础设施

### [[perf]优化 pre-commit 测试用例执行](https://github.com/SanaeMio/Bangumi-syncer/pull/211)

- `1188d598` 删除一个 slow 标记
- `674812d7` dev 依赖引入 pytest-xdist 并行执行测试用例  && 标记两个耗时用例为 slow，pre-commit 跳过耗时用例，并利用并 行降低 pre-commit 耗时

## 2026-07-26

### [【docs】更新 trakt 文档：通过 SSH 端口转发以应对 Trakt 严格校验回调地址](https://github.com/SanaeMio/Bangumi-syncer/pull/209)

- `390c2eb0` 更新端口
- `8fd78edb` 修复文档错误
- `97bd0d50` 更新 trakt 文档：通过 SSH 端口转发以应对 Trakt 严格校验回调地址

### [[feature]增加通知类型- AI 总结](https://github.com/SanaeMio/Bangumi-syncer/pull/205)

- `79a841d6` 修复复选框无法选中的问题
- `1895ad56` 改名时同步修改用户订阅的 notification_type
- `9f130748` 测试用例适配 /llm -&gt; /api/llm
- `60e7dc75` 统一 llm 层 API 以 /API 开头
- `4bfcebd3` 测试用例适配默认值 -1
- `466374d3` 传递给 LLM 的观看记录条数支持设置为 -1，即无限制 && 修改文档，提示用户在半年和全年 limit 设置为 -1
- `7654e8f0` 修改半年番总结
- `b30bf768` 优化季度番总结逻辑
- `5882334d` 增加 inbox 测试
- `b6c71967` 修复LLM失败时，错误提示同步失败
- `7274af4d` 修复测试用例
- `4a85847d` 优化前端细节
- `0298c424` LLM 和 Summary 失败时，增加 inbox 通知以及跳转
- `a143bdcf` repository 层增加 inbox 插入语句
- `d6748e11` 提示用户使用 V1 结尾的 Open AI兼容接口
- `a22fa08d` 文档拆分 LLM 配置和 AI 追番总结
- `285b41c0` 优化文档，提供月度/年度配置的 cron 表达式供用户参考 && 增加多种类型的 prompt 模版供用户参考
- `f323e5b3` - TestTypeMatches（6 个用例）：覆盖 all 匹配、精确匹配、含空格匹配、前缀误匹配（mark vs   mark_success）、空 types、单类型无逗号   - test_partial_update_only_enabled：验证只传 {"enabled": False} 时写入正确的配置节，不     会创建空的 summary- 节，且其他字段保持原值
- `24814533` 修复 generate_summary 中 latency 恒为 0 的情况
- `2342ccc5` 调用 LLM 失败时，通知内空内容改为明确的失败提示
- `1f959b75` 修复 name 为空造成 summary 配置保存为空的问题
- `88e76edb` AI追番总结的测试从调试工具中移入配置管理
- `9049b9ab` 增加调用错误日志记录
- `8c172237` 修复多次保存导致的密钥丢失问题
- `1c3cf48d` 修改 /api/summary/llm 为 /llm
- `f69b53e1` 修改注释为中文
- `9e3cfcce` 修复 provider 导致的测试用例失败
- `5aa36542` 删除 TODO
- `fc50d3ae` 删除 TODO
- `8bae2894` 为兼容 anthropic 预留 provider 字段
- `6a32023a` 增加说明文档 && 配置案例
- `f242b25f` 测试 summary 时，跳过冷却
- `b91837f4` summary 使用 name 代替 ID 索引
- `6a202985` 区分 total_tokens/prompt_tokens/completion_tokens && LLM 调用使用全局 Proxy && 增 加 refusal 字段，显式抛出 refusal
- `96f890fa` 修改 dashboard 中显示数据为 30 天内
- `e136755c` summary 删除 id 字段，该用 name 字段索引
- `304b9b21` 精准匹配通知类型
- `7030cff3` 修复 config 零值被当作 falsy 的问题
- `507ac009` 修复 llm_client 单例模式在修改配置后未刷新的问题
- `cb000005` 在配置保存时忽略掩码
- `8fe211bd` 跳过写入掩码值写入
- `5ea694a5` 对 *** 开头的敏感信息返回空值
- `162a4dc4` 删除重复 escapeHtml
- `9446695e` 修改测试用例
- `5fc92b6b` 按照notification_type归一化 summary_type
- `c59dd964` 导出 providers 模块
- `3ef3b5b2` 从 _log_usage 封装 _log_success 和 _log_error
- `233b5d03` 停止追踪 spec.md
- `47f839e4` 替换测试用例中未使用的对象
- `d0363cc3` 修改 review && 修改 API路径 llm-&gt;llm/config && LLM定时任务时区服用现有 schedule_config && 新建追番总结时，增加前端默认值
- `83ba67d6` 修改 review，提高代码可读性
- `2ce34ecc` review app/core/config.py
- `a2fc3c6d` review remained part
- `293debb4` review llm_usage.py
- `ea5b9e54` review summary.py 完成
- `255c36c9` 删除独立页面，明确 summary 作为 notify_type 的一种
- `d5da47c2` 存档 AI 开发 Spec

## 2026-07-25

### [perf: 集成 bangumi/common 常量，消除关联/条目/收藏类型硬编码](https://github.com/SanaeMio/Bangumi-syncer/pull/207)

- `14c5d95a` perf: 优化搜索权重和匹配类型
- `22adda65` refactor: 提取文本处理字典常量到 utils/text_constants.py 统一管理
- `4cdaf01a` feat: 集成 bangumi/common 常量，消除关联/条目/收藏类型硬编码

## 2026-07-24

### [fix: 修复重试时因信息缺失导致匹配错误的问题，完善输入持久化](https://github.com/SanaeMio/Bangumi-syncer/pull/206)

- `dc278592` fix: 修复重试时因信息缺失导致匹配错误的问题，完善输入持久化

## 2026-07-23

### [fix: Trakt 同步时 TMDB 映射支持季度感知查询与日期择优，修复无职第三季匹配错误](https://github.com/SanaeMio/Bangumi-syncer/pull/204)

- `6c8da1c6` test: 增加 TMDB 映射多条目选择、季度感知查询与日期回退测试
- `8c349ecb` fix: Trakt 同步时 TMDB 映射支持季度感知查询与日期择优，修复无职第三季匹配错误

## 2026-07-21

### [perf: 改进 title_diff_ratio 算法](https://github.com/SanaeMio/Bangumi-syncer/pull/203)

- `59e3beaa` perf：改进 title_diff_ratio 算法

### [perf: 重构同步记录详情、多季连续ep数字的场景进行调优、新增deadline防止循环卡死、regex替换re防止病态正则](https://github.com/SanaeMio/Bangumi-syncer/pull/202)

- `43b7ca58` perf: 重构同步记录详情
- `22b326ba` feat: 多季连续ep数字的场景进行调优
- `dfa432f5` fix: 修复番组不存在或集数过多失败时没有写入同步记录

## 2026-07-17

### [fix: 修复多用户模式保存配置失败的问题](https://github.com/SanaeMio/Bangumi-syncer/pull/201)

- `5780270a` fix: 修复多用户模式保存配置失败的问题

### [feat: 细粒化同步权限错误提示 + 测试接口可选跳过用户名校验](https://github.com/SanaeMio/Bangumi-syncer/pull/199)

- `e3ba552b` doc: 同步增加测试同步跳过用户名校验选项
- `24f36fc4` feat: 细粒化同步权限错误提示 + 测试接口可选跳过用户名校验

### [perf: 匹配记录合并到同步记录中，重写同步记录明细、表格组件响应式优化](https://github.com/SanaeMio/Bangumi-syncer/pull/200)

- `df1e1d86` perf: 表格组件响应式优化
- `4a7d28c5` perf: 匹配记录合并到同步记录中，重写同步记录明细

### [chore: 简化 PR 模板：移除提交前检查清单，pre-commit钩子可自动完成提交前的检查](https://github.com/SanaeMio/Bangumi-syncer/pull/198)

- `7c6063e9` chore: 简化 PR 模板：移除提交前检查清单，pre-commit钩子可自动完成提交前的检查

### [fix: 修复匹配记录不能打开，完善详情字段展示](https://github.com/SanaeMio/Bangumi-syncer/pull/197)

- `3cd076fc` fix: 匹配记录详情点击报错 — getMethodBadge 函数未定义
- `39aa790b` fix: 匹配记录详情增强 — 将 API 全部数据填充到详情页面

### [perf: 统一表格样式并适配移动端、合并匹配和同步测试工具](https://github.com/SanaeMio/Bangumi-syncer/pull/196)

- `b7271cda` perf: 合并匹配和同步测试工具
- `970b7e14` perf: 统一表格样式并适配移动端

### [fix: 修复升级后首次启动误删历史同步记录的问题](https://github.com/SanaeMio/Bangumi-syncer/pull/195)

- `1c288b70` docs: 文档优化
- `39d7925f` fix: 修复升级后首次启动误删历史同步记录的问题

## 2026-07-16

### [feat: 新增匹配记录、候选确认、OVA、OAD、三次元电影电视的支持、自定义映射增加正则支持。](https://github.com/SanaeMio/Bangumi-syncer/pull/194)

- `7a61182f` doc: 修改配置描述
- `6cedf5d7` perf: 修改清理表默认值
- `46f1080f` fix: 修复 Dockerfile/release-zip/.dockerignore 引用 config.ini 的问题
- `8744b540` docs: 新特性说明 + 全文档润色 + 代码级排错
- `e4656a6e` perf: 列表查询去除 match_trace + retention 自动清理 + config 模板化
- `c1a3bf52` test: 合并媒体类型测试并用真实数据替换占位符
- `b3253338` refactor: test_match 不再写库，消除统计污染
- `852e8507` fix: _build_retry_item 支持 ova/oad/real_action 媒体类型
- `f2b82110` fix: pending_candidates 去重 + 通知冷却细化
- `5c288a17` fix: _last_match_trace 竞态改为返回值传递
- `94be5894` feat(drivers): Jellyfin 和 Trakt 接入 OVA/OAD/三次元检测
- `5db92f09` feat(notifier): 候选确认触发通知
- `ab76f3e8` fix: 匹配记录icon不显示
- `abb3f906` feat(mappings): 合并正则规则到统一界面 + 匹配记录icon
- `c2fd9df1` feat(mappings): 映射管理增强 + 匹配记录跳转
- `d7851e1b` feat(records): 匹配记录与同步记录关联展示
- `643fb40c` fix(search): 修复候选筛选 + 支持单subject连续编号多季
- `9b3929ee` fix(match): season=1 时改选无季度后缀的第一季候选
- `b60ce3e5` test(match): 补充匹配记录与媒体类型检测测试覆盖
- `1cd5cf33` feat(match): 匹配记录增强 + 各驱动 OVA/OAD/三次元支持
- `6f490ae1` feat(match): 标题归一化 + top-N platform 加权排序
- `43f417d2` feat(match): 候选沉淀 + 确认 UI
- `6b1a3856` feat(match): 续作链 platform 隔离 + webhook 适配层透传
- `f1570499` feat(sync): 增加三次元（日剧/电影）匹配支持
- `2e064759` feat(match): 映射管理页面支持季度感知 + 正则规则
- `980858d0` feat(match): 映射服务支持季度感知 + 正则规则匹配
- `6defa214` feat(match): 新增匹配测试接口 + 调试页面匹配测试面板
- `db1ac3a1` feat(match): 匹配记录无需 debug 模式即可查看
- `f691896e` feat(match): 新增匹配记录 API + trace 详情接口
- `40141839` feat(match): 新增匹配记录页面 match_records.html
- `1e5c77d6` feat(match): 新增匹配记录页面路由 + 导航项
- `223d0ede` feat(match): _find_subject_id 注入 MatchTrace 收集匹配过程
- `825c2e9e` feat(match): 新增 MatchTrace 数据结构 + sync_records 表匹配追踪字段

### [feat: 新增日志智能分组功能](https://github.com/SanaeMio/Bangumi-syncer/pull/193)

- `bd9f4a7f` feat: 新增日志智能分组功能

### [feat: 新增几个增加体验的小功能](https://github.com/SanaeMio/Bangumi-syncer/pull/192)

- `28b2cbe5` feat: 新增常见同步失败原因文档 + 重试弹窗加宽并链接文档/issues
- `7af9eb06` feat: 同步记录重试时实时输出 debug 日志到弹窗
- `2da5785c` feat: 映射管理批量导入支持 JSON 文件上传
- `4d9f821d` feat: 登录后跳回原页面

## 2026-07-15

### [perf: 优化首页时间线海报异步加载](https://github.com/SanaeMio/Bangumi-syncer/pull/191)

- `58e2904a` perf: 优化首页时间线海报异步加载

### [chore: HTTP 成功请求日志改为 DEBUG](https://github.com/SanaeMio/Bangumi-syncer/pull/190)

- `b881b8c8` chore: HTTP 成功请求日志改为 DEBUG

### [perf: Web UI全面焕新，统一视觉语言与交互细节](https://github.com/SanaeMio/Bangumi-syncer/pull/189)

- `2f74e07b` perf: 前端全局翻新，优化整体页面样式和细节

### [docs: 文档细节优化](https://github.com/SanaeMio/Bangumi-syncer/pull/188)

- `74ab8913` docs: 文档细节优化

## 2026-07-14

### [#186 重构技术栈、驱动分包](https://github.com/SanaeMio/Bangumi-syncer/pull/187)

- `57cfa741` fix: HTTP 日志合并 + fongmi 日志格式化修复
- `fb920dd3` feat: 批量探测场景静默 HTTP 基类失败日志
- `9e30d8e7` feat: fongmi 设备扫描日志合并显示
- `257696c8` feat: fongmi 轮询日志合并
- `7a0f5b88` fix: pre-commit hook 行尾转 LF + 步骤编号修正
- `f93dacec` style: ruff format 自动格式化
- `420d0627` fix: httpx verify 弃用 + RuntimeWarning 修复
- `5b6b7210` fix: FastAPI on_event → lifespan, TemplateResponse 参数顺序
- `3e4c73a2` fix: Pydantic V2 弃用警告修复
- `9e82f58b` chore: 添加 .gitattributes 行尾规则
- `2ec66109` fix: 修复 config.ini 污染
- `f0071648` fix: 修复 flaky mtime 测试
- `c8413fc5` feat(fongmi): support movie/剧场版 detection
- `e939dd6e` refactor(http): wrap httpx into HttpClientBase with layered logging
- `4e3c6f5b` test(TC): add tests for retry, http_client, and fongmi API
- `609154d5` refactor(CQ4): complete missing type annotations
- `0d6300d2` fix(CQ7): fix docker_helper type annotation any→Any
- `beb35f74` refactor(CQ6): narrow except Exception to specific types
- `5a0b3e2b` refactor(CQ3-4): unify HTTP retry logic via shared retry utility
- `f5d189d1` refactor(CQ3-3): extract media server task submit/run helpers
- `f4891143` refactor(CQ3-2): extract webhook dispatcher to dedup media server handlers
- `2d2afaba` refactor(CQ3-1): extract BaseRepository to eliminate DB closure duplication
- `1f45d69c` refactor(CQ2-4): split bangumi_data.py (1120 lines) into bangumi_data/ package
- `df2f1798` refactor(CQ2-3): split sync_service.py (1181 lines) into sync_service/ package
- `72b6c5fd` refactor(CQ2-2): split bangumi_api.py (1044 lines) into bangumi_api/ package
- `68505347` refactor(CQ2-1): split notifier.py (1158 lines) into notifier/ package
- `fda96945` refactor(CQ1): split 6 long functions into focused helpers
- `9d65fdaa` refactor(A3+A5): lazy-load singletons and unify import patterns
- `e7cd61d7` refactor(P3): wrap sync blocking calls in async code with asyncio.to_thread
- `e629607e` refactor(A2): eliminate API layer direct database access
- `2e248652` refactor(A1): split DatabaseManager God Class into repository subpackage
- `66cf87ec` refactor: error handling, performance, and function splitting
- `bdda4ddd` doc: fix build
- `fe360c2d` doc: 润色文档、添加快速上手指南
- `0e14d9ff` fix: requirements.txt移除requests
- `24f518e9` refactor(A4): unify httpx client creation into factory module
- `3659ebbc` refactor: trakt 驱动清理死代码与未使用字段（Phase 5 最小调整）
- `53ad2b4b` refactor: 自定义 Webhook 逻辑抽象为独立子包，新增驱动接入指南
- `74eff2eb` refactor: 全量替换 requests 为 httpx 统一 HTTP 库
- `4e65dc74` chore: #186 强化 pre-commit 钩子，测试后自动恢复 config.ini
- `bf0d1fd9` chore: #186 新增 pre-commit 钩子强制执行测试与 ruff
- `eb560be5` refactor: #186 emby/jellyfin/plex 抽离为独立驱动子包
- `421558fd` refactor: #186 feiniu/fongmi 继承 BaseScheduler 与 BaseSyncResult
- `5c6ee94d` feat: 新增 BaseScheduler 和 BaseSyncResult 抽象基类
- `833bbde5` chore: #186 更改timezone设置

## 2026-07-13

### [feature: 支持fongmi定时同步](https://github.com/SanaeMio/Bangumi-syncer/pull/185)

- `c5e4eb8e` fix: #185 修改配置描述
- `7a0ea3f8` fix: 同步格式检查
- `62757991` feature: 支持fongmi定时同步

## 2026-07-08

### [perf: 优化封面加载机制，减少首页等待时间](https://github.com/SanaeMio/Bangumi-syncer/pull/184)

- `fb17a7a1` perf: 优化封面加载机制，减少首页等待时间

## 未关联 PR 的直接提交

- `1b079d1` docs(notification): 修正事件专属字段表与模板路径，并补测试防再脱节 `2026-10-12`
- `dc37e09` merge: 合入 upstream/main 最新代码（summary 服务冲突解决） `2026-09-14`
- `87bb88f` merge: 合并远程 main（日志 stdlib 兼容、追番总结通知修复） `2026-08-16`
- `a1e16b8` fix: 更新公告镜像站域名 `2026-07-08`
