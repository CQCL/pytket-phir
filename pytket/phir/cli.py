##############################################################################
#
# Copyright (c) 2023 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

# mypy: disable-error-code="misc"

from argparse import ArgumentParser
from importlib.metadata import version

from pecos.engines.hybrid_engine import HybridEngine  # type:ignore [import-not-found]

from phir.model import PHIRModel
from pytket.qasm.qasm import (
    circuit_from_qasm,
    circuit_from_qasm_str,
    circuit_to_qasm_str,
)

from .api import pytket_to_phir
from .qtm_machine import QtmMachine
from .rebasing.rebaser import rebase_to_qtm_machine


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
        "-m",
        "--machine",
        choices=["H1-1", "H1-2"],
        default="H1-1",
        help="machine name, H1-1 by default",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f'{version("pytket-phir")}',
    )
    args = parser.parse_args()

    for file in args.qasm_files:
        print(f"Processing {file}")  # noqa: T201
        c = circuit_from_qasm(file)
        rc = rebase_to_qtm_machine(c, args.machine)
        qasm = circuit_to_qasm_str(rc, header="hqslib1")
        circ = circuit_from_qasm_str(qasm)

        match args.machine:
            case "H1-1":
                machine = QtmMachine.H1_1
            case "H1-2":
                machine = QtmMachine.H1_2
        phir = pytket_to_phir(circ, machine)
        PHIRModel.model_validate_json(phir)

        HybridEngine(qsim="state-vector").run(program=phir, shots=10)
