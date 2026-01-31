# Makefile

.PHONY: help dev prod start stop logs build clean backup

# Цвета
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
RESET  := $(shell tput -Txterm sgr0)

help: ## Показать помощь
	@echo ''
	@echo '${GREEN}LoginovRemind${RESET}'
	@echo ''
	@echo 'Использование:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  ${YELLOW}%-15s${RESET} %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ''

dev: ## Запустить в режиме разработки
	@echo "🔧 Starting development mode..."
	docker-compose -f docker-compose.yml up -d db redis
	cd backend && python run.py &
	cd frontend && npm run dev

prod: ## Запустить в production
	@echo "🚀 Starting production..."
	docker-compose --profile production up -d

start: ## Запустить сервисы
	docker-compose up -d

stop: ## Остановить сервисы
	docker-compose down

logs: ## Показать логи (make logs s=backend)
	docker-compose logs -f $(s)

build: ## Пересобрать контейнеры
	docker-compose build --no-cache

clean: ## Очистить все данные
	docker-compose down -v
	docker system prune -f

backup: ## Создать бэкап БД
	@./scripts/backup.sh

shell-backend: ## Зайти в контейнер backend
	docker-compose exec backend sh

shell-db: ## Зайти в PostgreSQL
	docker-compose exec db psql -U remind -d loginov_remind

migrate: ## Применить миграции
	docker-compose exec backend alembic upgrade head

test: ## Запустить тесты
	docker-compose exec backend pytest

install: ## Установить зависимости локально
	cd backend && pip install -r requirements.txt
	cd frontend && npm install