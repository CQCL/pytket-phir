.PHONY: install dev dev-all tests lint docs clean build

install:
	pip install .

dev:
	pip install -e .

dev-all:
	pip install -e .[phirc]

tests:
	python tests/e2e_test.py
	pytest -s -x -vv tests/test*.py

lint:
	pre-commit run --all-files

docs:
	# sphinx-apidoc --implicit-namespaces -f -o docs/source/ pytket
	sphinx-build -M html docs/source/ docs/build/

clean:
	rm -rf *.egg-info dist build docs/build

build: clean
	python -m build --sdist --wheel -n
