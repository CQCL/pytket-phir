from pytket.circuit import Circuit

from .rebasing.rebaser import rebase_to_qtm_machine
from .sharding.sharder import Sharder


def pytket_to_phir(
    circuit: Circuit,
    qtm_machine: str | None = None,
) -> str:
    """Converts a pytket circuit into its PHIR representation.

    This can optionally include rebasing against a Quantinuum machine architecture.

    :param circuit: Circuit object to be converted
    :param qtm_machine: (Optional) Quantinuum machine architecture to rebase against

    Returns:
    -------
        PHIR JSON as a str
    """
    if qtm_machine:
        circuit = rebase_to_qtm_machine(circuit, qtm_machine)

    sharder = Sharder(circuit)
    shards = sharder.shard()

    # TODO: Pass shards[] into placement, routing, etc
    # TODO: Convert to PHIR JSON spec and return

    return str(shards)  # Just returning fake string for now
