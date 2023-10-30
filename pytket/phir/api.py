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
        machine = None

    logger.debug("Sharding input circuit...")
    sharder = Sharder(circuit)
    shards = sharder.shard()

    if machine:
        # Only print message if a machine object is passed
        # Otherwise, placment and routing are functionally skipped
        # The function is called, but the output is just filled with 0s
        logger.debug("Performing placement and routing...")
    placed = place_and_route(shards, machine)

    phir_json = genphir(placed)

    if logger.getEffectiveLevel() <= logging.INFO:
        print(PHIRModel.model_validate_json(phir_json))  # type: ignore[misc]
    return phir_json
