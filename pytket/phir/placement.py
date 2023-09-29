import math
import bisect
from pytket.phir.routing import inverse

class PlacementError(Exception):
    def __init__(self) -> None:
        super().__init__('No more possible zones to place qubit')

def placement_check(ops: list[list[int]], tq_options: set[int], sq_options: set[int], state: list[int]) -> bool:
    '''Ensure that the qubits end up in the right gating zones'''
    
    ok = False
    inv = inverse(state)

    #assume ops look like this [[1,2],[3],[4],[5,6],[7],[8],[9,10]]
    for op in ops:
        if len(op) == 2: #tq operation
            q1, q2 = op[0], op[1]
            #check that the q1 is next to q2 and they are in the right zone
            #for now assuming that it does not matter which qubit is where in the tq zone, can be modified once we have a better idea of what ops looks like
            zone = ((inv[q1] in tq_options) | (inv[q2] in tq_options))
            neighbor = ((state.index(q2) == state.index(q1) + 1) | (state.index(q1) == state.index(q2) + 1))
            ok = zone & neighbor
                             
        if len(op) == 1: #sq operation
            q = op[0]
            zone = (state.index(q) in sq_options)
            ok = zone

    return ok

def nearest(zone, options: set[int]) -> int:
    
    lst = sorted(options)
    ind = bisect.bisect_left(lst, zone)
    
    if ind == 0:
        nearest = lst[0]
    elif ind == len(lst):
        nearest = lst[-1]
    else:
        l = lst[ind-1]
        r = lst[ind]
        nearest = l if r-zone > zone-l else r
    
    return nearest

def place(ops: list[list[int]], tq_options: set[int], sq_options: set[int], trap_size: int) -> list[int]:
    '''Place the qubits in the trap'''
    #assume ops look like this [[1,2],[3],[4],[5,6],[7],[8],[9,10]]
    #need a way to determine which qubits are furthest away from each other first
    trap = [-1] * trap_size
    placed_qubits = set()
    
    tq_zones = tq_options
    sq_zones = sq_options

    tq_ops = []
    sq_ops = []

    #get separate lists of tq and sq operations
    for op in ops:
        if len(op) == 2: #tq operation
            tq_ops.append(op)
        if len(op) ==1: #sq_operation
            sq_ops.append(op)

    #sort the tq_ops by distance apart [[furthest] -> [closest]]
    tq_ops = sorted(tq_ops, key=lambda x: abs(x[0]-x[1]), reverse=True)

    #place the tq ops
    for op in tq_ops:
        #check to make sure that there are tq zones available
        if len(tq_zones) == 0:
            raise PlacementError()
        q1, q2 = op[0], op[1]
        #for now assuming that it does not matter which qubit is where in the tq zone, can be modified once we have a better idea of what ops looks like
        midpoint = math.floor(abs(q2-q1)/2) + min(q1, q2)
        #find the tq gating zone closest to the midpoint of the 2 qubits
        nearest_tq_zone = nearest(midpoint, tq_zones)
        trap[nearest_tq_zone] = q1
        trap[nearest_tq_zone+1] = q2
        #remove the occupied zones in the tap from tq and sq options
        tq_zones.discard(nearest_tq_zone)
        tq_zones.discard(nearest_tq_zone+1)
        sq_zones.discard(nearest_tq_zone)
        sq_zones.discard(nearest_tq_zone+1)
        placed_qubits.add(q1)
        placed_qubits.add(q2)

    #place the sq ops
    for op in sq_ops:
        #check to make sure that there are tq zones available
        if len(sq_zones) == 0:
            raise PlacementError()
        q1 = op[0]
        #place the qubit in the first available zone
        for i in range(trap_size):
            if i in sq_zones:
                trap[i] = q1
                tq_zones.discard(i)
                sq_zones.discard(i)
                placed_qubits.add(q1)
                break
    
    #fill in the rest of the slots in the trap with the inactive qubits
    for i in range(trap_size):
        if i not in placed_qubits:
            for j in range(trap_size):
                if trap[j] == -1:
                    trap[j] = i
                    break

    placement_check(ops, tq_options, sq_options, trap)
    #print(trap)
    return trap



