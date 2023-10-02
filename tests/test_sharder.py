from typing import cast

from pytket.circuit import Conditional, Op, OpType
from pytket.phir.sharding.sharder import Sharder

from .sample_data import QasmFiles, get_qasm_as_circuit


class TestSharder:
    def test_should_op_create_shard(self) -> None:
        expected_true: list[Op] = [
            Op.create(OpType.Measure),  # type: ignore  # noqa: PGH003
            Op.create(OpType.Reset),  # type: ignore  # noqa: PGH003
            Op.create(OpType.CX),  # type: ignore  # noqa: PGH003
            Op.create(OpType.Barrier),  # type: ignore  # noqa: PGH003
        ]
        expected_false: list[Op] = [
            Op.create(OpType.U1, 0.32),  # type: ignore  # noqa: PGH003
            Op.create(OpType.H),  # type: ignore  # noqa: PGH003
            Op.create(OpType.Z),  # type: ignore  # noqa: PGH003
        ]

        for op in expected_true:
            assert Sharder.should_op_create_shard(op)
        for op in expected_false:
            assert not Sharder.should_op_create_shard(op)

    def test_with_baby_circuit(self) -> None:
        circuit = get_qasm_as_circuit(QasmFiles.baby)
        sharder = Sharder(circuit)
        shards = sharder.shard()

        assert len(shards) == 3

        assert shards[0].primary_command.op.type == OpType.CX
        assert len(shards[0].primary_command.qubits) == 2
        assert not shards[0].primary_command.bits
        assert len(shards[0].sub_commands) == 2
        sub_commands = list(shards[0].sub_commands.items())
        print(sub_commands)
        assert sub_commands[0][1][0].op.type == OpType.H
        assert len(shards[0].depends_upon) == 0

        assert shards[1].primary_command.op.type == OpType.Measure
        assert len(shards[1].sub_commands) == 0
        assert shards[1].depends_upon == {shards[0].ID}

        assert shards[2].primary_command.op.type == OpType.Measure
        assert len(shards[2].sub_commands) == 0
        assert shards[2].depends_upon == {shards[0].ID}

    def test_rollup_behavior(self) -> None:
        circuit = get_qasm_as_circuit(QasmFiles.baby_with_rollup)
        sharder = Sharder(circuit)
        shards = sharder.shard()

        assert len(shards) == 5

        assert shards[0].primary_command.op.type == OpType.CX
        assert len(shards[0].primary_command.qubits) == 2
        assert not shards[0].primary_command.bits
        assert len(shards[0].sub_commands) == 2
        sub_commands = list(shards[0].sub_commands.items())
        print(sub_commands)
        assert sub_commands[0][1][0].op.type == OpType.H
        assert len(shards[0].depends_upon) == 0

        assert shards[1].primary_command.op.type == OpType.Measure
        assert len(shards[1].sub_commands) == 0
        assert shards[1].depends_upon == {shards[0].ID}

        assert shards[2].primary_command.op.type == OpType.Measure
        assert len(shards[2].sub_commands) == 0
        assert shards[2].depends_upon == {shards[0].ID}

        assert shards[3].primary_command.op.type == OpType.Barrier
        assert len(shards[3].sub_commands) == 1
        assert shards[3].depends_upon == {shards[0].ID, shards[1].ID}

        assert shards[4].primary_command.op.type == OpType.Barrier
        assert len(shards[4].sub_commands) == 1
        assert shards[4].depends_upon == {shards[0].ID, shards[2].ID}

    def test_simple_conditional(self) -> None:
        circuit = get_qasm_as_circuit(QasmFiles.simple_cond)
        sharder = Sharder(circuit)
        shards = sharder.shard()

        assert len(shards) == 3

        assert shards[0].primary_command.op.type == OpType.Measure
        assert len(shards[0].sub_commands.items()) == 1
        s0_qubit, s0_sub_cmds = next(iter(shards[0].sub_commands.items()))
        assert s0_qubit == circuit.qubits[0]
        assert s0_sub_cmds[0].op.type == OpType.H

        assert shards[1].primary_command.op.type == OpType.Reset
        assert len(shards[1].sub_commands.items()) == 0

        assert shards[2].primary_command.op.type == OpType.Measure
        assert len(shards[2].sub_commands.items()) == 1
        s2_qubit, s2_sub_cmds = next(iter(shards[2].sub_commands.items()))
        assert s2_qubit == circuit.qubits[0]
        assert s2_sub_cmds[0].op.type == OpType.Conditional
        assert cast(Conditional, s2_sub_cmds[0].op).op.type == OpType.H
        assert s2_sub_cmds[0].qubits == [circuit.qubits[0]]
