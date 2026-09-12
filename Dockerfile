FROM node:22-alpine AS web
WORKDIR /build
COPY apps/web/package*.json ./
RUN npm ci
COPY apps/web ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 DCMSIM_DATABASE_URL=sqlite:////data/dcmsim.db
COPY pyproject.toml README.md ./
COPY apps ./apps
RUN pip install --no-cache-dir .
COPY --from=web /build/dist /app/apps/api/app/static
COPY apps/api/alembic.ini ./alembic.ini
COPY apps/api/alembic ./apps/api/alembic
RUN mkdir -p /data
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/ready', timeout=3).close()"
CMD ["sh", "-c", "alembic -c apps/api/alembic.ini upgrade head && uvicorn app.main:app --app-dir apps/api --host 0.0.0.0 --port 8080"]

