from fastapi.testclient import TestClient

from chat.server import app

client = TestClient(app)


def test_seeds_are_a_through_d():
    data = client.get("/api/seeds").json()
    assert [row["id"] for row in data] == ["A", "B", "C", "D"]
    assert data[3]["force_local"] is True
    assert "standup" in data[0]["prompt"].lower()


def test_chat_dry_run_a():
    res = client.post(
        "/api/chat",
        json={
            "prompt": "Summarize this email in one sentence. Standup moves to 10:30.",
            "dry_run": True,
        },
    )
    body = res.json()
    assert body["ok"] is True
    assert body["scenario"] == "A"
    assert body["telemetry"]["route"] == "auto/local"


def test_chat_dry_run_b():
    res = client.post(
        "/api/chat",
        json={
            "prompt": (
                "Design a production-ready hybrid architecture. "
                "Compare routing approaches and list failure modes."
            ),
            "dry_run": True,
        },
    )
    body = res.json()
    assert body["scenario"] == "B"
    assert body["telemetry"]["route"] == "auto/cloud"


def test_chat_dry_run_c():
    res = client.post(
        "/api/chat",
        json={
            "prompt": (
                "Priya Naidoo <priya.naidoo@example.net> ID 9001014800088 "
                "phone +27 82 555 0147 — draft a refund reply."
            ),
            "dry_run": True,
        },
    )
    body = res.json()
    assert body["scenario"] == "C"
    assert body["telemetry"]["pii_redacted"] is True
    assert "priya.naidoo@example.net" not in body["outgoing"]


def test_chat_dry_run_d():
    res = client.post(
        "/api/chat",
        json={
            "prompt": "Design a production-ready hybrid architecture with trade-offs.",
            "force_local": True,
            "dry_run": True,
        },
    )
    body = res.json()
    assert body["scenario"] == "D"
    assert body["telemetry"]["route"] == "auto/local"
