#Tests for qubit routing
import pytest
from pytket.routing import RoutingLibrary as lib
from test_machine_class import TestMachine

r = lib()
m = TestMachine(4, [1], [1,2], 10, 2, 2)
m2 = TestMachine(6, [1,3], [1,2,3,4], 10, 2, 2)

def test_oe_sort():
    assert r.oe_sort([1,2,3,4,5,6],[1,2,3,4,5,6]) == (0,0)
    assert r.oe_sort([6,2,3,1,5,4],[1,2,3,4,5,6]) == (5,8)
    assert r.oe_sort([1,2,3,4,5,6],[2,1,4,5,6,3]) == (3,4)

def test_placement_check():

    #simple tq check
    ops = [[1,2]]
    state = [0,1,2,3]
    r.placement_check(ops, m.tq_options, m.sq_options, state)

    ops = [[2,1]]
    state = [0,1,2,3]
    r.placement_check(ops, m.tq_options, m.sq_options, state)

    #simple sq check
    ops = [[1], [2]]
    state = [0,1,2,3]
    r.placement_check(ops, m.tq_options, m.sq_options, state)

    #combined sq/tq check
    ops = [[1,2],[3],[4]]
    state = [0,1,2,3,4,5]
    r.placement_check(ops, m2.tq_options, m2.sq_options, state)

    ops = [[2,1],[3],[4]]
    state = [0,1,2,3,4,5]
    r.placement_check(ops, m2.tq_options, m2.sq_options, state)

    #failing tests
    ops = [[0],[5]]
    state = [0,1,2,3,4,5]
    with pytest.raises(AssertionError):
        r.placement_check(ops, m2.tq_options, m2.sq_options, state)

    ops = [[1,3],[2,4]]
    state = [0,1,2,3,4,5]
    with pytest.raises(AssertionError):
        r.placement_check(ops, m2.tq_options, m2.sq_options, state)


def test_simple_cost():
    assert r.simple_cost(21,2) == 42

test_oe_sort()
test_placement_check()
test_simple_cost()
