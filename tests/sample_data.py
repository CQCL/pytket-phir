##############################################################################
#
# Copyright (c) 2023 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

from enum import Enum, auto
from pathlib import Path

from pytket.circuit import Circuit
from pytket.qasm.qasm import circuit_from_qasm


class QasmFile(Enum):
    baby = auto()
    simple = auto()
    eztest = auto()
    baby_with_rollup = auto()
    big_gate = auto()
    simple_cond = auto()
    n10_test = auto()
    classical_hazards = auto()
    cond_1 = auto()
    barrier_complex = auto()
    cond_classical = auto()
    bv_n10 = auto()
    oned_brickwork_circuit_n20 = auto()
    qv20_0 = auto()


def get_qasm_as_circuit(qasm_file: QasmFile) -> Circuit:
    """Utility function to convert a QASM file to Circuit.

    Args:
        qasm_file: enum for a QASM file

    Returns:
        Corresponding tket circuit
    """
    this_dir = Path(Path(__file__).resolve()).parent
    return circuit_from_qasm(f"{this_dir}/data/qasm/{qasm_file.name}.qasm")
