SHELL := /bin/bash

.PHONY: setup setup-backend setup-frontend setup-env db-bootstrap dev-backend dev-frontend

setup: setup-backend setup-frontend

setup-backend:
	cd Backend && pip install -r requirements.txt

setup-frontend:
	cd Frontend && npm install

setup-env:
	@if [ ! -f Backend/.env ]; then \
		cp .env.example Backend/.env; \
		echo "Created Backend/.env from .env.example"; \
	else \
		echo "Backend/.env already exists"; \
	fi

db-bootstrap:
	@set -a; source Backend/.env; set +a; \
	mysql -u "$${USER}" -p"$${PASSWORD}" -e "CREATE DATABASE IF NOT EXISTS $${DATABASE};"; \
	mysql -u "$${USER}" -p"$${PASSWORD}" "$${DATABASE}" < Database/truebalance_db.sql

dev-backend:
	cd Backend && python main.py

dev-frontend:
	cd Frontend && npm run dev
