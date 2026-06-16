.PHONY: install dev build run

VENV_PYTHON = backend/venv/bin/python
VENV_PIP = backend/venv/bin/pip

install:
	cd backend && python3 -m venv venv
	$(VENV_PIP) install -r backend/requirements.txt
	cd frontend && npm install

dev-backend:
	cd backend && $(VENV_PYTHON) main.py

dev-frontend:
	cd frontend && npm run dev

build:
	cd frontend && npm run build

run:
	cd backend && $(VENV_PYTHON) main.py
