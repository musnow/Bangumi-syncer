"""NotificationTemplateManager 的类型专属字段渲染测试

覆盖 Issue #245 暴露的问题：使用通用默认模板时，追番总结等类型的
专属内容（总结正文）会被丢弃。
"""

from app.utils.notifier.template_manager import NotificationTemplateManager

# ─────────────────────────────────────────────────────────────────────────
# 辅助
# ─────────────────────────────────────────────────────────────────────────


def _summary_data(**overrides):
    data = {
        "notification_type": "watching_summary_每日总结",
        "type_display_name": "追番总结",
        "type_icon": "📊",
        "timestamp": "2026-01-01 00:00:00",
        "user_name": "tester",
        "title": "unknown",
        "season": 0,
        "episode": 0,
        "source": "summary",
        "job_name": "每日总结",
        "summary_text": "本周看了 3 部番，共 12 集。",
        "date_range": "2026-01-01 ~ 2026-01-07",
        "record_count": 12,
        "model": "deepseek-chat",
        "tokens_used": 3456,
    }
    data.update(overrides)
    return data


def _manager(tmp_path):
    """使用仓库内置模板目录的管理器"""
    return NotificationTemplateManager(default_dir=None, custom_dir=tmp_path)


# ─────────────────────────────────────────────────────────────────────────
# type_fields
# ─────────────────────────────────────────────────────────────────────────


class TestTypeFields:
    def test_watching_summary_includes_summary(self):
        fields = NotificationTemplateManager.type_fields(_summary_data())
        assert fields["summary"] == "本周看了 3 部番，共 12 集。"
        assert fields["job_name"] == "每日总结"
        assert fields["record_count"] == 12

    def test_missing_values_are_dropped(self):
        """缺失或空的字段不应出现，避免模板输出空键"""
        data = _summary_data()
        data.pop("model")
        data["date_range"] = ""
        fields = NotificationTemplateManager.type_fields(data)
        assert "model" not in fields
        assert "date_range" not in fields

    def test_unknown_type_returns_empty(self):
        assert (
            NotificationTemplateManager.type_fields(
                {"notification_type": "no_such_type"}
            )
            == {}
        )

    def test_missing_notification_type_returns_empty(self):
        assert NotificationTemplateManager.type_fields({}) == {}

    def test_type_without_fields_returns_empty(self):
        """request_received 未声明专属字段"""
        assert (
            NotificationTemplateManager.type_fields(
                {"notification_type": "request_received", "title": "x"}
            )
            == {}
        )


# ─────────────────────────────────────────────────────────────────────────
# render_webhook_payload
# ─────────────────────────────────────────────────────────────────────────


class TestRenderWebhookPayload:
    def test_default_template_gains_summary_field(self, tmp_path):
        """默认模板 + 追番总结 → payload 必须携带 summary"""
        payload = _manager(tmp_path).render_webhook_payload(_summary_data())
        assert payload["summary"] == "本周看了 3 部番，共 12 集。"
        assert payload["job_name"] == "每日总结"

    def test_default_template_drops_placeholder_sentinel(self, tmp_path):
        """模板中的 extra 哨兵不应以字面量泄漏到最终 payload"""
        payload = _manager(tmp_path).render_webhook_payload(_summary_data())
        assert "__type_fields__" not in payload.values()

    def test_default_template_keeps_common_fields(self, tmp_path):
        payload = _manager(tmp_path).render_webhook_payload(_summary_data())
        assert payload["type"] == "watching_summary_每日总结"
        assert payload["user"] == "tester"

    def test_mark_failed_gains_error_type(self, tmp_path):
        payload = _manager(tmp_path).render_webhook_payload(
            {
                "notification_type": "mark_failed",
                "type_display_name": "同步失败",
                "type_icon": "❌",
                "timestamp": "t",
                "user_name": "u",
                "title": "某番",
                "season": 1,
                "episode": 2,
                "source": "plex",
                "error_message": "boom",
                "error_type": "sync_error",
            }
        )
        assert payload["error"] == "boom"
        assert payload["error_type"] == "sync_error"
        # 不应混入追番总结的字段
        assert "summary" not in payload

    def test_unknown_type_does_not_raise(self, tmp_path):
        payload = _manager(tmp_path).render_webhook_payload(
            {"notification_type": "totally_unknown", "title": "x"}
        )
        assert isinstance(payload, dict)


# ─────────────────────────────────────────────────────────────────────────
# merge_type_fields
# ─────────────────────────────────────────────────────────────────────────


class TestMergeTypeFields:
    def test_merges_into_plain_payload(self, tmp_path):
        """用户自定义的裸模板也要能拿到类型专属字段"""
        merged = _manager(tmp_path).merge_type_fields(
            {"content": "📢 {title}"}, _summary_data()
        )
        assert merged["summary"] == "本周看了 3 部番，共 12 集。"
        assert merged["content"] == "📢 {title}"

    def test_expands_sentinel(self, tmp_path):
        merged = _manager(tmp_path).merge_type_fields(
            {"extra": "__type_fields__"}, _summary_data()
        )
        assert "extra" not in merged
        assert merged["summary"] == "本周看了 3 部番，共 12 集。"

    def test_does_not_override_existing_key(self, tmp_path):
        """用户模板里已显式给出的键优先，不被自动字段覆盖"""
        merged = _manager(tmp_path).merge_type_fields(
            {"summary": "用户自己写的"}, _summary_data()
        )
        assert merged["summary"] == "用户自己写的"

    def test_non_dict_payload_passthrough(self, tmp_path):
        assert _manager(tmp_path).merge_type_fields("plain", _summary_data()) == "plain"
        assert _manager(tmp_path).merge_type_fields([1, 2], _summary_data()) == [1, 2]

    def test_no_fields_leaves_payload_untouched(self, tmp_path):
        payload = {"a": 1}
        merged = _manager(tmp_path).merge_type_fields(
            payload, {"notification_type": "request_received"}
        )
        assert merged == {"a": 1}
