"""Single-operator local API. All content endpoints require a bearer token."""

import logging
import secrets
import sqlite3
from collections.abc import Awaitable, Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from agentic_media_os.config import Settings
from agentic_media_os.models import ApprovedContent, Brief, Review, WorkflowRun
from agentic_media_os.providers import ContentProvider, LocalProvider
from agentic_media_os.store import Conflict, NotFound, SQLiteRunStore
from agentic_media_os.workflows import ContentWorkflow


class BodyLimit:
    """Bound streamed bodies too, including requests without Content-Length."""

    def __init__(self, app: ASGIApp, max_bytes: int = 262144) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > self.max_bytes:
                await JSONResponse({"detail": "Request body too large"}, status_code=413)(
                    scope, receive, send
                )
                return
            if not message.get("more_body", False):
                break
        consumed = False

        async def replay() -> Message:
            nonlocal consumed
            if not consumed:
                consumed = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, replay, send)


def create_app(
    settings: Settings | None = None, provider: ContentProvider | None = None
) -> FastAPI:
    config = settings or Settings()
    if config.api_token is None:
        raise ValueError("Set AMOS_API_TOKEN before starting the API")
    token = config.api_token.get_secret_value()
    store = SQLiteRunStore(config.database_path)
    workflow = ContentWorkflow(store, provider or LocalProvider())
    logging.basicConfig(level=config.log_level, format="%(levelname)s %(name)s %(message)s")
    app = FastAPI(title="Agentic Media OS", version="0.1.0", docs_url=None, redoc_url=None)
    app.add_middleware(BodyLimit)
    bearer = HTTPBearer(auto_error=False)

    def authenticate(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    ) -> None:
        if credentials is None or not secrets.compare_digest(
            credentials.credentials.encode(), token.encode()
        ):
            raise HTTPException(
                401, "Invalid or missing bearer token", headers={"WWW-Authenticate": "Bearer"}
            )

    protected = [Depends(authenticate)]

    @app.exception_handler(NotFound)
    async def not_found(_request: Request, _error: NotFound) -> JSONResponse:
        return JSONResponse({"detail": "Workflow not found"}, status_code=404)

    @app.exception_handler(Conflict)
    async def conflict(_request: Request, _error: Conflict) -> JSONResponse:
        return JSONResponse({"detail": "State conflict; reload the workflow"}, status_code=409)

    @app.exception_handler(ValueError)
    async def invalid(_request: Request, _error: ValueError) -> JSONResponse:
        return JSONResponse({"detail": "Invalid workflow operation"}, status_code=422)

    @app.exception_handler(sqlite3.Error)
    async def storage_error(_request: Request, _error: sqlite3.Error) -> JSONResponse:
        return JSONResponse({"detail": "Workflow storage unavailable"}, status_code=503)

    @app.exception_handler(RequestValidationError)
    async def validation(_request: Request, error: RequestValidationError) -> JSONResponse:
        # FastAPI's default response echoes invalid input, potentially including private notes.
        return JSONResponse(
            {"detail": [{"loc": e["loc"], "type": e["type"]} for e in error.errors()]},
            status_code=422,
        )

    @app.middleware("http")
    async def private_responses(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/workflows/content", dependencies=protected, status_code=201)
    def start(brief: Brief) -> WorkflowRun:
        return workflow.start(brief)

    @app.get("/workflows/{run_id}", dependencies=protected)
    def get(run_id: UUID) -> WorkflowRun:
        return store.get(run_id)

    @app.post("/workflows/{run_id}/review", dependencies=protected)
    def review(run_id: UUID, decision: Review) -> WorkflowRun:
        return workflow.review(run_id, decision)

    @app.get("/workflows/{run_id}/export", dependencies=protected)
    def export(run_id: UUID) -> ApprovedContent:
        return workflow.export(run_id)

    # The schema contains no private data; docs UI is disabled to avoid CDN dependencies.
    return app
