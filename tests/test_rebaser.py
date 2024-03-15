##############################################################################
#
# Copyright (c) 2023 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

import logging

from pytket.circuit import Circuit, OpType
from pytket.phir.qtm_machine import QtmMachine
from pytket.phir.rebasing.rebaser import rebase_to_qtm_machine

from .test_utils import QasmFile, get_qasm_as_circuit

EXPECTED_GATES = [
    OpType.Measure,
    OpType.Rz,
    OpType.PhasedX,
    OpType.ZZPhase,
]


logger = logging.getLogger(__name__)


class TestRebaser:
    def test_rebaser_happy_path_arc1a(self) -> None:
        circ = get_qasm_as_circuit(QasmFile.baby)
        rebased: Circuit = rebase_to_qtm_machine(circ, QtmMachine.H1)

        logger.info(rebased)
        for command in rebased.get_commands():
            if command.op.is_gate():
                assert command.op.type in EXPECTED_GATES
