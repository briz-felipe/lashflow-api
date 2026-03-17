FROM python:3.12-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir pip setuptools wheel --upgrade

COPY pyproject.toml .
RUN pip install --no-cache-dir ".[dev]" || pip install --no-cache-dir .

COPY app/ ./app/

# ---- production stage ----
FROM python:3.12-slim AS production

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn
COPY --from=builder /usr/local/bin/alembic /usr/local/bin/alembic
COPY --from=builder /app/app ./app
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY entrypoint.sh .

RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
