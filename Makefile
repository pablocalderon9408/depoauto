SHELL := /bin/sh

# Variables
PROJECT ?= depoauto
COMPOSE ?= docker-compose
COMPOSE_PROD ?= docker-compose -f docker-compose.prod.yml
SU_USERNAME ?= pablo.calderon
SU_EMAIL ?= pcs@e.com
SU_PASSWORD ?= junio806P

.PHONY: help up down down-hard logs build shell web db minio createsuperuser createsuperuser-auto makemigrations migrate collectstatic seed flush restart up-prod down-prod logs-prod build-prod shell-prod createsuperuser-prod migrate-prod seed-prod

help:
	@echo "Targets disponibles:"
	@echo "  up                - Levanta servicios (web, db, minio)"
	@echo "  down              - Detiene y elimina servicios"
	@echo "  down-hard         - Detiene y elimina servicios y volúmenes"
	@echo "  logs              - Muestra logs de todos los servicios"
	@echo "  build             - Build de la imagen web"
	@echo "  shell             - Abre shell dentro del contenedor web"
	@echo "  web               - Logs del servicio web"
	@echo "  db                - Conecta a psql en db"
	@echo "  minio             - Abre mc dentro del init (si sigue vivo)"
	@echo "  createsuperuser   - Django createsuperuser"
	@echo "  makemigrations    - Django makemigrations"
	@echo "  migrate           - Django migrate"
	@echo "  collectstatic     - Django collectstatic"
	@echo "  seed              - Ejecuta seed de productos"
	@echo "  flush             - Django flush (con noinput)"
	@echo "  restart           - Reinicia el servicio web"
	@echo "  up-prod           - Levanta servicios de producción (sin MinIO)"
	@echo "  down-prod         - Detiene y elimina servicios prod"
	@echo "  logs-prod         - Logs de prod"
	@echo "  build-prod        - Build imagen web prod"
	@echo "  shell-prod        - Shell en web prod"
	@echo "  createsuperuser-prod - Django createsuperuser (prod)"
	@echo "  migrate-prod      - Django migrate (prod)"
	@echo "  seed-prod         - Ejecuta seed de productos (prod)"

up:
	$(COMPOSE) up --build

django-shell:
	$(COMPOSE) run --rm --service-ports web bash

django:
	$(COMPOSE) run --rm --service-ports web

django-shell-plus:
	$(COMPOSE) run --rm web python manage.py shell

down:
	$(COMPOSE) down

down-hard:
	$(COMPOSE) down -v

logs:
	$(COMPOSE) logs -f --tail=200

build:
	$(COMPOSE) build web

shell:
	$(COMPOSE) exec web /bin/sh -lc "python --version && sh"

web:
	$(COMPOSE) logs -f web

db:
	$(COMPOSE) exec db psql -U depoauto -d depoauto

minio:
	$(COMPOSE) exec createbuckets sh -lc "mc alias list || true"

createsuperuser:
	$(COMPOSE) exec web python manage.py createsuperuser

createsuperuser-auto:
	$(COMPOSE) exec -e DJANGO_SUPERUSER_USERNAME=$(SU_USERNAME) -e DJANGO_SUPERUSER_EMAIL=$(SU_EMAIL) -e DJANGO_SUPERUSER_PASSWORD=$(SU_PASSWORD) web python manage.py createsuperuser --noinput || true

makemigrations:
	$(COMPOSE) exec web python manage.py makemigrations

migrate:
	$(COMPOSE) exec web python manage.py migrate

collectstatic:
	$(COMPOSE) exec web python manage.py collectstatic --noinput

seed:
	$(COMPOSE) exec web python manage.py seed_products

excel-import:
	$(COMPOSE) exec web python manage.py import_products_from_excel

flush:
	$(COMPOSE) exec web python manage.py flush --noinput

restart:
	$(COMPOSE) restart web

up-prod:
	$(COMPOSE_PROD) up -d --build

down-prod:
	$(COMPOSE_PROD) down -v

logs-prod:
	$(COMPOSE_PROD) logs -f --tail=200

build-prod:
	$(COMPOSE_PROD) build web

shell-prod:
	$(COMPOSE_PROD) exec web /bin/sh -lc "python --version && sh"

createsuperuser-prod:
	$(COMPOSE_PROD) exec web python manage.py createsuperuser

migrate-prod:
	$(COMPOSE_PROD) exec web python manage.py migrate

seed-prod:
	$(COMPOSE_PROD) exec web python manage.py seed_products

minio-up:
	$(COMPOSE) up -d minio

minio-down:
	$(COMPOSE) down minio


