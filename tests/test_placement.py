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
    InvalidQubitIdError,
    optimized_place,
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

    # non-identity permutation, exercising inv[q] lookups vs state.index(q)
    ops = [[1, 2], [3], [4]]
    state = [5, 4, 3, 2, 1, 0]
    assert placement_check(ops, m2.tq_options, m2.sq_options, state)

    ops = [[1, 2], [3], [4]]
    state = [4, 1, 2, 3, 0, 5]
    assert not placement_check(ops, m2.tq_options, m2.sq_options, state)

    # out-of-range/negative qubit ids must be rejected, not silently
    # aliased via Python's negative-index wraparound (regression for
    # inv[q]/prev_state_inv[q] lookups replacing state.index(q))
    ops = [[-1], [0]]
    state = [0, 1, 2, 3]
    with pytest.raises(InvalidQubitIdError):
        placement_check(ops, m.tq_options, m.sq_options, state)

    ops = [[4], [0]]
    state = [0, 1, 2, 3]
    with pytest.raises(InvalidQubitIdError):
        placement_check(ops, m.tq_options, m.sq_options, state)


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


def test_optimized_place_preserves_previous_order_for_unplaced_qubits() -> None:
    """Test optimized placement of gates and inactive qubits."""
    ops = [[0, 5], [2]]
    tq_options = {1}
    sq_options = set(range(6))
    prev_state = [5, 4, 3, 2, 1, 0]

    order = optimized_place(ops, tq_options, sq_options, 6, prev_state)

    assert order == [3, 5, 0, 2, 1, 4]
    assert placement_check(ops, tq_options, sq_options, order)


def test_optimized_place_handles_only_inactive_qubits() -> None:
    """Test optimized placement without operations."""
    prev_state = [3, 2, 1, 0]

    assert optimized_place([], set(), set(range(4)), 4, prev_state) == prev_state


def test_optimized_place() -> None:
    """Test optimized_place, exercising prev_state-dependent placement.

    These cases specifically cover the qubits/zones that previously relied
    on repeated ``list.index`` scans of ``state``/``prev_state`` (now
    replaced by O(1) lookups into precomputed inverse permutation arrays),
    ensuring the optimization preserves behavior.
    """
    # one tq, several sq ops, non-trivial (reversed) prev_state
    ops = [[0, 5], [1], [2], [3], [4]]
    tq_options = {1, 3}
    sq_options = {0, 1, 2, 3, 4, 5}
    trap_size = 6
    prev_state = [5, 4, 3, 2, 1, 0]
    expected = [4, 3, 2, 5, 0, 1]
    result = optimized_place(ops, tq_options, sq_options, trap_size, prev_state)
    assert result == expected
    assert placement_check(ops, tq_options, sq_options, result)

    # identity prev_state (edge case: prev_state.index(i) == i)
    ops = [[0, 3], [1], [2]]
    tq_options = {1}
    sq_options = {0, 1, 2, 3}
    trap_size = 4
    prev_state = [0, 1, 2, 3]
    result = optimized_place(ops, tq_options, sq_options, trap_size, prev_state)
    assert placement_check(ops, tq_options, sq_options, result)

    # larger, mixed tq/sq/inactive-qubit scenario
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
    prev_state = list(range(32))
    expected_larger = [
        0,
        31,
        2,
        3,
        1,
        5,
        6,
        8,
        9,
        11,
        10,
        12,
        7,
        15,
        13,
        16,
        4,
        28,
        14,
        18,
        17,
        23,
        21,
        22,
        19,
        25,
        20,
        24,
        26,
        27,
        29,
        30,
    ]
    result = optimized_place(ops, tq_options, sq_options, trap_size, prev_state)
    assert result == expected_larger
    assert placement_check(ops, tq_options, sq_options, result)


def test_optimized_place_error_paths() -> None:
    """Test optimized_place error paths, including invalid qubit ids."""
    # error paths still raised the same way
    ops = [[0, 1], [2]]
    tq_options = {0}
    sq_options = {0, 1}
    trap_size = 2
    prev_state = [0, 1]
    with pytest.raises(GateOpportunitiesError):
        optimized_place(ops, tq_options, sq_options, trap_size, prev_state)

    ops = [[1], [1]]
    tq_options = {1}
    sq_options = {0, 1, 2, 3}
    trap_size = 4
    prev_state = [0, 1, 2, 3]
    with pytest.raises(InvalidParallelOpsError):
        optimized_place(ops, tq_options, sq_options, trap_size, prev_state)

    # out-of-range/negative sq-op qubit ids must be rejected, not silently
    # aliased via Python's negative-index wraparound (regression for
    # prev_state_inv[q1] lookup replacing prev_state.index(q1))
    ops = [[-1]]
    tq_options = set()
    sq_options = {0, 1, 2, 3}
    trap_size = 4
    prev_state = [0, 1, 2, 3]
    with pytest.raises(InvalidQubitIdError):
        optimized_place(ops, tq_options, sq_options, trap_size, prev_state)

    # out-of-range TQ-op qubit ids must also be rejected before the
    # ordering/swap-check pass, not raise a raw IndexError when an
    # unvalidated id reaches prev_state_inv[...] there
    ops = [[4, 0]]
    tq_options = {1}
    sq_options = set(range(4))
    trap_size = 4
    prev_state = [0, 1, 2, 3]
    with pytest.raises(InvalidQubitIdError):
        optimized_place(ops, tq_options, sq_options, trap_size, prev_state)


test_placement_check()
test_place()
test_optimized_place()
test_optimized_place_error_paths()
