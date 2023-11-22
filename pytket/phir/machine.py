##############################################################################
#
# Copyright (c) 2023 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################


class Machine:
    """A machine info class for testing."""

    def __init__(
        self,
        size: int,
        tq_options: set[int],
        tq_time: float,
        sq_time: float,
        qb_swap_time: float,
    ):
        """Create Machine object.

        Args:
            size: number of qubits/slots
            tq_options: options for where to perform tq gates
            tq_time: time for a two qubit gate
            sq_time: time for a single qubit gate
            qb_swap_time: time it takes to swap to qubits
        """
        self.size = size
        self.tq_options = tq_options
        self.sq_options: set[int] = set()
        self.tq_time = tq_time
        self.sq_time = sq_time
        self.qb_swap_time = qb_swap_time

        for i in self.tq_options:
            self.sq_options.add(i)
            self.sq_options.add(i + 1)
