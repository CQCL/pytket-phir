##############################################################################
#
# Copyright (c) 2023 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

# mypy: disable-error-code="misc"
# ruff: noqa: T201

from argparse import ArgumentParser, BooleanOptionalAction
from importlib.metadata import version

from pecos.engines.hybrid_engine import HybridEngine  # type:ignore [import-not-found]

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
        "--wasm-file-path",
        default=None,
        help="Optional WASM file path for use by the QASM programs",
    )
    parser.add_argument(
        "-m",
        "--machine",
        choices=["H1-1", "H1-2"],
        default="H1-1",
        help="machine name, H1-1 by default",
    )
    parser.add_argument(
        "-o",
        "--tket-opt-level",
        choices=["0", "1", "2"],
        default="0",
        help="TKET optimization level, 0 by default",
    )
    parser.add_argument("--verbose", action=BooleanOptionalAction)
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f'{version("pytket-phir")}',
    )
    args = parser.parse_args()

    for file in args.qasm_files:
        print(f"Processing {file}")
        circuit = None
        if args.wasm_file_path:
            print(f"Including WASM from file {args.wasm_file_path}")
            circuit = circuit_from_qasm_wasm(file, args.wasm_file_path)
        else:
            circuit = circuit_from_qasm(file)

        match args.machine:
            case "H1-1":
                machine = QtmMachine.H1_1
            case "H1-2":
                machine = QtmMachine.H1_2

        phir = pytket_to_phir(circuit, machine, int(args.tket_opt_level))
        if args.verbose:
            print("\nPHIR to be simulated:")
            print(phir)

        print("\nPECOS results:")
        print(HybridEngine(qsim="state-vector").run(program=phir, shots=10))
