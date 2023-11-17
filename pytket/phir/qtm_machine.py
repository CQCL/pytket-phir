##############################################################################
#
# Copyright (c) 2023 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

from enum import Enum

from .machine import Machine


class QtmMachine(Enum):
    """Available machine architectures."""

    H1_1 = "H1-1"
    H1_2 = "H1-2"


QTM_MACHINES_MAP = {
    QtmMachine.H1_1: Machine(
        size=20,
        tq_options={0, 2, 4, 6, 8, 10, 12, 14, 16, 18},
        # need to get better timing values for below
        # but will have to look them up in hqcompiler
        tq_time=3.0,
        sq_time=1.0,
        qb_swap_time=2.0,
    ),
    QtmMachine.H1_2: Machine(
        size=12,
        tq_options={0, 2, 4, 6, 8, 10},
        # need to get better timing values for below
        # but will have to look them up in hqcompiler
        tq_time=3.0,
        sq_time=1.0,
        qb_swap_time=2.0,
    ),
}
