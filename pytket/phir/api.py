import logging
from typing import TYPE_CHECKING

from rich import print

from phir.model import PHIRModel
from pytket.circuit import Circuit
from pytket.phir.phirgen import genphir
from pytket.phir.place_and_route import place_and_route
from pytket.phir.qtm_machine import QTM_MACHINES_MAP, QtmMachine
from pytket.phir.rebasing.rebaser import rebase_to_qtm_machine
from pytket.phir.sharding.sharder import Sharder

if TYPE_CHECKING:
    from pytket.phir.machine import Machine

logger = logging.getLogger(__name__)


def pytket_to_phir(
    circuit: Circuit,
    qtm_machine: QtmMachine | None = None,
) -> str:
    """Converts a pytket circuit into its PHIR representation.

    This can optionally include rebasing against a Quantinuum machine architecture.

    :param circuit: Circuit object to be converted
    :param qtm_machine: (Optional) Quantinuum machine architecture to rebase against

    Returns:
    -------
        PHIR JSON as a str
    """
    logger.info(f"Starting phir conversion process for circuit {circuit}")
    machine: Machine | None = None
    if qtm_machine:
        logger.info(f"Rebasing to machine {qtm_machine}")
        circuit = rebase_to_qtm_machine(circuit, qtm_machine.value)
        machine = QTM_MACHINES_MAP.get(qtm_machine)
    else:
        msg = "Machine parameter is currently required"
        raise NotImplementedError(msg)

    logger.debug("Sharding input circuit...")
    sharder = Sharder(circuit)
    shards = sharder.shard()

    logger.debug("Performing placement and routing...")
    if machine:
        placed = place_and_route(machine, shards)
    else:
        msg = "no machine found"
        raise ValueError(msg)

    phir_json = genphir(placed)

    logger.info(
        print(PHIRModel.model_validate_json(phir_json, strict=True)),  # type: ignore[func-returns-value, misc]
    )
    return phir_json
