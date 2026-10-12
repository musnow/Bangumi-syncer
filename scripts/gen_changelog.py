#!/usr/bin/env python3
"""从 git 历史生成 docs/changelog.md。

由 CI 在合并进 main 后自动运行（见 .github/workflows/changelog.yml），
也可本地手动执行。

生成内容按日期倒序分组，每个 PR 一条：PR 标题（链接到 GitHub）+ 该 PR 内的
提交清单。非 PR 的直接提交单独成段。

用法：
    python scripts/gen_changelog.py                 # 自上一个 v* tag 起
    python scripts/gen_changelog.py v3.11.3         # 自指定 tag 起
    python scripts/gen_changelog.py --stdout        # 打印而不写文件
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT = REPO_ROOT / "docs" / "changelog.md"
# 人工维护的版本亮点（实测数据、设计取舍、升级注意）。这些内容从 git 提交
# 信息里推不出来，因此单独存放；生成器只读取并原样带上，绝不覆盖。
HIGHLIGHTS = REPO_ROOT / "docs" / "changelog-highlights.md"
REPO_URL = "https://github.com/SanaeMio/Bangumi-syncer"
COMMITS_URL = f"{REPO_URL}/commits/main"

MERGE_PR_RE = re.compile(r"^Merge pull request #(\d+) from (\S+)")

# git 输出用 \x1f 分隔字段、\x1e 分隔记录，避免提交正文里的换行干扰解析
RECORD_SEP = "\x1e"
FIELD_SEP = "\x1f"

# 提交信息开头可能残留 BOM / 零宽字符（用编辑器或 `git commit -F` 带 BOM 的
# 文件提交时会混入），不清理会在文档里变成看不见的脏字符
_INVISIBLE = "\ufeff\u200b\u200c\u200d\xa0"


def clean(text: str) -> str:
    """去掉首尾不可见字符与多余空白。"""
    return text.strip().strip(_INVISIBLE).strip()


def escape_md(text: str) -> str:
    """转义会破坏 VitePress/Markdown 渲染的字符。

    提交信息里常出现 HTML 片段（如 `</div>`）或 `<`、`>`，Vue 编译器会把它们
    当成未闭合标签，导致 `npm run docs:build` 直接失败（实测一条
    「_bangumi_archive.html 多余 </div>」就会让整站构建报
    "Element is missing end tag"）。这里统一转成实体。
    """
    return text.replace("<", "&lt;").replace(">", "&gt;")


def git(*args: str) -> str:
    """执行 git 命令并返回 stdout；失败时返回空串。"""
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        print(
            f"[warn] git {' '.join(args)} 失败: {result.stderr.strip()}",
            file=sys.stderr,
        )
        return ""
    return result.stdout


def latest_version_tag() -> str:
    """最近的一个 v* tag（按版本号排序，不是按时间）。

    注意：仓库里还有 `backup/*` 之类非版本 tag，且其时间可能晚于最新版本
    tag，所以必须用 `-l "v*"` 过滤并按版本号排序，不能用 `git describe`。
    """
    out = git("tag", "-l", "v*", "--sort=-v:refname")
    tags = [t.strip() for t in out.splitlines() if t.strip()]
    return tags[0] if tags else ""


@dataclass
class PullRequest:
    number: int
    merge_sha: str
    date: str
    body: str = ""
    commits: list[tuple[str, str]] = field(default_factory=list)

    @property
    def url(self) -> str:
        return f"{REPO_URL}/pull/{self.number}"

    @property
    def title(self) -> str:
        """PR 标题。

        GitHub 生成的合并提交会把 PR 标题写进正文首行，优先用它；
        取不到时退回该 PR 的第一个子提交标题。
        """
        if self.body:
            first = clean(self.body.splitlines()[0])
            if first:
                return first
        if self.commits:
            return self.commits[0][1]
        return f"Pull request #{self.number}"


@dataclass
class DirectCommit:
    full_sha: str
    short_sha: str
    date: str
    subject: str


def collect(rev_range: str) -> tuple[list[PullRequest], list[DirectCommit]]:
    """遍历 rev_range，拆出 PR 与真正游离的直接提交。"""
    fmt = f"%H{FIELD_SEP}%P{FIELD_SEP}%ad{FIELD_SEP}%s{FIELD_SEP}%b{RECORD_SEP}"
    raw = git("log", f"--pretty=format:{fmt}", "--date=short", rev_range)

    prs: list[PullRequest] = []
    direct: list[DirectCommit] = []

    for record in raw.split(RECORD_SEP):
        record = record.strip("\n")
        if not record:
            continue
        parts = record.split(FIELD_SEP)
        if len(parts) < 5:
            continue
        sha, parents, date, subject, body = (
            parts[0],
            parts[1],
            parts[2],
            parts[3],
            parts[4],
        )
        subject = clean(subject)

        match = MERGE_PR_RE.match(subject)
        # 只把真正的合并提交（两个父提交）当作 PR，避免误判被回退的合并
        if match and len(parents.split()) == 2:
            prs.append(
                PullRequest(
                    number=int(match.group(1)),
                    merge_sha=sha,
                    date=date,
                    body=clean(body),
                )
            )
        elif not subject.startswith("Merge "):
            direct.append(
                DirectCommit(
                    full_sha=sha, short_sha=sha[:7], date=date, subject=subject
                )
            )

    # 收集所有 PR 覆盖的提交，稍后从 direct 里剔除。
    # 合并进 PR 的提交在 `git log` 里既会出现在 PR 的第二个父提交链上，
    # 也会作为普通提交被遍历到；不去重会让同一个提交既列在 PR 下、
    # 又出现在「直接提交」段（实测 638 条里 634 条是重复）。
    covered: set[str] = set()
    for pr in prs:
        # 合并提交的第一个父提交是主干，第二个父提交带 PR 全部内容
        sub = git(
            "log",
            "--no-merges",
            f"--pretty=format:%H{FIELD_SEP}%h{FIELD_SEP}%s",
            f"{pr.merge_sha}^1..{pr.merge_sha}",
        )
        for line in sub.splitlines():
            line = line.strip()
            if FIELD_SEP not in line:
                continue
            fields = line.split(FIELD_SEP)
            if len(fields) < 3:
                continue
            full_sha, short, subj = fields[0], fields[1], fields[2]
            subj = clean(subj)
            covered.add(full_sha)
            if subj:
                pr.commits.append((short.strip(), subj))

    # 真正游离的提交：不属于任何 PR
    direct = [c for c in direct if c.full_sha not in covered]

    return prs, direct


def read_highlights() -> str:
    """读取人工维护的版本亮点。

    文件用 `# 版本亮点（人工维护）` 作标题，这里剥掉该标题与紧随其后的
    引言块，只取正文（正文自身以 `## ` 开头），避免在页面上出现两级标题。
    """
    if not HIGHLIGHTS.exists():
        return ""
    raw = HIGHLIGHTS.read_text(encoding="utf-8").strip()
    lines = raw.splitlines()
    # 丢弃文件自身的 H1 及其后的引言（`>` 引用块），保留第一个 `## ` 起的正文
    for index, line in enumerate(lines):
        if line.startswith("## "):
            return "\n".join(lines[index:]).strip()
    return ""


def render(
    prs: list[PullRequest], direct: list[DirectCommit], start: str, pr_count: int
) -> str:
    """渲染成 Markdown。"""
    lines: list[str] = [
        "---",
        "title: 📝 更新日志",
        "order: 45",
        "---",
        "",
        "# Changes",
        "",
        f"本页由 git 历史自动生成，收录自 `{start}` 以来的 {pr_count} 个 PR"
        f"（最近更新 {prs[0].date if prs else '-'}）。",
        f"完整提交历史见 [GitHub Commits]({COMMITS_URL})。",
        "",
        "::: tip 关于本页",
        "「版本亮点」由人工维护（`docs/changelog-highlights.md`），收录实测数据、"
        "设计取舍与升级注意事项；「提交明细」由 `.github/workflows/changelog.yml` "
        "在合并进 `main` 后自动生成，**请勿手工编辑本页的提交明细部分**"
        "—— 下次生成会覆盖。",
        "如需修正条目措辞，请修改对应的提交信息或 PR 标题。",
        ":::",
        "",
    ]

    highlights = read_highlights()
    if highlights:
        lines.append("# 版本亮点")
        lines.append("")
        lines.append(highlights)
        lines.append("")
        lines.append("# 提交明细")
        lines.append("")

    by_date: dict[str, list[PullRequest]] = {}
    for pr in prs:
        by_date.setdefault(pr.date, []).append(pr)

    for date in sorted(by_date, reverse=True):
        lines.append(f"## {date}")
        lines.append("")
        for pr in by_date[date]:
            lines.append(f"### [{escape_md(pr.title)}]({pr.url})")
            lines.append("")
            if pr.commits:
                for short, subject in pr.commits:
                    lines.append(f"- `{short}` {escape_md(subject)}")
            else:
                lines.append("- _（无独立提交，squash 合并）_")
            lines.append("")

    if direct:
        lines.append("## 未关联 PR 的直接提交")
        lines.append("")
        for commit in direct:
            lines.append(
                f"- `{commit.short_sha}` {escape_md(commit.subject)} `{commit.date}`"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="从 git 历史生成 docs/changelog.md")
    parser.add_argument(
        "base",
        nargs="?",
        help="起始 tag/提交（默认自动取最近的 v* tag）",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="只打印到标准输出，不写文件",
    )
    args = parser.parse_args()

    base = args.base or latest_version_tag()
    if not base:
        print("[error] 找不到任何 v* tag，请显式指定起始提交", file=sys.stderr)
        return 1

    # 先确认 base 确实存在。否则 `git log` 会失败并返回空输出，脚本会把
    # 变更日志覆盖成一份空文档 —— 宁可报错退出，也不要静默清空。
    verify = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if verify.returncode != 0:
        print(f"[error] 起始提交不存在: {base}", file=sys.stderr)
        return 1

    rev_range = f"{base}..HEAD"
    prs, direct = collect(rev_range)
    if not prs and not direct:
        print(f"[info] {rev_range} 没有任何新提交，changelog 保持原样")
        return 0

    total_prs = len(prs)
    content = render(prs, direct, base, total_prs)

    if args.stdout:
        sys.stdout.write(content)
        return 0

    OUTPUT.write_text(content, encoding="utf-8")
    print(
        f"[ok] 已写入 {OUTPUT.relative_to(REPO_ROOT)}："
        f"{total_prs} 个 PR、{len(direct)} 个直接提交（自 {base} 起）"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
