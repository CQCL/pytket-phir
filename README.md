# pytket-phir

PHIR stands for _[PECOS](https://github.com/PECOS-packages/PECOS) High-level Intermediate Representation_.
See [PHIR specification](https://github.com/CQCL/phir/blob/main/phir_spec_qasm.md) for more.

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

See `Makefile` for other useful commands.

## Testing

Just issue `pytest` from the root directory.
