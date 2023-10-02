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
        self._pending_commands: dict[UnitID, list[Command]] = {}
        self._shards: list[Shard] = []
        print(f"Sharder created for circuit {self._circuit}")

    def shard(self) -> list[Shard]:
        """
        Performs the sharding algorithm on the circuit the Sharder was initialized
        with, returning the list of Shards needed to schedule
        """
        print("Sharding begins....")
        # https://cqcl.github.io/tket/pytket/api/circuit.html#pytket.circuit.Command
        for command in self._circuit.get_commands():
            self._process_command(command)
        self._cleanup_remaining_commands()

        print("Shard output:")
        for shard in self._shards:
            print(shard.pretty_print())
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
            self._add_pending_sub_command(command)

    def _build_shard(self, command: Command) -> None:
        """
        Creates a Shard object given the extant sharding context and the schedulable
        Command object passed in, and appends it to the Shard list
        """
        # Resolve any sub commands (SQ gates) that interact with the same qubits
        sub_commands: dict[UnitID, list[Command]] = {}
        for key in (
            key for key in list(self._pending_commands) if key in command.qubits
        ):
            sub_commands[key] = self._pending_commands.pop(key)

        # Handle dependency calculations
        depends_upon: set[int] = set()
        for shard in self._shards:
            # Check qubit dependencies (R/W implicitly) since all commands
            # on a given qubit need to be ordered as the circuit dictated
            if not shard.qubits_used.isdisjoint(command.qubits):
                depends_upon.add(shard.ID)
            # Check classical dependencies, which depend on writing and reading
            # hazards: RAW, WAW, WAR
            # TODO: Do it!

        shard = Shard(command, sub_commands, depends_upon)
        self._shards.append(shard)
        print("Appended shard:", shard)

    def _cleanup_remaining_commands(self) -> None:
        """
        Checks for any remaining "unsharded" commands, and if found, adds them
        to Barrier op shards for each qubit
        """
        remaining_qubits = [k for k, v in self._pending_commands.items() if v]
        for qubit in remaining_qubits:
            self._circuit.add_barrier([qubit])
            # Easiest way to get to a command, since there's no constructor. Could
            # create an entire orphan circuit with the matching qubits and the barrier
            # instead if this has unintended consequences
            barrier_command = self._circuit.get_commands()[-1]
            self._build_shard(barrier_command)

    def _add_pending_sub_command(self, command: Command) -> None:
        """
        Adds a pending sub command to the buffer to be flushed when a schedulable
        operation creates a Shard.
        """
        key = command.qubits[0]
        if key not in self._pending_commands:
            self._pending_commands[key] = []
        self._pending_commands[key].append(command)
        print(f"Adding pending command {command}")

    @staticmethod
    def should_op_create_shard(op: Op) -> bool:
        """
        Returns `True` if the operation is one that should result in shard creation.
        This includes non-gate operations like measure/reset as well as 2-qubit gates.
        TODO: This is almost certainly inadequate right now
        """
        return op.type in (OpType.Measure, OpType.Reset, OpType.Barrier) or (
            op.is_gate() and op.n_qubits > 1
        )
