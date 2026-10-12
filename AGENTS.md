# AGENTS.md

面向 AI 编码助手与本仓库协作者的快速上下文（人类贡献流程仍以 [README.md](https://github.com/SanaeMio/Bangumi-syncer/blob/main/README.md) 与 [CONTRIBUTING.md](https://github.com/SanaeMio/Bangumi-syncer/blob/main/CONTRIBUTING.md) 为准）。

## 项目概述

Bangumi-syncer 将常见媒体库（Plex、Emby、Jellyfin、Trakt、飞牛等）的观看进度同步到 [Bangumi（番组计划）](https://bgm.tv/) 官方 API。提供基于 **FastAPI** 的 Web 管理与同步接口，默认本地访问 `http://localhost:8000`。

## 技术栈与环境

- **Python**：`>=3.10`（见 [pyproject.toml](https://github.com/SanaeMio/Bangumi-syncer/blob/main/pyproject.toml) 中 `requires-python`）。
- **运行时**：FastAPI、Uvicorn、Jinja2、Pydantic、APScheduler 等（依赖见 `pyproject.toml`）。
- **包管理**：推荐 [uv](https://docs.astral.sh/uv/)。

## 仓库地图

| 路径 | 说明 |
| --- | --- |
| `app/` | 应用代码：`api/` 路由、`services/` 业务与调度、`core/` 配置与基础设施、`models/`、`utils/` |
| `app/main.py` | FastAPI 应用入口，`uvicorn app.main:app` |
| `tests/` | 单元测试与 API 测试 |
| `docs/` | 用户文档（VitePress），配图在 `docs/public/images/` |
| `templates/`、`static/` | Jinja 模板与静态资源 |
| `Dockerfile`、`entrypoint.sh` | 容器构建与启动 |
| `.github/workflows/` | CI：如 `lint.yml`、`ci-tests.yml`、`changelog.yml`、Docker 相关工作流、`docs.yml` |

## 安装、构建与常用命令

在项目根目录执行：

```bash
uv sync --group dev
```

```bash
# 代码风格与静态检查（CI 中 lint 工作流使用 ruff format --check）
uv run ruff check .
uv run ruff format .

# 仅当修改了 Jinja 模板时
uv run djlint templates/ --reformat

# 单元测试与覆盖率
uv run pytest tests/ --cov=app --cov-report=term
```

**仅当修改了 `pyproject.toml` 中的运行时依赖时**：在 `uv lock` 之后执行下面命令生成根目录 `requirements.txt` 并一并提交，避免与 README、用户文档里的 `pip install -r requirements.txt` 不同步。

```bash
uv export --format requirements.txt --no-dev -o requirements.txt
```

本地启动 Web 服务（等价于仓库内 `start.bat` / 镜像内 uvicorn 目标模块）：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

更完整的说明（Fork、PR、Docker 集成测试路径等）见 [CONTRIBUTING.md](https://github.com/SanaeMio/Bangumi-syncer/blob/main/CONTRIBUTING.md)。

## 测试说明

- 行为或逻辑变更应**尽量附带或更新** `tests/` 下相关用例；难以覆盖时请在 PR 中说明，并优先用 Mock 等保持稳定。
- CI：`ci-tests` 工作流运行 `pytest tests/` 并上传覆盖率；`lint` 工作流负责 Ruff；模板由 djLint 单独检查。
- 若改动 **Dockerfile、entrypoint、镜像内权限或启动方式**，请关注 CONTRIBUTING 中提到的集成脚本 `tests/integration/test_docker_perms.sh` 及 Docker 相关 workflow。

## 新增配置项（强制三件套）

新增任何配置段或配置键时，**必须**同时完成以下三件事；漏掉任一项，`tests/test_config_schema.py::TestConfigCoverage` 会在 CI 失败。

1. **`config.example.ini`** —— 写入段与键，并用注释说明取值含义与默认值（这是用户对照修改的契约）。
2. **`docs/`** —— 在用户文档里出现该键名。绝大多数配置写在 [`docs/config/configuration.md`](https://github.com/SanaeMio/Bangumi-syncer/blob/main/docs/config/configuration.md)；有独立页面的功能写进对应页面（如 `bangumi-archive.md` / `bangumi-replay.md` / `notification-configuration.md`）。**面向普通用户，避免技术术语**。
3. **配置页** —— 在 `app/core/config_schema.py` 注册 `SectionMeta`，并在 `templates/config/` 提供表单字段（`name="段名.键名"`，段名用下划线）。

做不到第 3 项时，**必须显式隐藏并说明原因**（不允许出现「文档不提、界面没有」的隐藏配置项）：

- 整段不做配置页 → `visible_in_ui=False` + `hidden_reason="在哪里配置"`（例如另有独立页面 / 弹窗 / 仅手改）。
- 段可见但个别键不做入口（自动生成的密钥、只读展示项、仅供排障的参数）→ 在 `SectionMeta.manual_keys` 里逐键写明原因。

其他约定：

- `SectionMeta.fields` 里登记的默认值必须与后端实际读取的兜底值一致（如 `arbiter.DEFAULT_*`），否则「界面显示的」和「实际生效的」会出现两条口径。
- 布尔字段按需选 `default_true`（未设置视为开）或 `loose_true`（兼容字符串 `'true'`），不要只靠注释说明。

## 文档不得与代码脱节（强制）

文档里**声称是程序真实产出**的内容必须可被验证。历史教训：`docs/config/notification-configuration.md` 的「实际发出去的内容」示例曾长期写着 `"episode": "S00E00"`，而在代码把无集数类型的 `ep_label` 改为空串后，该示例**没有任何东西能发现它已过期**；同一页还有「事件专属字段」表把某个类型算作会发它其实不发的字段、以及三个有专属字段的类型整行缺失。

### 写「实际输出」示例时的三条规则

1. **能从源文件引用就不要手抄。**
   若示例就是某个文件的完整内容（如默认模板），用 VitePress snippet 直接引用，不要复制：

   ```markdown
   <<< @/../templates/notifications/webhook/default.json
   ```

   注意路径以 `docs/` 为根（`@/` = `docs/`），`../` 才是仓库根。文件被改名/删除时 **docs 构建会直接失败（ENOENT）**，这正是想要的：构建失败好过静默过期。当前已用于 `notification-configuration.md` 的默认 Webhook 模板。

2. **加工过的示例（无法引用源文件）必须配断言。**
   在 `tests/` 里调用真实渲染路径，把文档里的代码块解析出来逐字段比对。参考 `tests/utils/test_notification_titles.py::TestDocsExampleMatchesRealOutput`——它直接解析文档中的 JSON 与 `render_webhook_payload()` 的真实输出比较。

3. **纯示意性内容必须写明「示意」。**
   如果示例是简化过的、不打算与代码逐字一致，就不要用「实际发出去的」「真实输出」这类承诺性措辞。

### 表格与清单同样要断言

文档里的**字段表、类型清单、枚举**属于可机检内容，应写断言比对源头（如注册表）。参考 `TestDocsEventFieldTableMatchesRegistry`：它解析文档表格并与 `notification_registry` 的 `payload_fields` 双向核对——既防「表里写了不存在的字段」，也防「有字段的类型整行漏掉」。

判断某条文档声明能否机检的方法：**问「有没有一个函数/注册表/接口的真实返回值可以和它比对」**。有就写断言，没有就按第 3 条写明「示意」。

### 提交前：核实领先远程的提交是否改动了文档行为

**当本地领先 `origin` 的提交中包含 `docs/` 变更时，推送前必须逐条核实这些文档描述是否仍与代码实际行为相符**，而不是只看 diff 是否「看起来对」：

1. 列出领先的提交：`git log --oneline origin/<branch>..HEAD`
2. 挑出其中改动 `docs/**`、`templates/**` 或用户可见行为的提交
3. 对每处新增/修改的示例、表格、默认值，**到代码里找到产出它的那一行**确认（不要依赖记忆或上下文里的旧结论）
4. 能引用源文件的改引用；加工过的补断言；简化示意的标注「示意」

这条针对的正是「文档与代码在同一批提交里一起改，改完没人再核对」的场景——单一提交里看不出问题，等到下一个 PR 才暴露。

## 更新日志（半自动，勿手改生成区）

`docs/changelog.md` 分两段，来源不同：

| 段落 | 来源 | 能否手改 |
| --- | --- | --- |
| `# 版本亮点` | `docs/changelog-highlights.md`（人工维护） | ✅ 手改这个文件 |
| `# 提交明细` | `scripts/gen_changelog.py` 由 git 历史生成 | ❌ 改了会被下次生成覆盖 |

**要补内容时改哪里**：

- 想写「实测数据、设计取舍、升级注意、破坏性变更」这类**提交信息里推不出来**的东西
  → 写进 `docs/changelog-highlights.md`。
- 其余（哪个 PR 改了哪些提交）→ 不用管，CI 自动生成。

**生成规则**：合并进 `main` 后，`.github/workflows/changelog.yml` 自动运行生成器并
开一个 PR（分支 `changelog/auto`）。本地想预览：

```bash
python scripts/gen_changelog.py            # 写入 docs/changelog.md
python scripts/gen_changelog.py --stdout   # 只打印
```

**踩过的三个坑**（已由 `tests/test_gen_changelog.py` 锁定，改生成器前先读）：

1. **去重**：PR 内的提交既出现在合并提交的父链上、又会被 `git log` 当普通提交遍历到。
   不去重会让同一提交既列在 PR 下又在「直接提交」段重复（实测 638 条里 634 条是重复）。
2. **HTML 转义**：提交信息里的 `</div>`、`<`、`>` 会被 Vue 编译器当成未闭合标签，
   让 `npm run docs:build` 直接失败。输出一律转成实体。
3. **取最新 tag 不能用 `git describe`**：仓库里有 `backup/*` 这类非版本 tag，
   其时间可能晚于最新 `v*` tag（实测 `backup/pre-distill-refactor-matching-pipeline`
   比 `v3.11.3` 新），必须 `git tag -l "v*" --sort=-v:refname`。

另外：起始提交不存在时生成器会**报错退出**而不是写空文件 —— 否则一次笔误就会把
变更日志清空。

## 代码风格与架构约定

- **风格**：以 [pyproject.toml](https://github.com/SanaeMio/Bangumi-syncer/blob/main/pyproject.toml) 中 **Ruff**、**djlint** 配置为准，勿在本文重复粘贴规则全文。
- **分层**：新 HTTP 接口放在 `app/api/`；复杂业务放在 `app/services/`（可参考现有 `sync_service`、`mapping_service` 及各媒体子包）。体量小的只读端点可参考 [`app/api/health.py`](https://github.com/SanaeMio/Bangumi-syncer/blob/main/app/api/health.py) 的组织方式。
- **文档**：配置项或面向用户的行为变更需同步更新 `docs/` 中对应 Markdown；图片放在 `docs/public/images/`，文内用根路径如 `![](/images/overview/xxx.png)`（见 CONTRIBUTING）。
- **协作**：与邻近文件保持一致的命名与注释习惯；避免无关大范围格式化或重命名。

## 安全与敏感信息

勿将 Bangumi Token、密码、私钥等**写入仓库**或提交到 Git。运行时密钥通过应用配置与环境管理；细节见在线文档与 CONTRIBUTING。

## PR 与提交前自检

推送或打开 PR 前建议至少执行上文 **Ruff + pytest**（若改模板则加 **djlint**）。**若改运行时依赖**，在 `uv lock` 后按上文单独一节执行 **`uv export` 并提交 `requirements.txt`**。单个 PR 尽量聚焦单一目的，便于审查与回滚。

**若本次领先远程的提交里有 `docs/` 变更**，按上文[「文档不得与代码脱节」](#文档不得与代码脱节强制)核实过再推；改动 `templates/notifications/**` 时同样跑一次 `npm run docs:build`（该目录已被文档 snippet 引用）。