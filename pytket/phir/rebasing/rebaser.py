##############################################################################
#
# Copyright (c) 2023 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

from typing import TYPE_CHECKING

from pytket.passes import DecomposeBoxes
from pytket.passes.auto_rebase import auto_rebase_pass
from pytket.phir.qtm_machine import QTM_DEFAULT_GATESET, QTM_MACHINES_MAP, QtmMachine

if TYPE_CHECKING:
    from pytket.circuit import Circuit


def rebase_to_qtm_machine(circuit: "Circuit", qtm_machine: QtmMachine) -> "Circuit":
    """Rebases a circuit's gate to the gate set appropriate for the given machine."""
    machine = QTM_MACHINES_MAP.get(qtm_machine)
    gateset = QTM_DEFAULT_GATESET if machine is None else machine.gateset
    c = circuit.copy()
    DecomposeBoxes().apply(c)
    auto_rebase_pass(gateset, allow_swaps=True).apply(c)
    return c
