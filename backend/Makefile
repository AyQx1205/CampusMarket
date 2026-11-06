# Campus Market 常用命令（在 backend/ 下执行）
# Windows 用户可用 Git Bash / WSL，或直接复制命令到 PowerShell。

.PHONY: install install-dev migrate revision test lint fmt check run

install:
	python -m pip install -r requirements.txt

install-dev:
	python -m pip install -r requirements-dev.txt

migrate:
	alembic upgrade head

revision:
	alembic revision --autogenerate -m "$(m)"

test:
	pytest

lint:
	ruff check app tests

fmt:
	ruff format app tests

check:
	ruff check app tests
	pytest

run:
	uvicorn app.main:app --reload --port 8000