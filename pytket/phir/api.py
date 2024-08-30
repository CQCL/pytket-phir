##############################################################################
#
# Copyright (c) 2023-2024 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

# mypy: disable-error-code="misc"

import logging
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING

from rich import print  # noqa: A004

from phir.model import PHIRModel
from pytket.qasm.qasm import circuit_from_qasm_str, circuit_from_qasm_wasm

from .phirgen import WORDSIZE, genphir
from .phirgen_parallel import genphir_parallel
from .place_and_route import place_and_route
from .qtm_machine import QTM_MACHINES_MAP, QtmMachine
from .rebasing.rebaser import rebase_to_qtm_machine
from .sharding.sharder import Sharder

if TYPE_CHECKING:
    from pytket.circuit import Circuit

    from .machine import Machine

logger = logging.getLogger(__name__)


def pytket_to_phir(circuit: "Circuit", qtm_machine: QtmMachine | None = None) -> str:
    """Converts a pytket circuit into its PHIR representation.

    This can optionally include rebasing against a Quantinuum machine architecture,
    and control of the TKET optimization level.

    :param circuit: Circuit object to be converted
    :param qtm_machine: (Optional) Quantinuum machine architecture to rebase against

    Returns:
        PHIR JSON as a str
    """
    logger.info("Starting phir conversion process for circuit %s", circuit)
    machine: Machine | None = None
    if qtm_machine:
        logger.info("Rebasing to machine %s", qtm_machine)
        circuit = rebase_to_qtm_machine(circuit, qtm_machine)
        machine = QTM_MACHINES_MAP.get(qtm_machine)
    else:
        machine = None

    logger.debug("Sharding input circuit...")
    shards = Sharder(circuit).shard()

    if machine:
        # Only print message if a machine object is passed
        # Otherwise, placement and routing are functionally skipped
        # The function is called, but the output is just filled with 0s
        logger.debug("Performing placement and routing...")
    placed = place_and_route(shards, machine)
    # safety check: never run with parallelization on a 1 qubit circuit
    if machine and len(circuit.qubits) > 1:
        phir_json = genphir_parallel(placed, machine)
    else:
        phir_json = genphir(placed, machine_ops=bool(machine))
    if logger.getEffectiveLevel() <= logging.INFO:
        print("PHIR JSON:")
        print(PHIRModel.model_validate_json(phir_json))
    return phir_json


def qasm_to_phir(
    qasm: str,
    qtm_machine: QtmMachine | None = None,
    wasm_bytes: bytes | None = None,
) -> str:
    """Converts a QASM circuit string into its PHIR representation.

    This can optionally include rebasing against a Quantinuum machine architecture,
    and control of the TKET optimization level.

    :param qasm: QASM input to be converted
    :param qtm_machine: (Optional) Quantinuum machine architecture to rebase against
    :param wasm_bytes: (Optional) WASM as bytes to include as part of circuit
    """
    circuit: Circuit
    if wasm_bytes:
        with (
            NamedTemporaryFile(suffix=".qasm", delete=False) as qasm_file,
            NamedTemporaryFile(suffix=".wasm", delete=False) as wasm_file,
        ):
            qasm_file.write(qasm.encode())
            qasm_file.flush()
            wasm_file.write(wasm_bytes)
            wasm_file.flush()

            circuit = circuit_from_qasm_wasm(
                qasm_file.name, wasm_file.name, maxwidth=WORDSIZE
            )
    else:
        circuit = circuit_from_qasm_str(qasm, maxwidth=WORDSIZE)
    return pytket_to_phir(circuit, qtm_machine)
