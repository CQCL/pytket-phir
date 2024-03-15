# pytket-phir

[![PyPI version](https://badge.fury.io/py/pytket-phir.svg)](https://badge.fury.io/py/pytket-phir)
[![Python versions](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://img.shields.io/badge/python-3.10%2C%203.11%20%7C%203.12-blue.svg)

PHIR stands for _[PECOS](https://github.com/PECOS-packages/PECOS) High-level Intermediate Representation_.
See [PHIR specification](https://github.com/CQCL/phir/blob/main/spec.md) for more.

`pytket-phir` is a circuit analyzer and translator from [pytket](https://tket.quantinuum.com/api-docs/index.html) to PHIR.

Also included is the CLI tool `phirc` that takes QASM programs as input and emulates them using PECOS.

## Prerequisites

Python >=3.10

## Installation

Just issue `pip install pytket-phir` to obtain the latest stable release.

## phirc CLI

The package includes a tool for emulating QASM files from the command line using PECOS.

Install additional dependencies needed for the CLI using `pip install pytket-phir[phirc]`.

```sh
❯ phirc -h
usage: phirc [-h] [-w WASM_FILE] [-m {H1}] [-v] [--version] qasm_files [qasm_files ...]

Emulates QASM program execution via PECOS

positional arguments:
  qasm_files            One or more QASM files to emulate

options:
  -h, --help            show this help message and exit
  -w WASM_FILE, --wasm-file WASM_FILE
                        Optional WASM file for use by the QASM programs
  -m {H1}, --machine {H1}
                        Machine name, H1 by default
  -v, --verbose
  --version             show program's version number and exit
```

## Development

Clone the repository and run:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -U pip setuptools
pip install -r requirements.txt
pre-commit install
```

Then, install the project using:

```sh
pip install -e .
```

See `Makefile` for other useful commands.

## Testing

Issue `pytest` from the root directory.
