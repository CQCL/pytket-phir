##############################################################################
#
# (c) 2023 @ Quantinuum LLC. All Rights Reserved.
# This software and all information and expression are the property of
# Quantinuum LLC, are Quantinuum LLC Confidential & Proprietary,
# contain trade secrets and may not, in whole or in part, be licensed,
# used, duplicated, disclosed, or reproduced for any purpose without prior
# written permission of Quantinuum LLC.
#
##############################################################################

from __future__ import annotations
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
    depends_upon: set[Shard]

    # def __init__(self, 
    #              primary_command: Command,
    #              sub_commands: dict[UnitID, list[Command]],
    #              depends_upon: set[Shard]) -> None:
        
    #     # The schedulable command of the shard
    #     self.primary_command = primary_command
        
    #     # The other commands related to the primary schedulable command, stored
    #     # as a map of bit handle (unitID) -> list[Command]
    #     self.sub_commands = sub_commands
        
    #     # A set of the other shards this particular shard depends upon, and thus
    #     # must be scheduled after
    #     self.depends_upon = depends_upon
    
