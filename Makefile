COMPOSE = docker compose -f infra/docker/docker-compose.yml

.PHONY: up down logs migrate test lint fmt shell celery-ping

up:
	$(COMPOSE) up --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f api

migrate:
	$(COMPOSE) exec api python manage.py migrate

test:
	cd backend && python -m pytest

lint:
	cd backend && ruff check . && black --check . && \
		SECRET_KEY=lint-only DATABASE_URL=postgres://x:x@localhost/x REDIS_URL=redis://localhost:6379/0 mypy .

fmt:
	cd backend && ruff check --fix . && black .

shell:
	$(COMPOSE) exec api python manage.py shell

# Proves a worker is actually consuming from RabbitMQ, not just that the
# task queues without error.
celery-ping:
	$(COMPOSE) exec api python manage.py shell -c "from shared.health.tasks import ping; print(ping.delay().get(timeout=10))"
