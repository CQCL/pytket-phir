.PHONY: tests lint clean build install dev

tests:
	pytest -s -x -vv tests/test*.py

lint:
	pre-commit run --all-files

clean:
	rm -rf *.egg-info dist build

build: clean
	python -m build --sdist -n

install:
	pip install .

dev:
	pip install -e .
