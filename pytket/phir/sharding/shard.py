from dataclasses import dataclass

from pytket.circuit import Command
from pytket.unit_id import UnitID


@dataclass
class Shard:
    """
    A shard is a logical grouping of operations that represents the unit by which
    we actually do placement of qubits
    """

    # The schedulable command of the shard
    primary_command: Command

    # The other commands related to the primary schedulable command, stored
    # as a map of bit-handle (unitID) -> list[Command]
    sub_commands: dict[UnitID, list[Command]]

    # A set of the other shards this particular shard depends upon, and thus
    # must be scheduled after
    depends_upon: set["Shard"]
