# 版本亮点（人工维护）

> 本文件**手工维护**，用于记录从提交信息里看不出来的内容 ——
> 实测数据（如「精确率 95.9% → 99.0%」）、设计取舍、升级注意事项、破坏性变更。
>
> `docs/changelog.md` 由 `scripts/gen_changelog.py` 自动生成，会引用本文件；
> 生成器**不会覆盖**这里的内容。

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
