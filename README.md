# pytemplate

This is a Python 3.11 app called pytemplate. It uses toml instead of setup.py for configuration. The project includes Docker, Pyright, Ruff, GitHub Actions, Black, pre-commit, and Sphinx.

## Project Structure

The project structure is as follows:

```sh
pytemplate
├── .github
│   └── workflows
│       └── python-app.yml
├── .pre-commit-config.yaml
├── .vscode
│   ├── launch.json
│   └── settings.json
├── docs
│   ├── conf.py
│   ├── index.rst
│   └── _static
├── qtmlib
│   ├── __init__.py
│   ├── main.py
│   └── utils.py
├── tests
│   ├── __init__.py
│   ├── test_main.py
│   └── test_utils.py
├── .dockerignore
├── .gitignore
├── Dockerfile
├── pyproject.toml
├── README.md
└── requirements.txt
```

The source code is located in the `pytemplate` folder, which contains the `__init__.py`, `main.py`, and `utils.py` files. The tests are located in the `tests` folder, which contains the `test_main.py` and `test_utils.py` files.

The project uses toml for configuration instead of setup.py. The configuration file is located in `pyproject.toml`.

The project includes Docker, with a Dockerfile located in the root directory. The `.dockerignore` file is also located in the root directory.

The project includes Pyright for static type checking, pre-commit for code formatting, Black for code formatting and Ruff for linting. The configuration for these tools is located in the `.pre-commit-config.yaml` file.

The project includes Sphinx for documentation, with the documentation located in the `docs` folder. The `conf.py` file contains the configuration for Sphinx.

The project includes GitHub Actions for continuous integration, with the configuration located in the `.github/workflows/python-app.yml` file.

## Installation

To install the project, clone the repository and run:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -U pip setuptools
pip install -r requirements.txt
pre-commit install
```

Then install the project using:

```sh
pip install -e .
```

## Testing

Just issue `pytest` from the root directory.
