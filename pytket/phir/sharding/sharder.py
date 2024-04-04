##############################################################################
#
# Copyright (c) 2023 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

import logging

from pytket.circuit import Circuit, Command, Conditional, Op, OpType
from pytket.unit_id import Bit, Qubit, UnitID

from .shard import Shard

NOT_IMPLEMENTED_OP_TYPES = [OpType.CircBox]

SHARD_TRIGGER_OP_TYPES = [
    OpType.Measure,
    OpType.Reset,
    OpType.Barrier,
    OpType.SetBits,
    OpType.ClassicalExpBox,  # some classical operations are rolled up into a box
    OpType.RangePredicate,
    OpType.ExplicitPredicate,
    OpType.ExplicitModifier,
    OpType.MultiBit,
    OpType.CopyBits,
    OpType.WASM,
]

logger = logging.getLogger(__name__)


class Sharder:
    """The Sharder class.

    Responsible for taking in a circuit in TKET representation
    and converting it into shards that can be subsequently handled in the
    compilation pipeline.
    """

    def __init__(self, circuit: Circuit) -> None:
        """Create Sharder object.

        Args:
            circuit: tket Circuit
        """
        self._circuit = circuit
        self._pending_commands: dict[UnitID, list[Command]] = {}
        self._shards: list[Shard] = []
        # These dictionaries map qubits/bits to the last shard that modified them
        self._qubit_touched_by: dict[UnitID, int] = {}
        self._bit_read_by: dict[UnitID, int] = {}
        self._bit_written_by: dict[UnitID, int] = {}

        logger.debug("Sharder created for circuit %s", self._circuit)

    def shard(self) -> list[Shard]:
        """Performs sharding algorithm on the circuit the Sharder was initialized with.

        Returns:
            list of Shards needed to schedule
        """
        logger.debug("Sharding beginning")
        commands = self._circuit.get_commands()

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("All commands:")
            for command in commands:
                logger.debug(command)

        for command in commands:
            self._process_command(command)
        self._cleanup_remaining_commands()

        logger.debug("Shard output:")
        for shard in self._shards:
            logger.debug(shard)
        return self._shards

    def _process_command(self, command: Command) -> None:
        """Handles a command per the type and the extant context within the Sharder.

        Args:
            command: tket command (operation, bits, etc)
        """
        logger.debug(
            "Processing command: %s of type %s with args: %s",
            command.op,
            command.op.type,
            command.args,
        )
        if command.op.type in NOT_IMPLEMENTED_OP_TYPES:
            msg = f"OpType {command.op.type} not supported!"
            raise NotImplementedError(msg)

        if Sharder._is_command_global_phase(command):
            logger.debug("Ignoring global Phase gate")
            return

        if Sharder.should_op_create_shard(command.op):
            self._build_shard(command)
        else:
            self._add_pending_sub_command(command)

    def _build_shard(self, command: Command) -> None:
        """Builds a shard.

        Creates a Shard object given the extant sharding context and the schedulable
        Command object passed in, and appends it to the Shard list.

        Args:
            command: tket command (operation, bits, etc)
        """
        logger.debug("Building shard for command: %s", command)
        # Rollup any sub commands (SQ gates) that interact with the same qubits
        sub_commands: dict[UnitID, list[Command]] = {}
        for key in (
            key for key in list(self._pending_commands) if key in command.qubits
        ):
            sub_commands[key] = self._pending_commands.pop(key)

        all_commands = [command]
        for sub_command_list in sub_commands.values():
            all_commands.extend(sub_command_list)

        logger.debug("All shard commands: %s", all_commands)
        qubits_used = set(command.qubits)
        bits_written = set(command.bits)
        bits_read: set[Bit] = set()

        for sub_command in all_commands:
            bits_written.update(sub_command.bits)
            bits_read.update(
                set(filter(lambda x: isinstance(x, Bit), sub_command.args)),  # type: ignore [misc, arg-type]
            )

        # Handle dependency calculations
        depends_upon = self._resolve_shard_dependencies(
            qubits_used, bits_written, bits_read
        )

        shard = Shard(
            command,
            sub_commands,
            qubits_used,
            bits_written,
            bits_read,
            depends_upon,
        )

        self._mark_dependencies(shard)

        self._shards.append(shard)
        logger.debug("Appended shard: %s", shard)

    def _resolve_shard_dependencies(
        self, qubits: set[Qubit], bits_written: set[Bit], bits_read: set[Bit]
    ) -> set[int]:
        """Finds the dependent shards for a given shard.

        This involves checking for qubit interaction and classical hazards of
        various types.

        Args:
            shard: Shard to run dependency calculation on
            qubits: Set of all qubits interacted with in the command/sub-commands
            bits_written: Classical bits the command/sub-commands write to
            bits_read: Classical bits the command/sub-commands read from
        """
        logger.debug(
            "Resolving shard dependencies with qubits=%s bits_written=%s bits_read=%s",
            qubits,
            bits_written,
            bits_read,
        )

        depends_upon: set[int] = set()

        for qubit in qubits:
            if qubit in self._qubit_touched_by:
                logger.debug(
                    "...adding shard dep %s -> qubit overlap",
                    self._qubit_touched_by[qubit],
                )
                depends_upon.add(self._qubit_touched_by[qubit])

        for bit_read in bits_read:
            if bit_read in self._bit_written_by:
                logger.debug(
                    "...adding shard dep %s -> RAW", self._bit_written_by[bit_read]
                )
                depends_upon.add(self._bit_written_by[bit_read])

        for bit_written in bits_written:
            if bit_written in self._bit_written_by:
                logger.debug(
                    "...adding shard dep %s -> WAW", self._bit_written_by[bit_written]
                )
                depends_upon.add(self._bit_written_by[bit_written])
            if bit_written in self._bit_read_by:
                logger.debug(
                    "...adding shard dep %s -> WAR", self._bit_read_by[bit_written]
                )
                depends_upon.add(self._bit_read_by[bit_written])

        return depends_upon

    def _mark_dependencies(
        self,
        shard: Shard,
    ) -> None:
        """Marks (updates) the dependency maps.

        This allows subsequent shard dependency resolution to have the right
        state of everything, updating the shards

        Args:
            shard: Shard to be updated
        """
        for qubit in shard.qubits_used:
            self._qubit_touched_by[qubit] = shard.ID
        for bit in shard.bits_written:
            self._bit_written_by[bit] = shard.ID
        for bit in shard.bits_read:
            self._bit_read_by[bit] = shard.ID
        logger.debug("... dependencies marked")

    def _cleanup_remaining_commands(self) -> None:
        """Cleans up any remaining subcommands.

        This is done by creating a superfluous Barrier command that serves just
        to roll up lingering subcommands.
        """
        remaining_qubits = [k for k, v in self._pending_commands.items() if v]
        logger.debug(
            "Cleaning up remaining subcommands for qubits %s", remaining_qubits
        )
        for qubit in remaining_qubits:
            logger.debug("Adding barrier for subcommands for qubit %s", qubit)
            self._circuit.add_barrier([qubit])
            # Easiest way to get to a command, since there's no constructor. Could
            # create an entire orphan circuit with the matching qubits and the barrier
            # instead, if this has unintended consequences
            barrier_command = self._circuit.get_commands()[-1]
            self._build_shard(barrier_command)

    def _add_pending_sub_command(self, command: Command) -> None:
        """Adds a pending command.

        Adds a pending sub command to the buffer to be flushed when a schedulable
        operation creates a Shard.

        Args:
            command:  tket command (operation, bits, etc)
        """
        qubit_key = command.qubits[0]
        if qubit_key not in self._pending_commands:
            self._pending_commands[qubit_key] = []
        self._pending_commands[qubit_key].append(command)
        logger.debug("Added pending sub-command %s", command)

    @staticmethod
    def should_op_create_shard(op: Op) -> bool:
        """Decide whether to create a shard.

        This includes non-gate operations like measure/reset as well as 2-qubit gates.

        Args:
            op: operation

        Returns:
            `True` if the operation is one that should result in shard creation
        """
        return (
            op.type in SHARD_TRIGGER_OP_TYPES
            or isinstance(op, Conditional)
            or (op.is_gate() and op.n_qubits > 1)
        )

    @staticmethod
    def _is_command_global_phase(command: Command) -> bool:
        """Check if an operation related to global phase.

        Args:
            command: Command to evaluate
        """
        return command.op.type == OpType.Phase or (
            isinstance(command.op, Conditional) and command.op.op.type == OpType.Phase
        )
