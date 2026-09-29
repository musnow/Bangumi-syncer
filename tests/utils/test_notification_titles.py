"""标题模板回归测试（含 H1：per-type 标题信息不得丢失）

背景：删除 html_builders.py 时，旧实现的 per-type 邮件主题/标题（形如
「同步成功 - {title} S01E02」）一度退化为只有「✅ 同步成功」，导致同一类型
的多条通知无法区分。现由注册表 NotificationTypeMeta.title_template 恢复，
并由 NotificationService 在 {ep_label} 就位后渲染。

本文件钉死这些 per-type 标题，防止再次静默丢失。
"""

import pytest

from app.core.notification_registry import get_type_meta
from app.services.notification_service import NotificationService
from app.utils.notifier.channels_impl import EmailChannel, WebhookChannel

ITEM = {
    "title": "葬送的芙莉莲",
    "season": 1,
    "episode": 2,
    "user_name": "tester",
    "source": "plex",
}


@pytest.fixture
def svc():
    return NotificationService()


@pytest.fixture
def webhook():
    return WebhookChannel("notify-webhook-1", {"url": "https://x", "enabled": True})


@pytest.fixture
def email():
    return EmailChannel(
        "notify-email-1",
        {"smtp_server": "s", "email_to": "d@e.com", "enabled": True},
    )


# ─────────────────────────────────────────────────────────────────────────
# H1：per-type 标题必须带番剧/集数
# ─────────────────────────────────────────────────────────────────────────


class TestPerTypeTitlesRestored:
    @pytest.mark.parametrize(
        "notification_type,expected",
        [
            ("mark_success", "✅ 同步成功 - 葬送的芙莉莲 S01E02"),
            ("mark_failed", "❌ 同步失败 - 葬送的芙莉莲 S01E02"),
            ("mark_skipped", "⏭️ 已看过 - 葬送的芙莉莲 S01E02"),
            ("request_received", "📥 收到同步请求 - 葬送的芙莉莲 S01E02"),
            ("episode_not_found", "📺 未找到剧集 - 葬送的芙莉莲 S01E02"),
            ("pending_candidate", "📝 候选待确认 - 葬送的芙莉莲 S01E02"),
            ("bangumi_id_found", "🔍 匹配到番剧 - 葬送的芙莉莲"),
            ("anime_not_found", "🔍 未找到番剧 - 葬送的芙莉莲"),
        ],
    )
    def test_title_contains_anime(self, svc, webhook, notification_type, expected):
        rendered = svc._render_for_channel(webhook, notification_type, ITEM)
        assert rendered["payload"]["title"] == expected

    def test_watching_summary_title_has_job_name(self, svc, webhook):
        rendered = svc._render_for_channel(
            webhook,
            "watching_summary_每日总结",
            {"job_name": "每日总结", "summary_text": "正文"},
        )
        assert rendered["payload"]["title"] == "📊 追番总结 - 每日总结"

    def test_email_subject_matches_title(self, svc, webhook, email):
        """邮件主题与 webhook 标题同源，避免两处不一致"""
        for t in ("mark_success", "mark_failed", "pending_candidate"):
            w = svc._render_for_channel(webhook, t, ITEM)
            e = svc._render_for_channel(email, t, ITEM)
            assert e["subject"] == w["payload"]["title"]

    def test_types_without_title_template_use_display_name(self, svc, webhook):
        """未声明 title_template 的类型回退为「图标 + 展示名」"""
        rendered = svc._render_for_channel(
            webhook, "config_error", {"error_message": "e"}
        )
        assert rendered["payload"]["title"] == "⚙️ 配置错误"


class TestEpisodeLabel:
    def test_two_digit_padding(self, svc, webhook):
        """集数补零，保持与旧实现 S01E02 一致"""
        r = svc._render_for_channel(
            webhook, "mark_success", {"title": "T", "season": 1, "episode": 2}
        )
        assert r["payload"]["episode"] == "S01E02"

    def test_large_numbers_not_truncated(self, svc, webhook):
        r = svc._render_for_channel(
            webhook, "mark_success", {"title": "T", "season": 12, "episode": 25}
        )
        assert r["payload"]["episode"] == "S12E25"

    def test_movie_uses_special_label(self, svc, webhook):
        r = svc._render_for_channel(
            webhook, "mark_success", {"title": "T", "media_type": "movie"}
        )
        assert r["payload"]["episode"] == "剧场版"

    def test_missing_season_episode_does_not_crash(self, svc, webhook):
        r = svc._render_for_channel(webhook, "mark_success", {"title": "T"})
        assert r["payload"]["episode"] == "S00E00"

    def test_existing_ep_label_preserved(self, svc, webhook):
        """调用方已显式给出 ep_label 时不应被覆盖"""
        r = svc._render_for_channel(
            webhook, "mark_success", {"title": "T", "ep_label": "自定义标签"}
        )
        assert r["payload"]["episode"] == "自定义标签"
        assert "自定义标签" in r["payload"]["title"]


class TestTitleTemplateMechanism:
    def test_all_item_level_types_have_titles(self):
        """条目级类型的标题必须能区分具体条目（即含 {title}）"""
        from app.core.notification_registry import all_types

        missing = [
            m.id
            for m in all_types()
            if m.is_item_level and "{title}" not in (m.title_template or "")
        ]
        assert missing == [], f"这些条目级类型标题缺 title 占位符: {missing}"

    def test_default_title_uses_icon(self):
        meta = get_type_meta("mark_success")
        assert meta.default_title().startswith("✅ ")

    def test_unknown_type_falls_back(self, svc, webhook):
        r = svc._render_for_channel(webhook, "no_such_type", {"title": "T"})
        assert r["payload"]["title"] == "T"
