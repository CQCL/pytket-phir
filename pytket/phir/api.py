##############################################################################
#
# Copyright (c) 2023 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

import logging
from typing import TYPE_CHECKING

from rich import print

from phir.model import PHIRModel
from pytket.qasm.qasm import circuit_from_qasm_str

from .phirgen import genphir
from .phirgen_parallel import genphir_parallel
from .place_and_route import place_and_route
from .qtm_machine import QTM_MACHINES_MAP, QtmMachine
from .rebasing.rebaser import rebase_to_qtm_machine
from .sharding.sharder import Sharder

if TYPE_CHECKING:
    from pytket.circuit import Circuit

    from .machine import Machine

logger = logging.getLogger(__name__)

DEFAULT_TKET_OPT_LEVEL = 0


def pytket_to_phir(
    circuit: "Circuit",
    qtm_machine: QtmMachine | None = None,
    tket_optimization_level: int = DEFAULT_TKET_OPT_LEVEL,
) -> str:
    """Converts a pytket circuit into its PHIR representation.

    This can optionally include rebasing against a Quantinuum machine architecture,
    and control of the TKET optimization level.

    :param circuit: Circuit object to be converted
    :param qtm_machine: (Optional) Quantinuum machine architecture to rebase against
    :param tket_optimization_level: (Default=0) TKET circuit optimization level

    Returns:
        PHIR JSON as a str
    """
    logger.info("Starting phir conversion process for circuit %s", circuit)
    machine: Machine | None = None
    if qtm_machine:
        logger.info("Rebasing to machine %s", qtm_machine)
        circuit = rebase_to_qtm_machine(
            circuit, qtm_machine.value, tket_optimization_level
        )
        machine = QTM_MACHINES_MAP.get(qtm_machine)
    else:
        machine = None

    logger.debug("Sharding input circuit...")
    sharder = Sharder(circuit)
    shards = sharder.shard()

    if machine:
        # Only print message if a machine object is passed
        # Otherwise, placement and routing are functionally skipped
        # The function is called, but the output is just filled with 0s
        logger.debug("Performing placement and routing...")
    placed = place_and_route(shards, machine)
    if machine:
        phir_json = genphir_parallel(placed, machine)
    else:
        phir_json = genphir(placed, machine_ops=bool(machine))
    if logger.getEffectiveLevel() <= logging.INFO:
        print(PHIRModel.model_validate_json(phir_json))  # type: ignore[misc]
    return phir_json


def qasm_to_phir(
    qasm: str,
    qtm_machine: QtmMachine | None = None,
    tket_optimization_level: int = DEFAULT_TKET_OPT_LEVEL,
) -> str:
    """Converts a QASM circuit string into its PHIR representation.

    This can optionally include rebasing against a Quantinuum machine architecture,
    and control of the TKET optimization level.

    :param circuit: Circuit object to be converted
    :param qtm_machine: (Optional) Quantinuum machine architecture to rebase against
    :param tket_optimization_level: (Default=0) TKET circuit optimization level
    """
    circuit = circuit_from_qasm_str(qasm)
    return pytket_to_phir(circuit, qtm_machine, tket_optimization_level)
