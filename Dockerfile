FROM python:3.15-slim AS builder
WORKDIR /build
RUN pip install --no-cache-dir uv==0.13.4
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable --python /usr/local/bin/python

FROM python:3.15-slim
RUN groupadd --gid 10001 amos && useradd --uid 10001 --gid amos --no-create-home amos \
    && mkdir /data && chown amos:amos /data
WORKDIR /app
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AMOS_DATABASE_PATH=/data/amos.sqlite3
USER amos
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"]
CMD ["python", "-m", "uvicorn", "agentic_media_os.api:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
