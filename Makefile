.PHONY: install test lint web-test build dev-api dev-web migrate
install:
	python -m pip install -e ".[dev]"
	cd apps/web && npm install
test:
	pytest
web-test:
	cd apps/web && npm test -- --run
lint:
	ruff check apps/api
	cd apps/web && npm run lint && npm run typecheck
build:
	cd apps/web && npm run build
dev-api:
	uvicorn app.main:app --app-dir apps/api --reload
dev-web:
	cd apps/web && npm run dev
migrate:
	alembic -c apps/api/alembic.ini upgrade head

