"""docs/changelog.md 生成器（scripts/gen_changelog.py）的回归测试。

这三个断言都对应实测踩到的坑，不是假设出来的：
1. PR 内的提交被重复列出（638 条里 634 条是重复）；
2. 提交信息里的 `</div>` 之类 HTML 片段让 docs 构建直接失败；
3. 仓库里存在时间晚于最新版本 tag 的 `backup/*` 标签，用 `git describe`
   会取错起点。
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = REPO_ROOT / "docs" / "changelog.md"


def _load_module():
    """按路径加载 scripts/gen_changelog.py（scripts/ 不是包）。"""
    spec = importlib.util.spec_from_file_location(
        "gen_changelog", REPO_ROOT / "scripts" / "gen_changelog.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_changelog"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen():
    return _load_module()


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    ).stdout.strip()


class TestTagDetection:
    def test_picks_version_tag_not_backup_tag(self, gen):
        """最新起点必须是 v* 版本 tag。

        仓库里存在 `backup/pre-distill-refactor-matching-pipeline`
        （2026-09-09），其时间晚于 v3.11.3（2026-07-07）。若按时间排序或
        用 `git describe`，会把它当成起点，算出的范围完全错误。
        """
        tag = gen.latest_version_tag()
        assert tag, "没有任何 v* tag，生成器会直接报错退出"
        assert tag.startswith("v"), f"取到了非版本 tag: {tag}"
        assert tag == _git("tag", "-l", "v*", "--sort=-v:refname").splitlines()[0]


class TestNoDuplicateCommits:
    def test_pr_commits_not_repeated_in_direct_section(self, gen):
        """同一个提交不能既列在 PR 下、又出现在「直接提交」段。"""
        base = gen.latest_version_tag()
        prs, direct = gen.collect(f"{base}..HEAD")

        pr_short_shas = {short for pr in prs for short, _ in pr.commits}
        direct_short_shas = {c.short_sha for c in direct}

        overlap = pr_short_shas & direct_short_shas
        assert not overlap, (
            f"以下提交同时出现在 PR 列表和「直接提交」段（重复计数）: "
            f"{sorted(overlap)[:10]}"
        )

    def test_direct_section_is_small(self, gen):
        """游离提交应当很少。

        实测：修复前去重逻辑缺失时有 638 条（其中 634 条是重复）。
        这里给出宽松上限，防止去重逻辑再次失效。
        """
        base = gen.latest_version_tag()
        prs, direct = gen.collect(f"{base}..HEAD")
        assert len(direct) < 50, (
            f"「直接提交」有 {len(direct)} 条，疑似未剔除属于 PR 的提交"
        )


class TestHtmlEscaping:
    def _generated_body(self, gen) -> str:
        """只取生成器产出的部分（提交明细），排除人工维护的亮点正文。

        亮点正文由人手写，可以正常使用 ``<channel>`` 这类写法（它在行内的
        反引号代码里是安全的），因此不该套用「不得出现裸尖括号」这条限制。
        """
        base = gen.latest_version_tag()
        prs, direct = gen.collect(f"{base}..HEAD")
        content = gen.render(prs, direct, base, len(prs))
        marker = "# 提交明细"
        return content.split(marker, 1)[1] if marker in content else content

    def test_no_raw_angle_brackets_in_generated_body(self, gen):
        """生成器产出的内容里不能有裸 `<` / `>`。

        提交信息里有 `修复 _bangumi_archive.html 多余 </div>`，未转义会被
        Vue 编译器当成未闭合标签，`npm run docs:build` 报
        "Element is missing end tag" 而整站构建失败。
        """
        body = self._generated_body(gen)
        offenders = [line for line in body.splitlines() if "<" in line or ">" in line]
        assert not offenders, (
            "以下行含未转义的尖括号，会让 docs 构建失败:\n" + "\n".join(offenders[:5])
        )

    def test_real_html_fragment_is_escaped(self, gen):
        """实测用例：带 `</div>` 的真实历史提交必须被转义后输出。"""
        body = self._generated_body(gen)
        assert "&lt;/div&gt;" in body, (
            "历史提交「_bangumi_archive.html 多余 </div>」应转义为 &lt;/div&gt;"
        )

    def test_escape_md_converts_angle_brackets(self, gen):
        assert gen.escape_md("</div>") == "&lt;/div&gt;"
        assert gen.escape_md("season>1") == "season&gt;1"


class TestCleanInvisibleChars:
    def test_strips_bom_and_zero_width(self, gen):
        """提交信息开头的 BOM 必须清掉。

        PowerShell 的 `Out-File -Encoding utf8` 配合 `git commit -F` 会写入
        BOM，实测 722 个提交里有 9 个带 BOM，不清理会在文档里显示为脏字符。
        """
        assert gen.clean("\ufeffdocs(x): y") == "docs(x): y"
        assert gen.clean("\u200bfoo\u200b") == "foo"
        assert gen.clean("  正常标题  ") == "正常标题"


class TestInvalidBaseFails:
    def test_nonexistent_base_returns_nonzero(self, gen, tmp_path):
        """起始提交不存在时必须报错退出，而不是把 changelog 清空。

        生成器直接写 docs/changelog.md；若 `git log` 因 revision 无效而返回
        空输出并被当成「没有新提交」，CI 会把变更日志覆盖成空文档。
        """
        original = gen.OUTPUT
        target = tmp_path / "changelog.md"
        target.write_text("原有内容\n", encoding="utf-8")
        gen.OUTPUT = target
        try:
            sys.argv = ["gen_changelog.py", "vDOES_NOT_EXIST_12345"]
            code = gen.main()
        finally:
            gen.OUTPUT = original
            sys.argv = sys.argv[:1]

        assert code != 0, "无效的起始提交必须返回非 0"
        assert target.read_text(encoding="utf-8") == "原有内容\n", (
            "起始提交无效时不得改写文件"
        )


class TestGeneratedFileIsCurrent:
    def test_changelog_matches_generator_output(self, gen):
        """已提交的 docs/changelog.md 应与生成器输出一致。

        防止手工编辑（文件头已声明「请勿手工编辑」）或忘记重新生成。
        若此测试失败，运行 `python scripts/gen_changelog.py` 后提交即可。
        """
        base = gen.latest_version_tag()
        prs, direct = gen.collect(f"{base}..HEAD")
        expected = gen.render(prs, direct, base, len(prs))
        actual = CHANGELOG.read_text(encoding="utf-8")
        assert actual == expected, (
            "docs/changelog.md 与生成器输出不一致；"
            "请运行 `python scripts/gen_changelog.py` 重新生成"
        )
