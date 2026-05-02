.PHONY: dev down seed e2e

dev:
	docker compose -f docker-compose.dev.yml up -d
	@echo "backend: http://localhost:8000  frontend: http://localhost:3000"

down:
	docker compose -f docker-compose.dev.yml down

seed:
	python scripts/seed_dev_db.py

e2e:
	BASE_URL=http://localhost:3000 pnpm --filter frontend exec playwright test --grep @e2e-real
