.PHONY: install run test lint format clean

install:
	python -m pip install -r requirements.txt
	pre-commit install

run:
	uvicorn main:app --reload --host 0.0.0.0 --port 8030

test:
	python -m pytest

lint:
	ruff check .

format:
	ruff format .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
