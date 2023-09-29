#Tests for qubit routing
import pytest
from pytket.phir.placement import *
from pytket.phir.routing import *
from test_machine_class import TestMachine

m = TestMachine(4, {1}, {1,2}, 10, 2, 2)
m2 = TestMachine(6, {1,3}, {1,2,3,4}, 10, 2, 2)

def test_inverse():
    
    #one
    lst = [0]
    assert inverse(lst) == [0]

    #few
    lst = [2,1,0]
    assert inverse(lst) == [2,1,0]

    #many
    lst = [0,1,2,3,4,5,6,7,8,9]
    assert inverse(lst) == [0,1,2,3,4,5,6,7,8,9]

    #fail
    lst = [3,4,5,6]
    with pytest.raises(PermutationError):
        inverse(lst)

def test_transport_cost():

    #one
    init = [0]
    goal = [0]
    swap_cost = 1
    assert transport_cost(init, goal, swap_cost) == 0

    #few
    init = [0,1,2]
    goal = [2,1,0]
    swap_cost = 1
    assert transport_cost(init, goal, swap_cost) == 2

    #many
    init = [0,1,2,3,4,5,6,7,8,9]
    goal = [9,1,2,3,4,5,6,8,7,0]
    swap_cost == 1
    assert transport_cost(init, goal, swap_cost) == 9

    #fail
    init = [0,1,2]
    goal = [0,1,2,3]
    swap_cost = 1
    with pytest.raises(TransportError):
        transport_cost(init, goal, swap_cost)
        
def test_placement_check():

    #simple tq check
    ops = [[1,2]]
    state = [0,1,2,3]
    assert placement_check(ops, m.tq_options, m.sq_options, state)

    ops = [[2,1]]
    state = [0,1,2,3]
    assert placement_check(ops, m.tq_options, m.sq_options, state)

    #simple sq check
    ops = [[1], [2]]
    state = [0,1,2,3]
    assert placement_check(ops, m.tq_options, m.sq_options, state)

    #combined sq/tq check
    ops = [[1,2],[3],[4]]
    state = [0,1,2,3,4,5]
    assert placement_check(ops, m2.tq_options, m2.sq_options, state)

    ops = [[2,1],[3],[4]]
    state = [0,1,2,3,4,5]
    assert placement_check(ops, m2.tq_options, m2.sq_options, state)

    #failing tests
    ops = [[0],[5]]
    state = [0,1,2,3,4,5]
    assert not placement_check(ops, m2.tq_options, m2.sq_options, state)

    ops = [[1,3],[2,4]]
    state = [0,1,2,3,4,5]
    assert not placement_check(ops, m2.tq_options, m2.sq_options, state)

def test_place():

    #one tq
    ops = [[0,3]]
    tq_options = {1}
    sq_options = {1,2}
    trap_size = 4
    expected = [1,0,3,2]
    assert place(ops, tq_options, sq_options, trap_size) == expected

    #one tq two sq
    ops = [[0,3],[1],[2]]
    tq_options = {1}
    sq_options = {0,1,2,3}
    trap_size = 4
    expected = [1,0,3,2]
    assert place(ops, tq_options, sq_options, trap_size) == expected

    #two tq
    ops = [[0,5],[1,4]]
    tq_options = {1,3}
    sq_options = {0,1,2,3,4,5}
    trap_size = 6
    expected = [2, 1, 4, 0, 5, 3]
    assert place(ops, tq_options, sq_options, trap_size) == expected

    #two tq two sq
    ops = [[0,5],[1,4],[2],[3]]
    tq_options = {1,3}
    sq_options = {0,1,2,3,4,5}
    trap_size = 6
    expected = [2, 1, 4, 0, 5, 3]
    assert place(ops, tq_options, sq_options, trap_size) == expected

    #real slice?
    ops = [[1,5],[7,15],[9,11],[4,28],[17,23],[2],[10],[13],[16],[21],[22],[25]]
    tq_options = {4,8,12,16,20,24,28}
    sq_options = {i for i in range(32)}
    trap_size = 32
    expected = [2, 10, 13, 16, 1, 5, 21, 22, 9, 11, 25, 0, 7, 15, 3, 6, 4, 28, 8, 12, 17, 23, 14, 18, 19, 20, 24, 26, 27, 29, 30, 31]
    assert place(ops, tq_options, sq_options, trap_size) == expected

    #fail
    ops = [[0,1],[1]]
    tq_options = {0}
    sq_options = {0,1}
    trap_size = 2
    with pytest.raises(PlacementError):
        place(ops, tq_options, sq_options, trap_size)




test_inverse()
test_transport_cost()
test_placement_check()
test_place()
