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

from pytket import Circuit
from pytket.circuit import Command, Op, OpType
from pytket._tket.unit_id import UnitID

from .shard import Shard

NOT_IMPLEMENTED_OP_TYPES = [OpType.CircBox, OpType.WASM]

class Sharder:
    """
    The sharder class is responsible for taking in a circuit in TKET representation
    and converting it into shards that can be subsequently handled in the 
    compilation pipeline.
    """

    def __init__(self, circuit: Circuit) -> None:
        self._circuit = circuit
        print(f'Sharder created for circuit {self._circuit}')
        self._pending_commands: dict[UnitID, list[Command]] = {}
        self._shards: list[Shard] = []

    def shard(self) -> list[Shard]:
        print('Sharding begins....')
        # https://cqcl.github.io/tket/pytket/api/circuit.html#pytket.circuit.Command
        
        for command in self._circuit.get_commands():
            self._process_command(command)
        return self._shards
    
    def _process_command(self, command: Command) -> None:
        print('Processing command: ', command.op, command.op.type, command.args)
        if command.op.type in NOT_IMPLEMENTED_OP_TYPES:
            raise NotImplementedError(f'OpType {command.op.type} not supported!')
        
        if self._is_op_schedulable(command.op):
            print(f'Scheduling command: {command}')
            self._build_shard(command)
        else:
            self._add_pending_command(command)


    def _build_shard(self, command: Command) -> None:
        shard = Shard(command, 
                      {}, 
                      [])
        # TODO: Add sub operations
        self._shards.append(shard)
        print('Appended shard: ', shard)

    def _add_pending_command(self, command: Command) -> None:
        #if command.
        pass

    def _is_op_schedulable(self, op: Op) -> bool:
        return (
            op.type == OpType.Measure
            or op.type == OpType.Reset
            or (op.is_gate() and op.n_qubits > 1)
            )