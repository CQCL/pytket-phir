.PHONY: tests lint clean build install dev docs

tests:
	pytest -s -x -vv tests/test*.py

lint:
	pre-commit run --all-files

clean:
	rm -rf *.egg-info dist build docs/build

build: clean
	python -m build --sdist -n

install:
	pip install .

dev:
	pip install -e .

docs:
	# sphinx-apidoc -f -o docs/source/ pytket
	sphinx-build -M html docs/source/ docs/build/
