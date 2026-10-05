"""
映射 API 测试
"""

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api import deps, mappings


@pytest.fixture
def app_with_auth():
    """创建带有认证的测试应用"""
    app = FastAPI()
    app.include_router(mappings.router)

    async def mock_get_current_user(request=None, credentials=None):
        return {"username": "testuser", "id": 1}

    app.dependency_overrides[deps.get_current_user_flexible] = mock_get_current_user

    yield app

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_custom_mappings(app_with_auth):
    """测试获取自定义映射"""
    with patch("app.api.mappings.mapping_service") as mock_service:
        mock_service.get_all_mappings.return_value = {"test": "value"}

        async with AsyncClient(
            transport=ASGITransport(app=app_with_auth), base_url="http://test"
        ) as client:
            response = await client.get("/api/mappings")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"


@pytest.mark.asyncio
async def test_get_custom_mappings_exception(app_with_auth):
    """测试获取自定义映射异常"""
    with patch("app.api.mappings.mapping_service") as mock_service:
        mock_service.get_all_mappings.side_effect = Exception("Error")

        async with AsyncClient(
            transport=ASGITransport(app=app_with_auth), base_url="http://test"
        ) as client:
            response = await client.get("/api/mappings")

            assert response.status_code == 500


@pytest.mark.asyncio
async def test_update_custom_mappings(app_with_auth):
    """测试更新自定义映射"""
    with patch("app.api.mappings.mapping_service"):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_auth), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/mappings", json={"mappings": {"test": "value"}}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"


@pytest.mark.asyncio
async def test_update_custom_mappings_exception(app_with_auth):
    """测试更新自定义映射异常"""
    with patch("app.api.mappings.mapping_service") as mock_service:
        mock_service.update_custom_mappings.side_effect = Exception("Error")

        async with AsyncClient(
            transport=ASGITransport(app=app_with_auth), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/mappings", json={"mappings": {"test": "value"}}
            )

            assert response.status_code == 500


@pytest.mark.asyncio
async def test_delete_custom_mapping(app_with_auth):
    """测试删除自定义映射"""
    with patch("app.api.mappings.mapping_service") as mock_service:
        mock_service.get_all_mappings.return_value = {"test": "value"}

        async with AsyncClient(
            transport=ASGITransport(app=app_with_auth), base_url="http://test"
        ) as client:
            response = await client.delete("/api/mappings/test")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"


@pytest.mark.asyncio
async def test_delete_custom_mapping_not_found(app_with_auth):
    """测试删除不存在的映射"""
    with patch("app.api.mappings.mapping_service") as mock_service:
        mock_service.get_all_mappings.return_value = {}

        async with AsyncClient(
            transport=ASGITransport(app=app_with_auth), base_url="http://test"
        ) as client:
            response = await client.delete("/api/mappings/nonexistent")

            assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_custom_mapping_exception(app_with_auth):
    """测试删除映射异常"""
    with patch("app.api.mappings.mapping_service") as mock_service:
        mock_service.get_all_mappings.return_value = {"test": "value"}
        mock_service.delete_single_mapping.side_effect = Exception("Error")

        async with AsyncClient(
            transport=ASGITransport(app=app_with_auth), base_url="http://test"
        ) as client:
            response = await client.delete("/api/mappings/test")

            assert response.status_code == 500


@pytest.mark.asyncio
async def test_update_custom_mappings_write_failure_returns_500(app_with_auth):
    """写入失败必须返回 500

    原实现丢弃 update_custom_mappings 的返回值、无条件回 success，前端会显示
    「保存成功」而改动并未落盘。
    """
    with patch("app.api.mappings.mapping_service") as mock_service:
        mock_service.update_custom_mappings.return_value = False

        async with AsyncClient(
            transport=ASGITransport(app=app_with_auth), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/mappings", json={"mappings": {"test": "value"}}
            )

        assert response.status_code == 500
        assert "写入失败" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_custom_mappings_rejects_bad_types(app_with_auth):
    """mappings/rules 类型非法时应返回 400，而不是写坏配置文件"""
    async with AsyncClient(
        transport=ASGITransport(app=app_with_auth), base_url="http://test"
    ) as client:
        bad_mappings = await client.post("/api/mappings", json={"mappings": []})
        assert bad_mappings.status_code == 400

        bad_rules = await client.post(
            "/api/mappings", json={"mappings": {}, "rules": "oops"}
        )
        assert bad_rules.status_code == 400


# --------------------------------------------------------------------------
# 章节列表端点（供映射弹窗自动推算偏移量）
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_subject_episodes(app_with_auth):
    """返回正片章节的 sort/name/airdate"""
    from unittest.mock import MagicMock

    api = MagicMock()
    api.get_episodes.return_value = {
        "data": [
            {"sort": 1, "name": "Ep1", "name_cn": "第一集", "airdate": "2024-01-01"},
            {"sort": 2, "name": "Ep2", "name_cn": "", "airdate": "2024-01-08"},
            {"name": "no sort field"},  # 无 sort 应被跳过
        ],
        "total": 3,
    }

    with patch(
        "app.utils.bangumi_api.factory.build_bangumi_api_from_primary_config",
        return_value=api,
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_auth), base_url="http://test"
        ) as client:
            response = await client.get("/api/mappings/subject/639938/episodes")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total"] == 2
    assert data["episodes"][0]["sort"] == 1
    assert data["episodes"][1]["airdate"] == "2024-01-08"
    api.close.assert_called_once()


@pytest.mark.asyncio
async def test_get_subject_episodes_invalid_id(app_with_auth):
    async with AsyncClient(
        transport=ASGITransport(app=app_with_auth), base_url="http://test"
    ) as client:
        response = await client.get("/api/mappings/subject/0/episodes")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_subject_episodes_no_account(app_with_auth):
    """无可用账号时给出可操作的 400，而不是 500"""
    with patch(
        "app.utils.bangumi_api.factory.build_bangumi_api_from_primary_config",
        return_value=None,
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_auth), base_url="http://test"
        ) as client:
            response = await client.get("/api/mappings/subject/639938/episodes")

    assert response.status_code == 400
    assert "账号" in response.json()["detail"]
