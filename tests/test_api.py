import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

TASKS = {
    "tasks": [
        {"id": "A", "name": "Design", "duration": 3, "predecessors": []},
        {"id": "B", "name": "Order parts", "duration": 2, "predecessors": ["A"]},
        {"id": "C", "name": "Prepare site", "duration": 4, "predecessors": ["A"]},
        {"id": "D", "name": "Install", "duration": 5, "predecessors": ["B", "C"]},
    ]
}


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_cpm_returns_critical_path():
    response = client.post("/cpm", json=TASKS)

    assert response.status_code == 200
    body = response.json()
    assert body["project_duration"] == 12
    assert body["critical_path"] == ["A", "C", "D"]
    assert {t["id"]: t["total_float"] for t in body["tasks"]}["B"] == 2


def test_cpm_cycle_returns_422_with_message():
    cyclic = {
        "tasks": [
            {"id": "A", "name": "A", "duration": 1, "predecessors": ["B"]},
            {"id": "B", "name": "B", "duration": 1, "predecessors": ["A"]},
        ]
    }

    response = client.post("/cpm", json=cyclic)

    assert response.status_code == 422
    assert "cycle" in response.json()["detail"].lower()


def test_cpm_rejects_invalid_payload():
    response = client.post("/cpm", json={"tasks": [{"id": "A", "name": "A", "duration": "x"}]})

    assert response.status_code == 422


def test_cpm_from_csv_body():
    csv_text = "id,name,duration,predecessors\nA,Design,3,\nB,Build,2,A\n"

    response = client.post("/cpm/csv", content=csv_text, headers={"content-type": "text/csv"})

    assert response.status_code == 200
    assert response.json()["project_duration"] == 5


def test_cpm_from_csv_reports_bad_input():
    response = client.post(
        "/cpm/csv",
        content="id,name,duration,predecessors\nA,Design,abc,\n",
        headers={"content-type": "text/csv"},
    )

    assert response.status_code == 422
    assert "line 2" in response.json()["detail"]


def test_evm_endpoint():
    response = client.post("/evm", json={"bac": 1000, "pv": 500, "ev": 450, "ac": 600})

    assert response.status_code == 200
    body = response.json()
    assert body["spi"] == pytest.approx(0.9)
    assert body["cpi"] == pytest.approx(0.75)


def test_evm_negative_value_returns_422():
    response = client.post("/evm", json={"bac": 1000, "pv": -5, "ev": 1, "ac": 1})

    assert response.status_code == 422
