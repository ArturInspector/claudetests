from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
from click.testing import CliRunner

from socratic import config
from socratic.main import cli


@pytest.fixture
def runner(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> CliRunner:
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config.json")
    return CliRunner()


@pytest.fixture
def mock_transport(monkeypatch: pytest.MonkeyPatch):
    responses: dict[tuple[str, str], tuple[int, dict]] = {}
    original_client = httpx.Client

    def handler(request: httpx.Request) -> httpx.Response:
        key = (request.method, request.url.path)
        status, body = responses.get(key, (404, {"detail": "not found"}))
        return httpx.Response(status, json=body, request=request)

    transport = httpx.MockTransport(handler)

    def client_factory(*args, **kwargs):
        return original_client(transport=transport, *args, **kwargs)

    monkeypatch.setattr(httpx, "Client", client_factory)
    return responses


def test_login_saves_token(runner: CliRunner, mock_transport):
    mock_transport[("POST", "/api/v1/auth/login")] = (200, {"access_token": "tok123"})

    result = runner.invoke(cli, ["login", "--email", "a@b.com", "--password", "secret"])
    assert result.exit_code == 0
    saved = json.loads(config.CONFIG_PATH.read_text())
    assert saved["token"] == "tok123"
    assert "Login successful" in result.output


def test_start_list_and_answer_flow(runner: CliRunner, mock_transport):
    config.CONFIG_PATH.write_text(json.dumps({"base_url": "http://localhost:8000/api/v1", "token": "t"}))
    mock_transport[("POST", "/api/v1/sessions")] = (201, {"id": 1, "topic": "Networks"})
    mock_transport[("GET", "/api/v1/sessions")] = (
        200,
        [{"id": 1, "topic": "Networks", "iteration_count": 0}],
    )
    mock_transport[("POST", "/api/v1/sessions/1/answer")] = (
        200,
        {
            "iteration": {"id": 10, "number": 1, "feedback": "ok", "question": "", "answer": "", "created_at": ""},
            "similar_context": ["ctx-1"],
        },
    )
    mock_transport[("POST", "/api/v1/analyze/1")] = (200, {"summary": "analysis"})

    res_start = runner.invoke(cli, ["start", "Networks"])
    assert res_start.exit_code == 0
    assert "Started session #1" in res_start.output

    res_list = runner.invoke(cli, ["list"])
    assert res_list.exit_code == 0
    assert "#1 | Networks" in res_list.output

    res_answer = runner.invoke(
        cli,
        ["answer", "1", "--question", "Q?", "--answer", "A"],
    )
    assert res_answer.exit_code == 0
    assert "Feedback" in res_answer.output
    assert "ctx-1" in res_answer.output

    res_analyze = runner.invoke(cli, ["analyze", "1"])
    assert res_analyze.exit_code == 0
    assert "analysis" in res_analyze.output


def test_export_md_and_json(runner: CliRunner, mock_transport, tmp_path: Path):
    config.CONFIG_PATH.write_text(json.dumps({"base_url": "http://localhost:8000/api/v1", "token": "t"}))
    detail = {
        "id": 3,
        "topic": "Caching",
        "level": "mid",
        "iterations": [
            {
                "number": 1,
                "question": "Q1",
                "answer": "A1",
                "feedback": "F1",
            }
        ],
    }
    mock_transport[("GET", "/api/v1/sessions/3")] = (200, detail)

    out_md = tmp_path / "export.md"
    res_md = runner.invoke(cli, ["export", "3", "--output", str(out_md)])
    assert res_md.exit_code == 0
    assert out_md.read_text().startswith("# Session 3: Caching")

    out_json = tmp_path / "export.json"
    res_json = runner.invoke(cli, ["export", "3", "--format", "json", "--output", str(out_json)])
    assert res_json.exit_code == 0
    saved = json.loads(out_json.read_text())
    assert saved["topic"] == "Caching"

