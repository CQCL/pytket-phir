##############################################################################
#
# (c) 2023 @ Quantinuum LLC. All Rights Reserved.
# This software and all information and expression are the property of
# Quantinuum LLC, are Quantinuum LLC Confidential & Proprietary,
# contain trade secrets and may not, in whole or in part, be licensed,
# used, duplicated, disclosed, or reproduced for any purpose without prior
# written permission of Quantinuum LLC.
#
##############################################################################

from enum import Enum

from pytket import Circuit
from pytket.qasm import circuit_from_qasm

class QasmFiles(Enum):
    simple = 1
    cond_1 = 2
    bv_n10 = 3
    baby = 4

def get_qasm_as_circuit(qasm_file: QasmFiles) -> Circuit:
    return circuit_from_qasm(f'tests/data/qasm/{qasm_file.name}.qasm')