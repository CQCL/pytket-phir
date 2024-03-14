##############################################################################
#
# Copyright (c) 2023 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytket.circuit import OpType


@dataclass
class MachineTimings:
    """Gate times for a machine.

    tq_time: time for a two qubit gate
    sq_time: time for a single qubit gate
    qb_swap_time: time it takes to swap to qubits
    meas_prep_time: time to arrange qubits for measurement
    """

    tq_time: float
    sq_time: float
    qb_swap_time: float
    meas_prep_time: float


class Machine:
    """A machine info class for testing."""

    def __init__(
        self,
        size: int,
        gateset: "set[OpType]",
        tq_options: set[int],
        timings: MachineTimings,
    ):
        """Create Machine object.

        Args:
            size: number of qubits/slots
            gateset: set of supported gates
            tq_options: options for where to perform tq gates
            timings: gate times
        """
        self.size = size
        self.gateset = gateset
        self.tq_options = tq_options
        self.sq_options: set[int] = set()
        self.tq_time = timings.tq_time
        self.sq_time = timings.sq_time
        self.qb_swap_time = timings.qb_swap_time
        self.meas_prep_time = timings.meas_prep_time

        for i in self.tq_options:
            self.sq_options.add(i)
            self.sq_options.add(i + 1)
