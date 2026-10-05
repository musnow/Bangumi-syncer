"""subject_id 有效性校验（共享实现）

原实现是 ``SyncService._validate_subject_id`` 的私有方法，只有「确认待确认
候选」一条路径会调用。结果是：映射管理页手动添加/编辑映射时**不做任何校验**，
用户可以写入书籍/音乐/游戏条目的 ID，直到真正同步时才失败 —— 而那时错误
信息离「写错了 ID」已经很远。

本模块把校验逻辑抽出为共享函数，供两条写入路径共用，避免再出现
「一处校验、另一处不校验」的分叉。
"""

from __future__ import annotations

from typing import Any

from ...core.logging import logger

#: Bangumi 条目类型：2=动画，6=三次元。同步只支持这两类。
SUBJECT_TYPE_ANIME = 2
SUBJECT_TYPE_REAL = 6


def _get_archive_shortcut():
    """延迟获取 archive 短路器

    刻意**不**在模块顶层 ``from ._archive_shortcut import archive_shortcut``：
    那样会把对象引用绑定到本模块，``patch`` 原模块属性将不再生效
    （测试里 ``patch("app.utils.bangumi_api._archive_shortcut.archive_shortcut")``
    会静默失效，导致用例互相污染）。每次经属性访问即可保持可打桩。
    """
    from . import _archive_shortcut

    return _archive_shortcut.archive_shortcut


def _get_accounts():
    """延迟导入账号模块

    账号层会 import 配置层，配置层在导入时即构建 ConfigManager 并打印启动
    信息；放在模块顶层会让本模块的导入带上这种副作用。测试中可用
    ``patch("...subject_validation._get_accounts")`` 替换。
    """
    from ...core import accounts

    return accounts


def _get_config_manager():
    """延迟导入配置管理器（原因同 ``_get_accounts``）"""
    from ...core.config import config_manager

    return config_manager


def _get_api_class():
    """延迟导入 BangumiApi

    它定义在包 ``__init__`` 中，而本模块是该包的子模块；顶层直接
    ``from . import BangumiApi`` 会形成循环导入。测试中可用
    ``patch("...subject_validation._get_api_class")`` 替换。
    """
    from . import BangumiApi

    return BangumiApi


def validate_subject_id(subject_id: Any) -> tuple[bool, str]:
    """校验 subject_id 是否有效：存在且类型为动画/三次元

    优先走 archive 短路（本地查询，<1ms），未命中降级到 Bangumi API。
    返回 ``(True, "")`` 或 ``(False, reason)``。

    校验失败场景：
    - subject_id 非数字
    - 条目不存在（API 404 或返回空）
    - 类型非动画/三次元（如书籍/音乐/游戏）

    **降级放行**（返回 True）的情形：无可用 Bangumi 账号、archive 与 API 均
    不可用。理由是「校验本身不应成为写入的阻塞项」—— 网络故障时把用户的
    编辑挡回去，比允许一个可能无效的 ID 更糟；无效 ID 会在同步时暴露。
    """
    try:
        sid = int(subject_id)
    except (TypeError, ValueError):
        return False, "ID 必须为纯数字"

    if sid <= 0:
        return False, "ID 必须为正整数"

    # 优先走 archive 短路（无网络开销）
    shortcut = _get_archive_shortcut()
    if shortcut.enabled:
        result = shortcut.try_get_subject(sid)
        if result.hit and isinstance(result.data, dict):
            stype = result.data.get("type")
            if stype in (SUBJECT_TYPE_ANIME, SUBJECT_TYPE_REAL):
                return True, ""
            return False, f"条目类型为 {stype}，仅支持动画/三次元"
        # archive 未命中或不完整：降级到 API

    # 降级到 API：DB 为唯一真相源，取首选账号；无首选则取首个可用账号
    accounts = _get_accounts()

    cfg = accounts.get_primary_bangumi_config() or None
    if cfg is None:
        configs = accounts.list_bangumi_configs()
        if not configs:
            # 无可用配置时降级放行（不阻塞用户，映射写入后再由同步流程校验）
            logger.warning(f"subject_id={sid} 校验跳过：无可用 Bangumi 配置，降级放行")
            return True, ""
        cfg = next(iter(configs.values()))

    dev_snapshot = _get_config_manager().get_dev_http_snapshot()
    api = _get_api_class()(
        username=cfg["username"],
        access_token=cfg["access_token"],
        private=cfg.get("private", False),
        http_proxy=dev_snapshot["script_proxy"],
        ssl_verify=dev_snapshot["ssl_verify"],
        bgm_api_proxy=dev_snapshot["bgm_api_proxy"],
        bgm_next_proxy=dev_snapshot["bgm_next_proxy"],
        ech_mode=dev_snapshot["ech_mode"],
    )
    try:
        data = api.get_subject(sid)
    except Exception as e:
        logger.warning(f"subject_id={sid} API 校验异常：{e}，降级放行")
        return True, ""
    finally:
        try:
            api.close()
        except Exception:  # noqa: BLE001 — 关闭失败不影响校验结论
            pass

    if not isinstance(data, dict) or not data:
        return False, "条目不存在或 API 返回空"

    stype = data.get("type")
    if stype not in (SUBJECT_TYPE_ANIME, SUBJECT_TYPE_REAL):
        return False, f"条目类型为 {stype}，仅支持动画/三次元"

    return True, ""


def collect_subject_ids(mappings: dict[str, Any]) -> list[str]:
    """收集一份 mappings 里出现的全部 subject_id（含 segments 内的）。

    用于写入前批量校验。返回去重后的字符串 ID 列表（保序）。
    """
    seen: list[str] = []

    def _add(raw: Any) -> None:
        if raw is None:
            return
        sid = str(raw).strip()
        if sid and sid not in seen:
            seen.append(sid)

    for entry in (mappings or {}).values():
        if isinstance(entry, dict):
            _add(entry.get("subject_id"))
            segs = entry.get("segments")
            if isinstance(segs, list):
                for seg in segs:
                    if isinstance(seg, dict):
                        _add(seg.get("subject_id"))
        else:
            _add(entry)

    return seen
