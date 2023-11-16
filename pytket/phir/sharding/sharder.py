##############################################################################
#
# Copyright (c) 2023 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

import logging
from typing import cast

from pytket.circuit import Circuit, Command, Conditional, Op, OpType
from pytket.unit_id import Bit, UnitID

from .shard import Shard

NOT_IMPLEMENTED_OP_TYPES = [OpType.CircBox, OpType.WASM]

SHARD_TRIGGER_OP_TYPES = [
    OpType.Measure,
    OpType.Reset,
    OpType.Barrier,
    OpType.SetBits,
    OpType.ClassicalExpBox,  # some classical operations are rolled up into a box
    OpType.RangePredicate,
    OpType.ExplicitPredicate,
]

logger = logging.getLogger(__name__)


def _is_command_global_phase(command: Command) -> bool:
    return command.op.type == OpType.Phase or (
        command.op.type == OpType.Conditional
        and cast(Conditional, command.op).op.type == OpType.Phase
    )


class Sharder:
    """The Sharder class.

    Responsible for taking in a circuit in TKET representation
    and converting it into shards that can be subsequently handled in the
    compilation pipeline.
    """

    def __init__(self, circuit: Circuit) -> None:
        """Create Sharder object.

        Args:
        ----
            circuit: tket Circuit
        """
        self._circuit = circuit
        self._pending_commands: dict[UnitID, list[Command]] = {}
        self._shards: list[Shard] = []
        logger.debug("Sharder created for circuit %s", self._circuit)

    def shard(self) -> list[Shard]:
        """Performs sharding algorithm on the circuit the Sharder was initialized with.

        Returns:
        -------
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

        if _is_command_global_phase(command):
            logger.debug("Ignoring global Phase gate")
            return

        if self.should_op_create_shard(command.op):
            logger.debug("Building shard for command: %s", command)
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
        # Rollup any sub commands (SQ gates) that interact with the same qubits
        sub_commands: dict[UnitID, list[Command]] = {}
        for key in (
            key for key in list(self._pending_commands) if key in command.qubits
        ):
            sub_commands[key] = self._pending_commands.pop(key)

        all_commands = [command]
        for sub_command_list in sub_commands.values():
            all_commands.extend(sub_command_list)

        qubits_used = set(command.qubits)
        bits_written = set(command.bits)
        bits_read: set[Bit] = set()

        for sub_command in all_commands:
            bits_written.update(sub_command.bits)
            bits_read.update(
                set(filter(lambda x: isinstance(x, Bit), sub_command.args)),  # type: ignore [misc, arg-type]
            )

        # Handle dependency calculations
        depends_upon: set[int] = set()
        for shard in self._shards:
            # Check qubit dependencies (R/W implicitly) since all commands
            # on a given qubit need to be ordered as the circuit dictated
            if not shard.qubits_used.isdisjoint(command.qubits):
                logger.debug("...adding shard dep %s -> qubit overlap", shard.ID)
                depends_upon.add(shard.ID)
            # Check classical dependencies, which depend on writing and reading
            # hazards: RAW, WAW, WAR
            # NOTE: bits_read will include bits_written in the current impl

            # Check for write-after-write (changing order would change final value)
            # by looking at overlap of bits_written
            elif not shard.bits_written.isdisjoint(bits_written):
                logger.debug("...adding shard dep %s -> WAW", shard.ID)
                depends_upon.add(shard.ID)

            # Check for read-after-write (value seen would change if reordered)
            elif not shard.bits_written.isdisjoint(bits_read):
                logger.debug("...adding shard dep %s -> RAW", shard.ID)
                depends_upon.add(shard.ID)

            # Check for write-after-read (no reordering or read is changed)
            elif not shard.bits_written.isdisjoint(bits_read):
                logger.debug("...adding shard dep %s -> WAR", shard.ID)
                depends_upon.add(shard.ID)

        shard = Shard(
            command,
            sub_commands,
            qubits_used,
            bits_written,
            bits_read,
            depends_upon,
        )
        self._shards.append(shard)
        logger.debug("Appended shard: %s", shard)

    def _cleanup_remaining_commands(self) -> None:
        remaining_qubits = [k for k, v in self._pending_commands.items() if v]
        for qubit in remaining_qubits:
            self._circuit.add_barrier([qubit])
            # Easiest way to get to a command, since there's no constructor. Could
            # create an entire orphan circuit with the matching qubits and the barrier
            # instead if this has unintended consequences
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
        logger.debug("Adding pending command %s", command)

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
            op.type in (SHARD_TRIGGER_OP_TYPES)
            or (
                op.type == OpType.Conditional
                and cast(Conditional, op).op.type in (SHARD_TRIGGER_OP_TYPES)
            )
            or (op.is_gate() and op.n_qubits > 1)
        )
