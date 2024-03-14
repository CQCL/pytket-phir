##############################################################################
#
# Copyright (c) 2023 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

# Tests for qubit routing

import pytest

from pytket.phir.machine import Machine, MachineTimings
from pytket.phir.placement import (
    GateOpportunitiesError,
    InvalidParallelOpsError,
    place,
    placement_check,
)
from pytket.phir.qtm_machine import QTM_DEFAULT_GATESET

m = Machine(4, QTM_DEFAULT_GATESET, {1}, MachineTimings(10, 2, 2, 1))
m2 = Machine(6, QTM_DEFAULT_GATESET, {1, 3}, MachineTimings(10, 2, 2, 1))
m3 = Machine(8, QTM_DEFAULT_GATESET, {0, 6}, MachineTimings(10, 2, 2, 1))


def test_placement_check() -> None:
    """Test placement check."""
    # simple tq check
    ops = [[1, 2]]
    state = [0, 1, 2, 3]
    assert placement_check(ops, m.tq_options, m.sq_options, state)

    ops = [[2, 1]]
    state = [0, 1, 2, 3]
    assert placement_check(ops, m.tq_options, m.sq_options, state)

    # simple sq check
    ops = [[1], [2]]
    state = [0, 1, 2, 3]
    assert placement_check(ops, m.tq_options, m.sq_options, state)

    # combined sq/tq check
    ops = [[1, 2], [3], [4]]
    state = [0, 1, 2, 3, 4, 5]
    assert placement_check(ops, m2.tq_options, m2.sq_options, state)

    ops = [[2, 1], [3], [4]]
    state = [0, 1, 2, 3, 4, 5]
    assert placement_check(ops, m2.tq_options, m2.sq_options, state)

    # failing tests
    ops = [[0], [5]]
    state = [0, 1, 2, 3, 4, 5]
    assert not placement_check(ops, m2.tq_options, m2.sq_options, state)

    ops = [[1, 3], [2, 4]]
    state = [0, 1, 2, 3, 4, 5]
    assert not placement_check(ops, m2.tq_options, m2.sq_options, state)


def test_place() -> None:
    """Test place."""
    # one tq
    ops = [[0, 3]]
    tq_options = {1}
    sq_options = {1, 2}
    trap_size = 4
    expected = [1, 0, 3, 2]
    assert place(ops, tq_options, sq_options, trap_size) == expected

    # one tq two sq
    ops = [[0, 3], [1], [2]]
    tq_options = {1}
    sq_options = {0, 1, 2, 3}
    trap_size = 4
    expected = [1, 0, 3, 2]
    assert place(ops, tq_options, sq_options, trap_size) == expected

    # two tq
    ops = [[0, 5], [1, 4]]
    tq_options = {1, 3}
    sq_options = {0, 1, 2, 3, 4, 5}
    trap_size = 6
    expected = [2, 1, 4, 0, 5, 3]
    assert place(ops, tq_options, sq_options, trap_size) == expected

    # two tq two sq
    ops = [[0, 5], [1, 4], [2], [3]]
    tq_options = {1, 3}
    sq_options = {0, 1, 2, 3, 4, 5}
    trap_size = 6
    expected = [2, 1, 4, 0, 5, 3]
    assert place(ops, tq_options, sq_options, trap_size) == expected

    # real slice?
    ops = [
        [1, 5],
        [7, 15],
        [9, 11],
        [4, 28],
        [17, 23],
        [2],
        [10],
        [13],
        [16],
        [21],
        [22],
        [25],
    ]
    tq_options = {4, 8, 12, 16, 20, 24, 28}
    sq_options = set(range(32))
    trap_size = 32
    expected = [
        2,
        10,
        13,
        16,
        1,
        5,
        21,
        22,
        9,
        11,
        25,
        0,
        7,
        15,
        3,
        6,
        4,
        28,
        8,
        12,
        17,
        23,
        14,
        18,
        19,
        20,
        24,
        26,
        27,
        29,
        30,
        31,
    ]
    assert place(ops, tq_options, sq_options, trap_size) == expected

    # placement error
    ops = [[0, 1], [2]]
    tq_options = {0}
    sq_options = {0, 1}
    trap_size = 2
    with pytest.raises(GateOpportunitiesError):
        place(ops, tq_options, sq_options, trap_size)

    # op error
    ops = [[1], [1]]
    tq_options = {1}
    sq_options = {0, 1}
    trap_size = 2
    with pytest.raises(InvalidParallelOpsError):
        place(ops, tq_options, sq_options, trap_size)


test_placement_check()
test_place()
