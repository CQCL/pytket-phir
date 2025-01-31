.PHONY: install dev dev-all tests lint docs clean build

install:
	uv pip install .

dev:
	uv pip install -e .

dev-all:
	uv pip install -e .[phirc]

tests:
	uv run python tests/e2e_test.py
	uv run pytest -s -x -vv tests/test*.py

lint:
	uv run pre-commit run --all-files

docs:
	# uv run sphinx-apidoc --implicit-namespaces -f -o docs/source/ pytket
	uv run sphinx-build -M html docs/source/ docs/build/

clean:
	rm -rf *.egg-info dist build docs/build

build: clean
	uv build
