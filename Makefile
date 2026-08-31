.PHONY: install dev lint test docker-up docker-airgap download-models verify-airgap train-router train-yolo clean

install:
	uv sync --all-packages

dev:
	# Run backend + frontend
	echo "Running backend and frontend..."

lint:
	ruff check .
	ruff format .

test:
	pytest

docker-up:
	docker compose up

docker-airgap:
	docker compose -f infra/docker/docker-compose.airgap.yml up

download-models:
	bash infra/scripts/download_models.sh

verify-airgap:
	bash infra/scripts/verify_airgap.sh

train-router:
	python training/task-router/train_router.py

train-yolo:
	python training/yolo-pid/train_yolo.py

clean:
	rm -rf build/
	find . -type d -name __pycache__ -exec rm -rf {} +
