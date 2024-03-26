##############################################################################
#
# Copyright (c) 2023 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

from pytket.circuit import Conditional, Op, OpType
from pytket.phir.sharding.sharder import Sharder

from .test_utils import QasmFile, get_qasm_as_circuit


class TestSharder:
    def test_shard_hashing(self) -> None:
        circuit = get_qasm_as_circuit(QasmFile.baby)
        shards = Sharder(circuit).shard()

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
        shards = Sharder(circuit).shard()

        assert len(shards) == 3

        assert shards[0].primary_command.op.type == OpType.CX
        assert len(shards[0].primary_command.qubits) == 2
        assert not shards[0].primary_command.bits
        assert len(shards[0].sub_commands) == 2
        sub_commands = list(shards[0].sub_commands.items())
        assert sub_commands[0][1][0].op.type == OpType.H
        assert not shards[0].depends_upon

        assert shards[1].primary_command.op.type == OpType.Measure
        assert not shards[1].sub_commands
        assert shards[1].depends_upon == {shards[0].ID}

        assert shards[2].primary_command.op.type == OpType.Measure
        assert not shards[2].sub_commands
        assert shards[2].depends_upon == {shards[0].ID}

    def test_rollup_behavior(self) -> None:
        circuit = get_qasm_as_circuit(QasmFile.baby_with_rollup)
        shards = Sharder(circuit).shard()

        assert len(shards) == 5

        # Shard 0: CX gate, with 2 hadamard subcommands
        assert shards[0].primary_command.op.type == OpType.CX
        assert len(shards[0].primary_command.qubits) == 2
        assert not shards[0].primary_command.bits
        assert len(shards[0].sub_commands) == 2
        sub_commands = list(shards[0].sub_commands.items())
        assert sub_commands[0][1][0].op.type == OpType.H
        assert not shards[0].depends_upon

        # Shard 1: Measure q[0] -> c[0] (TKET splits q->c)
        assert shards[1].primary_command.op.type == OpType.Measure
        assert not shards[1].sub_commands
        assert shards[1].depends_upon == {shards[0].ID}

        # shard 2: Measure q[1] -> c[1]
        assert shards[2].primary_command.op.type == OpType.Measure
        assert not shards[2].sub_commands
        assert shards[2].depends_upon == {shards[0].ID}

        # Shard 3: Rollup barrier for a lingering hadamard on q[0]
        assert shards[3].primary_command.op.type == OpType.Barrier
        assert len(shards[3].sub_commands) == 1
        assert shards[3].depends_upon == {shards[1].ID}

        # Shard 4: Rollup barrier for second lingering hadamard on q[1]
        assert shards[4].primary_command.op.type == OpType.Barrier
        assert len(shards[4].sub_commands) == 1
        assert shards[4].depends_upon == {shards[2].ID}

    def test_simple_conditional(self) -> None:
        circuit = get_qasm_as_circuit(QasmFile.simple_cond)
        shards = Sharder(circuit).shard()

        assert len(shards) == 5

        # shard 0: [h q;] measure q->c;
        assert shards[0].primary_command.op.type == OpType.Measure
        assert shards[0].qubits_used == {circuit.qubits[0]}
        assert shards[0].bits_written == {circuit.bits[0]}
        assert not shards[0].depends_upon
        assert len(shards[0].sub_commands.items()) == 1
        s0_qubit, s0_sub_cmds = next(iter(shards[0].sub_commands.items()))
        assert s0_qubit == circuit.qubits[0]
        assert s0_sub_cmds[0].op.type == OpType.H

        # shard 1: reset q;
        assert shards[1].primary_command.op.type == OpType.Reset
        assert len(shards[1].sub_commands.items()) == 0
        assert shards[1].qubits_used == {circuit.qubits[0]}
        assert shards[1].depends_upon == {shards[0].ID}
        assert not shards[1].bits_written
        assert not shards[1].bits_read

        # shard 2: if (c==1) z=1;
        assert isinstance(shards[2].primary_command.op, Conditional)
        assert shards[2].primary_command.op.op.type == OpType.SetBits
        assert not shards[2].sub_commands
        assert not shards[2].qubits_used
        assert shards[2].bits_written == {circuit.bits[1]}
        assert shards[2].bits_read == {circuit.bits[0], circuit.bits[1]}
        assert shards[2].depends_upon == {shards[0].ID}

        # shard 3: [if (c==1) h q;]
        assert isinstance(shards[3].primary_command.op, Conditional)
        assert shards[3].primary_command.op.op.type == OpType.H
        assert not shards[3].sub_commands
        assert shards[3].qubits_used == {circuit.qubits[0]}
        assert shards[3].bits_read == {circuit.bits[0]}
        assert shards[3].depends_upon == {shards[0].ID, shards[1].ID}

        # shard 4: measure q->c;
        assert shards[4].primary_command.op.type == OpType.Measure
        assert not shards[4].sub_commands
        assert shards[4].qubits_used == {circuit.qubits[0]}
        assert shards[4].bits_written == {circuit.bits[0]}
        assert shards[4].depends_upon == {shards[0].ID, shards[3].ID}

    def test_complex_barriers(self) -> None:  # noqa: PLR0915
        circuit = get_qasm_as_circuit(QasmFile.barrier_complex)
        shards = Sharder(circuit).shard()

        assert len(shards) == 7

        # shard 0: [], c[3] = 1
        assert shards[0].primary_command.op.type == OpType.SetBits
        assert len(shards[0].sub_commands.items()) == 0
        assert not shards[0].qubits_used
        assert shards[0].bits_written == {circuit.bits[3]}
        assert shards[0].bits_read == {circuit.bits[3]}  # bits written are always read
        assert not shards[0].depends_upon

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
        assert not shards[2].bits_written
        assert not shards[2].bits_read
        assert shards[2].depends_upon == {shards[1].ID}

        # shard 3: measure q[0]->c[0];
        assert shards[3].primary_command.op.type == OpType.Measure
        assert len(shards[3].sub_commands.items()) == 0
        assert shards[3].qubits_used == {circuit.qubits[0]}
        assert shards[3].bits_written == {circuit.bits[0]}
        assert shards[3].bits_read == {circuit.bits[0]}
        assert shards[3].depends_upon == {shards[2].ID}

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
        assert not shards[4].bits_written
        assert not shards[4].bits_read
        assert not shards[4].depends_upon

        # shard 5: [] CX q[2], q[3];
        assert shards[5].primary_command.op.type == OpType.CX
        assert len(shards[5].sub_commands.items()) == 0
        assert shards[5].qubits_used == {circuit.qubits[2], circuit.qubits[3]}
        assert not shards[5].bits_written
        assert not shards[5].bits_read
        assert shards[5].depends_upon == {shards[4].ID}

        # shard 6: measure q[2]->c[2];
        assert shards[6].primary_command.op.type == OpType.Measure
        assert len(shards[6].sub_commands.items()) == 0
        assert shards[6].qubits_used == {circuit.qubits[2]}
        assert shards[6].bits_written == {circuit.bits[2]}
        assert shards[6].bits_read == {circuit.bits[2]}
        assert shards[6].depends_upon == {shards[5].ID}

    def test_classical_hazards(self) -> None:
        circuit = get_qasm_as_circuit(QasmFile.classical_hazards)
        shards = Sharder(circuit).shard()

        assert len(shards) == 5

        # shard 0: [h q[0];] measure q[0]->c[0];
        assert shards[0].primary_command.op.type == OpType.Measure
        assert len(shards[0].sub_commands.items()) == 1
        assert shards[0].qubits_used == {circuit.qubits[0]}
        assert shards[0].bits_written == {circuit.bits[0]}
        assert shards[0].bits_read == {circuit.bits[0]}
        assert not shards[0].depends_upon

        # shard 1: [H q[1];] measure q[1]->c[2];
        # NOTE: pytket reorganizes circuits to be efficiently ordered
        assert shards[1].primary_command.op.type == OpType.Measure
        assert len(shards[1].sub_commands.items()) == 1
        assert shards[1].qubits_used == {circuit.qubits[1]}
        assert shards[1].bits_written == {circuit.bits[2]}
        assert shards[1].bits_read == {circuit.bits[2]}
        assert not shards[1].depends_upon

        # shard 2: [] if(c[0]==1) c[1]=1;
        assert shards[2].primary_command.op.type == OpType.Conditional
        assert not shards[2].sub_commands
        assert not shards[2].qubits_used
        assert shards[2].bits_written == {circuit.bits[1]}
        assert shards[2].bits_read == {circuit.bits[1], circuit.bits[0]}
        assert shards[2].depends_upon == {shards[0].ID}

        # shard 3: [] c[0]=0;
        assert shards[3].primary_command.op.type == OpType.SetBits
        assert not shards[2].sub_commands
        assert not shards[3].qubits_used
        assert shards[3].bits_written == {circuit.bits[0]}
        assert shards[3].bits_read == {circuit.bits[0]}
        assert shards[3].depends_upon == {shards[0].ID, shards[2].ID}

        # shard 4: [] if(c[2]==1) c[0]=1;
        assert shards[4].primary_command.op.type == OpType.Conditional
        assert not shards[4].sub_commands
        assert not shards[4].qubits_used
        assert shards[4].bits_written == {circuit.bits[0]}
        assert shards[4].bits_read == {circuit.bits[0], circuit.bits[2]}
        assert shards[4].depends_upon == {shards[1].ID, shards[3].ID}

    def test_with_big_gate(self) -> None:
        circuit = get_qasm_as_circuit(QasmFile.big_gate)
        shards = Sharder(circuit).shard()

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
        assert not shards[0].bits_written

        # shard 1: [] measure q[3]->[c0]
        assert shards[1].primary_command.op.type == OpType.Measure
        assert not shards[1].sub_commands
        assert shards[1].qubits_used == {circuit.qubits[3]}
        assert shards[1].bits_written == {circuit.bits[0]}

    def test_classical_ordering_breaking_circuit(self) -> None:
        circuit = get_qasm_as_circuit(QasmFile.classical_ordering)
        shards = Sharder(circuit).shard()

        assert len(shards) == 4

        # shard 0
        assert shards[0].primary_command.op.type == OpType.SetBits
        assert len(shards[0].sub_commands.items()) == 0
        assert not shards[0].qubits_used
        assert shards[0].bits_written == {
            circuit.bits[0],
            circuit.bits[1],
            circuit.bits[2],
            circuit.bits[3],
        }
        assert shards[0].bits_read == {
            circuit.bits[0],
            circuit.bits[1],
            circuit.bits[2],
            circuit.bits[3],
        }
        assert not shards[0].depends_upon

        # shard 1
        assert shards[1].primary_command.op.type == OpType.CopyBits
        assert len(shards[1].sub_commands.items()) == 0
        assert not shards[1].qubits_used
        assert shards[1].bits_written == {
            circuit.bits[4],
            circuit.bits[5],
            circuit.bits[6],
            circuit.bits[7],
        }
        assert shards[1].bits_read == {
            circuit.bits[0],
            circuit.bits[1],
            circuit.bits[2],
            circuit.bits[3],
            circuit.bits[4],
            circuit.bits[5],
            circuit.bits[6],
            circuit.bits[7],
        }
        assert shards[1].depends_upon == {shards[0].ID}

        # shard 2
        assert shards[2].primary_command.op.type == OpType.ClassicalExpBox
        assert len(shards[2].sub_commands.items()) == 0
        assert not shards[2].qubits_used
        assert shards[2].bits_written == {
            circuit.bits[8],
            circuit.bits[9],
            circuit.bits[10],
            circuit.bits[11],
        }
        assert shards[2].bits_read == {
            circuit.bits[0],
            circuit.bits[1],
            circuit.bits[2],
            circuit.bits[3],
            circuit.bits[4],
            circuit.bits[5],
            circuit.bits[6],
            circuit.bits[7],
            circuit.bits[8],
            circuit.bits[9],
            circuit.bits[10],
            circuit.bits[11],
        }
        assert shards[2].depends_upon == {shards[0].ID, shards[1].ID}

        # shard 2
        assert shards[3].primary_command.op.type == OpType.ClassicalExpBox
        assert len(shards[3].sub_commands.items()) == 0
        assert not shards[3].qubits_used
        assert shards[3].bits_written == {
            circuit.bits[0],
            circuit.bits[1],
            circuit.bits[2],
            circuit.bits[3],
        }
        assert shards[3].bits_read == {
            circuit.bits[0],
            circuit.bits[1],
            circuit.bits[2],
            circuit.bits[3],
        }
        assert shards[3].depends_upon == {shards[0].ID, shards[2].ID}
