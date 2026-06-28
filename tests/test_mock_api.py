from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_mock_logs_endpoint_returns_log_platform_payload():
    response = client.get("/mock/logs", params={"query": "订单接口 500", "context": "order-service"})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["source"] == "data/logs/order-service.log"
    assert data["metadata"]["platform"] == "mock_log_platform"
    assert "status=500" in data["data"]


def test_mock_configs_endpoint_returns_config_center_payload():
    response = client.get("/mock/configs", params={"query": "支付超时配置"})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["source"] == "data/configs/dev.json,data/configs/prod.json"
    assert data["metadata"]["platform"] == "mock_config_center"
    assert data["metadata"]["diff_count"] > 0


def test_mock_git_commits_endpoint_returns_git_platform_payload():
    response = client.get("/mock/git/commits", params={"query": "payment timeout", "context": "order-service"})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["source"] == "data/git/commits.json"
    assert data["metadata"]["platform"] == "mock_git_platform"
    assert data["metadata"]["commit_count"] > 0
