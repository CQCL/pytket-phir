from pytket.circuit import Circuit, Command, Op, OpType
from pytket.unit_id import UnitID

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
        print(f"Sharder created for circuit {self._circuit}")
        self._pending_commands: dict[UnitID, list[Command]] = {}
        self._shards: list[Shard] = []

    def shard(self) -> list[Shard]:
        """
        Performs the sharding algorithm on the circuit the Sharder was initialized
        with, returning the list of Shards needed to schedule
        """
        print("Sharding begins....")
        # https://cqcl.github.io/tket/pytket/api/circuit.html#pytket.circuit.Command
        for command in self._circuit.get_commands():
            self._process_command(command)
        return self._shards

    def _process_command(self, command: Command) -> None:
        """
        Handles a given TKET command (operation, bits, etc) according to the type
        and the extant context within the Sharder
        """
        print("Processing command: ", command.op, command.op.type, command.args)
        if command.op.type in NOT_IMPLEMENTED_OP_TYPES:
            msg = f"OpType {command.op.type} not supported!"
            raise NotImplementedError(msg)

        if self.should_op_create_shard(command.op):
            print(f"Building shard for command: {command}")
            self._build_shard(command)
        else:
            self._add_pending_command(command)

    def _build_shard(self, command: Command) -> None:
        """
        Creates a Shard object given the extant sharding context and the schedulable
        Command object passed in, and appends it to the Shard list
        """
        shard = Shard(command, self._pending_commands, set())
        # TODO: Dependencies!
        self._pending_commands = {}
        self._shards.append(shard)
        print("Appended shard:", shard)

    def _add_pending_command(self, command: Command) -> None:
        """
        Adds a pending sub command to the buffer to be flushed when a schedulable
        operation creates a Shard.
        """
        # TODO: Need to make sure 'args[0]' is the right key to use.
        if command.args[0] not in self._pending_commands:
            self._pending_commands[command.args[0]] = []
        self._pending_commands[command.args[0]].append(command)

    @staticmethod
    def should_op_create_shard(op: Op) -> bool:
        """
        Returns `True` if the operation is one that should result in shard creation.
        This includes non-gate operations like measure/reset as well as 2-qubit gates.
        """
        # TODO: This is almost certainly inadequate right now
        return (
            op.type == OpType.Measure
            or op.type == OpType.Reset
            or (op.is_gate() and op.n_qubits > 1)
        )
