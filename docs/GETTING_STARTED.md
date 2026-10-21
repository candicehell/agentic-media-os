# Getting started

Run commands from the repository root with Python 3.12+. Create and activate a virtual environment as shown in the README, then `python -m pip install -e ".[dev]"`.

## CLI

`amos run examples/brief.json` generates a pending draft. Copy its UUID; `amos show UUID` reloads persisted state. Read all source notes and the output before submitting `amos review UUID examples/review.json`. `amos export UUID` returns the approved payload.

To edit, create a review JSON with `expected_version`, `decision: "approve"`, `reviewer`, `note`, and optional `edited_draft` containing `title`, `body`, and `source_ids`. Omit the draft to approve unchanged. Original text is retained. Source IDs must exist in the brief. Rejection uses `decision: "reject"`; rejected runs cannot be reopened.

Exit codes: 0 success, 1 created run with generation failure, 2 invalid input/configuration/state/storage operation.

## Configuration

Settings load environment variables and optional `.env` in the current directory. Environment values take precedence. Copy `.env.example` if needed; never commit secrets.

| Variable | Default | Meaning |
| --- | --- | --- |
| AMOS_DATABASE_PATH | data/amos.sqlite3 | Operator-controlled SQLite file |
| AMOS_PROVIDER | local | Only shipped provider; unknown values fail |
| AMOS_LOG_LEVEL | INFO | DEBUG, INFO, WARNING, ERROR |
| AMOS_API_TOKEN | unset | API requires 32+ ASCII characters without whitespace |

CLI needs no token. Generate one with `python -c "import secrets; print(secrets.token_urlsafe(32))"`, store it as `AMOS_API_TOKEN` in `.env`, and restart after changing settings.

## API

```sh
uvicorn agentic_media_os.api:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
```

`GET /health` is public liveness, not readiness. `GET /openapi.json` is public schema; a CDN-backed docs UI is disabled. Workflow endpoints require `Authorization: Bearer YOUR_TOKEN`.

| Endpoint | Behavior |
| --- | --- |
| POST /workflows/content | Brief → persisted run; 201 even if generation fails; inspect status |
| GET /workflows/{id} | Load run or 404 |
| POST /workflows/{id}/review | Review → updated run; stale or terminal state returns 409 |
| GET /workflows/{id}/export | Approved payload or 409 |

macOS/Linux request (also export the token into the shell):

```sh
curl -H "Authorization: Bearer $AMOS_API_TOKEN" -H "Content-Type: application/json" --data-binary @examples/brief.json http://127.0.0.1:8000/workflows/content
```

PowerShell request (set `$env:AMOS_API_TOKEN` for this shell):

```powershell
$headers = @{ Authorization = "Bearer $env:AMOS_API_TOKEN" }
$run = Invoke-RestMethod http://127.0.0.1:8000/workflows/content -Method Post -Headers $headers -ContentType application/json -Body (Get-Content examples/brief.json -Raw)
Invoke-RestMethod "http://127.0.0.1:8000/workflows/$($run.id)" -Headers $headers
```

422 indicates schema/operation validation; 413 oversized body; 401 authentication failure; 503 SQLite failure. Validation errors do not echo private values. Provider failure creates a durable failed run with a fixed error code.

## Docker (optional)

Requires Docker Engine and Compose v2. Put a generated token in `.env`, then `docker compose up --build`. Compose binds to host loopback, persists SQLite in a named volume, and runs as non-root with a read-only root filesystem. Docker administrators can inspect the environment token. `docker compose down` preserves state; back up and retain the volume intentionally.

## Troubleshooting

For missing token errors, check `.env` location and token length. For 409, reload the record instead of retrying stale reviews. For failed generation, test the provider with synthetic data; private exception strings are intentionally not logged. A process interrupted during generation can leave `running`; start a new run because resume is not implemented. Do not share private notes, databases or `.env` in bug reports.
