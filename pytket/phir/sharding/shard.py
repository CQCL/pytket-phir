##############################################################################
#
# Copyright (c) 2023 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

import io
from dataclasses import dataclass, field
from itertools import count
from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from pytket.circuit import Command
    from pytket.unit_id import Bit, Qubit, UnitID


@dataclass(frozen=True)
class Shard:
    """The Shard class.

    A shard is a logical grouping of operations that represents the unit by which
    we actually do placement of qubits.
    """

    # The unique identifier of the shard
    ID: int = field(default_factory=count().__next__, init=False)

    # The "schedulable" command of the shard
    primary_command: "Command"

    # The other commands related to the primary schedulable command, stored
    # as a map of bit-handle (unitID) -> list[Command]
    sub_commands: dict["UnitID", list["Command"]]

    # All qubits used by the primary and sub commands
    qubits_used: set["Qubit"]

    # Set of all classical bits written to by the primary and sub commands
    bits_written: set["Bit"]

    # Set of all classical bits read by the primary and sub commands
    bits_read: set["Bit"]

    # A set of the identifiers of other shards this particular shard depends upon
    depends_upon: set[int]

    def __hash__(self) -> int:
        """Hashing for shards is done only by its autogen unique int ID."""
        return self.ID

    def pretty_print(self) -> str:
        """Returns the shard in a human-friendly format."""
        output = io.StringIO()
        output.write(f"Shard {self.ID}:")
        output.write(f"\n   Command: {self.primary_command}")
        output.write("\n   Sub commands: ")
        if not self.sub_commands:
            output.write("[]")
        for sub in self.sub_commands:
            output.write(f"\n       {sub}: {self.sub_commands[sub]}")
        output.write(f"\n   Qubits used:  {self.qubits_used}")
        output.write(f"\n   Bits written: {self.bits_written}")
        output.write(f"\n   Bits read:    {self.bits_read}")
        output.write(f"\n   Depends upon: {self.depends_upon}")
        content = output.getvalue()
        output.close()
        return content


Cost: TypeAlias = float
ShardLayer: TypeAlias = list[Shard]
Ordering: TypeAlias = list[int]
