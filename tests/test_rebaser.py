from pytket.circuit import Circuit, OpType
from pytket.phir.rebasing.rebaser import rebase_to_qtm_machine

from .sample_data import QasmFiles, get_qasm_as_circuit

EXPECTED_GATES = [
    OpType.Measure,
    OpType.Rz,
    OpType.PhasedX,
    OpType.ZZPhase,
]


class TestRebaser:
    def test_rebaser_happy_path_arc1a(self) -> None:
        circ = get_qasm_as_circuit(QasmFiles.baby)
        rebased: Circuit = rebase_to_qtm_machine(circ, "H1-1")

        print(rebased)
        for command in rebased.get_commands():
            print(command)
            if command.op.is_gate():
                assert command.op.type in EXPECTED_GATES