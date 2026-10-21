import json
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from agentic_media_os.api import create_app
from agentic_media_os.cli import main
from agentic_media_os.config import Settings
from agentic_media_os.models import Brief
from agentic_media_os.providers import LocalProvider

TOKEN = "test-token-" + "x" * 32
AUTH = {"Authorization": f"Bearer {TOKEN}"}


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    return TestClient(
        create_app(
            Settings(
                database_path=tmp_path / "api.sqlite3", api_token=SecretStr(TOKEN), _env_file=None
            )
        )
    )


def test_api_requires_token(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="AMOS_API_TOKEN"):
        create_app(
            Settings(database_path=tmp_path / "none.sqlite3", api_token=None, _env_file=None)
        )


def test_api_flow(client: TestClient, brief: Brief) -> None:
    assert client.get("/health").json() == {"status": "ok"}
    assert client.post("/workflows/content", json=brief.model_dump(mode="json")).status_code == 401
    response = client.post("/workflows/content", headers=AUTH, json=brief.model_dump(mode="json"))
    assert response.status_code == 201
    run = response.json()
    path = f"/workflows/{run['id']}"
    assert client.get(path, headers=AUTH).json() == run
    assert client.get(path + "/export", headers=AUTH).status_code == 409
    review = json.loads(Path("examples/review.json").read_text())
    assert client.post(path + "/review", headers=AUTH, json=review).json()["status"] == "approved"
    assert client.post(path + "/review", headers=AUTH, json=review).status_code == 409
    assert client.get(path + "/export", headers=AUTH).json()["draft"] == run["draft"]
    assert client.get(path, headers=AUTH).headers["cache-control"] == "no-store"


def test_api_validation_and_size_limits(client: TestClient) -> None:
    assert client.get(f"/workflows/{uuid4()}", headers=AUTH).status_code == 404
    assert client.get("/workflows/not-a-uuid", headers=AUTH).status_code == 422
    response = client.post("/workflows/content", headers=AUTH, json={"private": "sensitive-text"})
    assert response.status_code == 422 and "sensitive-text" not in response.text
    assert client.post("/workflows/content", headers=AUTH, content=b"x" * 262145).status_code == 413
    assert (
        client.post(
            "/workflows/content", headers=AUTH, content=iter([b"x" * 140000] * 2)
        ).status_code
        == 413
    )


def test_api_failure_returns_inspectable_run(tmp_path: Path, brief: Brief) -> None:
    class Broken(LocalProvider):
        def plan(self, *args: object) -> object:
            raise RuntimeError("private-data")

    client = TestClient(
        create_app(
            Settings(
                database_path=tmp_path / "failure.sqlite3",
                api_token=SecretStr(TOKEN),
                _env_file=None,
            ),
            Broken(),
        )
    )
    response = client.post("/workflows/content", headers=AUTH, json=brief.model_dump(mode="json"))
    assert response.status_code == 201  # run resource created, but generation failed
    assert response.json()["status"] == "failed" and "private-data" not in response.text


def test_cli_end_to_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("AMOS_DATABASE_PATH", str(tmp_path / "cli.sqlite3"))
    assert main(["run", "examples/brief.json"]) == 0
    run = json.loads(capsys.readouterr().out)
    assert main(["export", run["id"]]) == 2
    capsys.readouterr()
    assert main(["review", run["id"], "examples/review.json"]) == 0
    capsys.readouterr()
    assert main(["export", run["id"]]) == 0
    assert json.loads(capsys.readouterr().out)["workflow_id"] == run["id"]
