##############################################################################
#
# Copyright (c) 2023-2024 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

# mypy: disable-error-code="misc"
# ruff: noqa: T201

import logging
from argparse import ArgumentParser
from importlib.metadata import version

from pecos.engines.hybrid_engine import HybridEngine
from pecos.foreign_objects.wasmtime import WasmtimeObj

from pytket.phir.phirgen import WORDSIZE
from pytket.qasm.qasm import (
    circuit_from_qasm,
    circuit_from_qasm_wasm,
)

from .api import pytket_to_phir
from .qtm_machine import QtmMachine


def main() -> None:
    """pytket-phir compiler CLI."""
    parser = ArgumentParser(
        prog="phirc",
        description="Emulates QASM program execution via PECOS",
    )
    parser.add_argument(
        "qasm_files", nargs="+", default=None, help="One or more QASM files to emulate"
    )
    parser.add_argument(
        "-w",
        "--wasm-file",
        default=None,
        help="Optional WASM file for use by the QASM programs",
    )
    parser.add_argument(
        "-m",
        "--machine",
        choices=["H1"],
        default="H1",
        help="Machine name, H1 by default",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument(
        "--version",
        action="version",
        version=version("pytket-phir"),
    )
    args = parser.parse_args()

    for file in args.qasm_files:
        print(f"Processing {file}")
        circuit = None
        if args.wasm_file:
            print(f"Including WASM from file {args.wasm_file}")
            circuit = circuit_from_qasm_wasm(file, args.wasm_file, maxwidth=WORDSIZE)
            wasm_pecos_obj = WasmtimeObj(args.wasm_file)
        else:
            circuit = circuit_from_qasm(file, maxwidth=WORDSIZE)

        match args.machine:
            case "H1":
                machine = QtmMachine.H1
            case _:
                raise NotImplementedError

        if args.verbose:
            logging.basicConfig(level=logging.INFO)
        phir = pytket_to_phir(circuit, machine)

        print("\nPECOS results:")
        print(
            HybridEngine(qsim="state-vector").run(
                program=phir,
                shots=10,
                foreign_object=wasm_pecos_obj if args.wasm_file else None,  # type: ignore[arg-type]
            )
        )
