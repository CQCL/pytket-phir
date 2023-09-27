.PHONY: tests, lint

tests:
	pytest -s -x -vv tests/test*.py

lint:
	pre-commit run --all-files
