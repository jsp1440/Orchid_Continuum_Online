.PHONY: api worker widgets build

api:
	uvicorn apps.api.main:app --reload

worker:
	python apps/worker/worker.py

widgets:
	cd frontend/widgets && npm install && npm run build

build: widgets
