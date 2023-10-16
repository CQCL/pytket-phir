import os
from enum import Enum

from pytket.circuit import Circuit
from pytket.qasm.qasm import circuit_from_qasm


class QasmFiles(Enum):
    simple = 1
    cond_1 = 2
    bv_n10 = 3
    baby = 4
    baby_with_rollup = 5
    simple_cond = 6
    cond_classical = 7
    barrier_complex = 8
    classical_hazards = 9
    big_gate = 10


def get_qasm_as_circuit(qasm_file: QasmFiles) -> Circuit:
    """Utility function to convert a QASM file to Circuit.

    Args:
        qasm_file: enum for a QASM file

    Returns:
        Corresponding tket circuit
    """
    this_dir = os.path.dirname(os.path.abspath(__file__))
    return circuit_from_qasm(f"{this_dir}/data/qasm/{qasm_file.name}.qasm")
