#Tests for qubit routing
from routing.routing import RoutingLibrary as lib

def test_oe_sort():

    r = lib()

    assert r.oe_sort([1,2,3,4,5,6],[1,2,3,4,5,6]) == (0,0)
    assert r.oe_sort([6,2,3,1,5,4],[1,2,3,4,5,6]) == (5,8)
    assert r.oe_sort([1,2,3,4,5,6],[2,1,4,5,6,3]) == (3,4)

test_oe_sort()