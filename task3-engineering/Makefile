.PHONY: setup test lint clean

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest

setup: $(VENV)/bin/activate

$(VENV)/bin/activate:
	python -m venv $(VENV)
	$(PIP) install -r requirements.txt

test: setup
	$(PYTEST) -v

clean:
	rm -rf $(VENV) __pycache__ .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
