##############################################################################
#
# Copyright (c) 2023 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

from typing import cast

from pytket.circuit import Conditional, Op, OpType
from pytket.phir.sharding.sharder import Sharder

from .sample_data import QasmFile, get_qasm_as_circuit


class TestSharder:
    def test_shard_hashing(self) -> None:
        circuit = get_qasm_as_circuit(QasmFile.baby)
        sharder = Sharder(circuit)
        shards = sharder.shard()

        shard_set = set(shards)
        assert len(shard_set) == 3

        first_shard = next(iter(shard_set))
        shard_set.add(first_shard)
        assert len(shard_set) == 3

    def test_should_op_create_shard(self) -> None:
        expected_true: list[Op] = [
            Op.create(OpType.Measure),
            Op.create(OpType.Reset),
            Op.create(OpType.CX),
            Op.create(OpType.Barrier),
        ]
        expected_false: list[Op] = [
            Op.create(OpType.U1, 0.32),
            Op.create(OpType.H),
            Op.create(OpType.Z),
        ]

        for op in expected_true:
            assert Sharder.should_op_create_shard(op)
        for op in expected_false:
            assert not Sharder.should_op_create_shard(op)

    def test_with_baby_circuit(self) -> None:
        circuit = get_qasm_as_circuit(QasmFile.baby)
        sharder = Sharder(circuit)
        shards = sharder.shard()

        assert len(shards) == 3

        assert shards[0].primary_command.op.type == OpType.CX
        assert len(shards[0].primary_command.qubits) == 2
        assert not shards[0].primary_command.bits
        assert len(shards[0].sub_commands) == 2
        sub_commands = list(shards[0].sub_commands.items())
        assert sub_commands[0][1][0].op.type == OpType.H
        assert len(shards[0].depends_upon) == 0

        assert shards[1].primary_command.op.type == OpType.Measure
        assert len(shards[1].sub_commands) == 0
        assert shards[1].depends_upon == {shards[0].ID}

        assert shards[2].primary_command.op.type == OpType.Measure
        assert len(shards[2].sub_commands) == 0
        assert shards[2].depends_upon == {shards[0].ID}

    def test_rollup_behavior(self) -> None:
        circuit = get_qasm_as_circuit(QasmFile.baby_with_rollup)
        sharder = Sharder(circuit)
        shards = sharder.shard()

        assert len(shards) == 5

        assert shards[0].primary_command.op.type == OpType.CX
        assert len(shards[0].primary_command.qubits) == 2
        assert not shards[0].primary_command.bits
        assert len(shards[0].sub_commands) == 2
        sub_commands = list(shards[0].sub_commands.items())
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
        circuit = get_qasm_as_circuit(QasmFile.simple_cond)
        sharder = Sharder(circuit)
        shards = sharder.shard()

        assert len(shards) == 4

        # shard 0: [h q;] measure q->c;
        assert shards[0].primary_command.op.type == OpType.Measure
        assert shards[0].qubits_used == {circuit.qubits[0]}
        assert shards[0].bits_written == {circuit.bits[0]}
        assert shards[0].depends_upon == set()
        assert len(shards[0].sub_commands.items()) == 1
        s0_qubit, s0_sub_cmds = next(iter(shards[0].sub_commands.items()))
        assert s0_qubit == circuit.qubits[0]
        assert s0_sub_cmds[0].op.type == OpType.H

        # shard 1: reset q;
        assert shards[1].primary_command.op.type == OpType.Reset
        assert len(shards[1].sub_commands.items()) == 0
        assert shards[1].qubits_used == {circuit.qubits[0]}
        assert shards[1].depends_upon == {shards[0].ID}
        assert shards[1].bits_written == set()
        assert shards[1].bits_read == set()

        # shard 2: if (c==1) z=1;
        assert shards[2].primary_command.op.type == OpType.Conditional
        assert cast(Conditional, shards[2].primary_command.op).op.type == OpType.SetBits
        assert len(shards[2].sub_commands.keys()) == 0
        assert shards[2].qubits_used == set()
        assert shards[2].bits_written == {circuit.bits[1]}
        assert shards[2].bits_read == {circuit.bits[0], circuit.bits[1]}
        assert shards[2].depends_upon == {shards[0].ID}

        # shard 3: [if (c==1) h q;] measure q->c;
        assert shards[3].primary_command.op.type == OpType.Measure
        assert shards[3].qubits_used == {circuit.qubits[0]}
        assert shards[3].bits_written == {circuit.bits[0]}
        assert shards[3].bits_read == {circuit.bits[0]}
        assert shards[3].depends_upon == {shards[0].ID, shards[1].ID}
        assert len(shards[3].sub_commands.items()) == 1
        s2_qubit, s2_sub_cmds = next(iter(shards[3].sub_commands.items()))
        assert s2_qubit == circuit.qubits[0]
        assert s2_sub_cmds[0].op.type == OpType.Conditional
        assert cast(Conditional, s2_sub_cmds[0].op).op.type == OpType.H
        assert s2_sub_cmds[0].qubits == [circuit.qubits[0]]

    def test_complex_barriers(self) -> None:  # noqa: PLR0915
        circuit = get_qasm_as_circuit(QasmFile.barrier_complex)
        sharder = Sharder(circuit)
        shards = sharder.shard()

        assert len(shards) == 7

        # shard 0: [], c[3] = 1
        assert shards[0].primary_command.op.type == OpType.SetBits
        assert len(shards[0].sub_commands.items()) == 0
        assert shards[0].qubits_used == set()
        assert shards[0].bits_written == {circuit.bits[3]}
        assert shards[0].bits_read == {circuit.bits[3]}  # bits written are always read
        assert shards[0].depends_upon == set()

        # shard 1: [h q[0]; h q[1];] barrier q[0], q[1], c[3];
        assert shards[1].primary_command.op.type == OpType.Barrier
        assert len(shards[1].sub_commands.items()) == 2
        shard_1_q0_cmds = shards[1].sub_commands[circuit.qubits[0]]
        assert len(shard_1_q0_cmds) == 1
        assert shard_1_q0_cmds[0].op.type == OpType.H
        assert shard_1_q0_cmds[0].qubits == [circuit.qubits[0]]
        shard_1_q1_cmds = shards[1].sub_commands[circuit.qubits[1]]
        assert len(shard_1_q1_cmds) == 1
        assert shard_1_q1_cmds[0].op.type == OpType.H
        assert shard_1_q1_cmds[0].qubits == [circuit.qubits[1]]
        assert shards[1].qubits_used == {circuit.qubits[0], circuit.qubits[1]}
        assert shards[1].bits_written == {circuit.bits[3]}
        assert shards[1].bits_read == {circuit.bits[3]}
        assert shards[1].depends_upon == {shards[0].ID}

        # shard 2: [] CX q[0], q[1];
        assert shards[2].primary_command.op.type == OpType.CX
        assert len(shards[2].sub_commands.items()) == 0
        assert shards[2].qubits_used == {circuit.qubits[0], circuit.qubits[1]}
        assert shards[2].bits_written == set()
        assert shards[2].bits_read == set()
        assert shards[2].depends_upon == {shards[1].ID}

        # shard 3: measure q[0]->c[0];
        assert shards[3].primary_command.op.type == OpType.Measure
        assert len(shards[3].sub_commands.items()) == 0
        assert shards[3].qubits_used == {circuit.qubits[0]}
        assert shards[3].bits_written == {circuit.bits[0]}
        assert shards[3].bits_read == {circuit.bits[0]}
        assert shards[3].depends_upon == {shards[2].ID, shards[1].ID}

        # shard 4: [H q[3];, H q[3];, X q[3];]] barrier q[2], q[3];
        assert shards[4].primary_command.op.type == OpType.Barrier
        assert len(shards[4].sub_commands.items()) == 2
        shard_4_q2_cmds = shards[4].sub_commands[circuit.qubits[2]]
        assert len(shard_4_q2_cmds) == 2
        assert shard_4_q2_cmds[0].op.type == OpType.H
        assert shard_4_q2_cmds[0].qubits == [circuit.qubits[2]]
        assert shard_4_q2_cmds[1].op.type == OpType.H
        assert shard_4_q2_cmds[1].qubits == [circuit.qubits[2]]
        shard_4_q3_cmds = shards[4].sub_commands[circuit.qubits[3]]
        assert len(shard_4_q3_cmds) == 3
        assert shard_4_q3_cmds[0].op.type == OpType.H
        assert shard_4_q3_cmds[0].qubits == [circuit.qubits[3]]
        assert shard_4_q3_cmds[1].op.type == OpType.H
        assert shard_4_q3_cmds[1].qubits == [circuit.qubits[3]]
        assert shard_4_q3_cmds[2].op.type == OpType.X
        assert shard_4_q3_cmds[2].qubits == [circuit.qubits[3]]
        assert shards[4].qubits_used == {circuit.qubits[2], circuit.qubits[3]}
        assert shards[4].bits_written == set()
        assert shards[4].bits_read == set()
        assert shards[4].depends_upon == set()

        # shard 5: [] CX q[2], q[3];
        assert shards[5].primary_command.op.type == OpType.CX
        assert len(shards[5].sub_commands.items()) == 0
        assert shards[5].qubits_used == {circuit.qubits[2], circuit.qubits[3]}
        assert shards[5].bits_written == set()
        assert shards[5].bits_read == set()
        assert shards[5].depends_upon == {shards[4].ID}

        # shard 6: measure q[2]->c[2];
        assert shards[6].primary_command.op.type == OpType.Measure
        assert len(shards[6].sub_commands.items()) == 0
        assert shards[6].qubits_used == {circuit.qubits[2]}
        assert shards[6].bits_written == {circuit.bits[2]}
        assert shards[6].bits_read == {circuit.bits[2]}
        assert shards[6].depends_upon == {shards[5].ID, shards[4].ID}

    def test_classical_hazards(self) -> None:
        circuit = get_qasm_as_circuit(QasmFile.classical_hazards)
        sharder = Sharder(circuit)
        shards = sharder.shard()

        assert len(shards) == 5

        # shard 0: [h q[0];] measure q[0]->c[0];
        assert shards[0].primary_command.op.type == OpType.Measure
        assert len(shards[0].sub_commands.items()) == 1
        assert shards[0].qubits_used == {circuit.qubits[0]}
        assert shards[0].bits_written == {circuit.bits[0]}
        assert shards[0].bits_read == {circuit.bits[0]}
        assert shards[0].depends_upon == set()

        # shard 1: [H q[1];] measure q[1]->c[2];
        # NOTE: pytket reorganizes circuits to be efficiently ordered
        assert shards[1].primary_command.op.type == OpType.Measure
        assert len(shards[1].sub_commands.items()) == 1
        assert shards[1].qubits_used == {circuit.qubits[1]}
        assert shards[1].bits_written == {circuit.bits[2]}
        assert shards[1].bits_read == {circuit.bits[2]}
        assert shards[1].depends_upon == set()

        # shard 2: [] if(c[0]==1) c[1]=1;
        assert shards[2].primary_command.op.type == OpType.Conditional
        assert len(shards[2].sub_commands) == 0
        assert shards[2].qubits_used == set()
        assert shards[2].bits_written == {circuit.bits[1]}
        assert shards[2].bits_read == {circuit.bits[1], circuit.bits[0]}
        assert shards[2].depends_upon == {shards[0].ID}

        # shard 3: [] c[0]=0;
        assert shards[3].primary_command.op.type == OpType.SetBits
        assert len(shards[2].sub_commands) == 0
        assert shards[3].qubits_used == set()
        assert shards[3].bits_written == {circuit.bits[0]}
        assert shards[3].bits_read == {circuit.bits[0]}
        assert shards[3].depends_upon == {shards[0].ID}

        # shard 4: [] if(c[2]==1) c[0]=1;
        assert shards[4].primary_command.op.type == OpType.Conditional
        assert len(shards[4].sub_commands) == 0
        assert shards[4].qubits_used == set()
        assert shards[4].bits_written == {circuit.bits[0]}
        assert shards[4].bits_read == {circuit.bits[0], circuit.bits[2]}
        assert shards[4].depends_upon == {shards[1].ID, shards[0].ID, shards[3].ID}

    def test_with_big_gate(self) -> None:
        circuit = get_qasm_as_circuit(QasmFile.big_gate)
        sharder = Sharder(circuit)
        shards = sharder.shard()

        assert len(shards) == 2

        # shard 0: [h q[0]; h q[1]; h q[2];] c4x q[0],q[1],q[2],q[3];
        assert shards[0].primary_command.op.type == OpType.CnX
        assert len(shards[0].sub_commands) == 3
        assert shards[0].qubits_used == {
            circuit.qubits[0],
            circuit.qubits[1],
            circuit.qubits[2],
            circuit.qubits[3],
        }
        assert shards[0].bits_written == set()

        # shard 1: [] measure q[3]->[c0]
        assert shards[1].primary_command.op.type == OpType.Measure
        assert len(shards[1].sub_commands) == 0
        assert shards[1].qubits_used == {circuit.qubits[3]}
        assert shards[1].bits_written == {circuit.bits[0]}
