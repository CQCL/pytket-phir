import logging

from pytket.circuit import Circuit
from pytket.phir.qtm_machine import QtmMachine
from pytket.phir.rebasing.rebaser import rebase_to_qtm_machine
from pytket.phir.sharding.sharder import Sharder

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
    if qtm_machine:
        logger.info(f"Rebasing to machine {qtm_machine}")
        circuit = rebase_to_qtm_machine(circuit, qtm_machine.value)

    sharder = Sharder(circuit)
    shards = sharder.shard()

    phir_output = str(shards)  # Just returning fake string for now
    # TODO: Pass shards[] into placement, routing, etc
    # TODO: Convert to PHIR JSON spec and return
    logger.info("Output: %s", phir_output)
    return phir_output
