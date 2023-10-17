import os
from enum import Enum, auto

from pytket.circuit import Circuit
from pytket.qasm.qasm import circuit_from_qasm


class QasmFile(Enum):
    simple = auto()
    cond_1 = auto()
    bv_n10 = auto()
    baby = auto()
    baby_with_rollup = auto()
    simple_cond = auto()
    cond_classical = auto()
    barrier_complex = auto()
    classical_hazards = auto()
    big_gate = auto()
    n10_test = auto()
    qv20_0 = auto()
    oned_brickwork_circuit_n20 = auto()
    eztest = auto()


def get_qasm_as_circuit(qasm_file: QasmFile) -> Circuit:
    """Utility function to convert a QASM file to Circuit.

    Args:
        qasm_file: enum for a QASM file

    Returns:
        Corresponding tket circuit
    """
    this_dir = os.path.dirname(os.path.abspath(__file__))
    return circuit_from_qasm(f"{this_dir}/data/qasm/{qasm_file.name}.qasm")
