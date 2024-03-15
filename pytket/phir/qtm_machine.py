##############################################################################
#
# Copyright (c) 2023 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

from enum import Enum

from pytket.circuit import OpType

from .machine import Machine, MachineTimings


class QtmMachine(Enum):
    """Available machine architectures."""

    H1 = "H1"


QTM_DEFAULT_GATESET = {OpType.Rz, OpType.PhasedX, OpType.ZZPhase}

QTM_MACHINES_MAP = {
    QtmMachine.H1: Machine(
        size=20,
        gateset=QTM_DEFAULT_GATESET,
        tq_options={0, 2, 4, 6, 8, 10, 12, 14, 16, 18},
        timings=MachineTimings(
            tq_time=0.04,
            sq_time=0.03,
            qb_swap_time=0.9,
            meas_prep_time=0.05,
        ),
    )
}
