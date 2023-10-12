from pytket.circuit import Circuit

from .sharding.sharder import Sharder


def pytket_to_phir(
    circuit: Circuit,
) -> str:
    """Converts a pytket circuit into its PHIR representation.

    :param circuit: Circuit object to be converted
    """
    # TODO: Process circuit according to desired machine architecture

    sharder = Sharder(circuit)
    shards = sharder.shard()  # noqa: F841

    # TODO: Pass shards[] into placement, routing, etc
    # TODO: Convert to PHIR JSON spec and return

    return "{ phir json, someday }"
