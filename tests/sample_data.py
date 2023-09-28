from enum import Enum

from pytket.circuit import Circuit
from pytket.qasm.qasm import circuit_from_qasm


class QasmFiles(Enum):
    simple = 1
    cond_1 = 2
    bv_n10 = 3
    baby = 4


def get_qasm_as_circuit(qasm_file: QasmFiles) -> Circuit:
    return circuit_from_qasm(f"tests/data/qasm/{qasm_file.name}.qasm")
