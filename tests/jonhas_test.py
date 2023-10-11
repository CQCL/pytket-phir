import ast
from pytket.phir.placement import *
from pytket.phir.routing import *
from test_machine_class import TestMachine

m = TestMachine(12, {0,2,4,6,8,10}, 10, 2, 2)

def parse_circuit(file):
    print(file)
    circuit = []
    with open(file, "r") as f:
        for line in f:
            line = line.replace('\n', '')
            if ((line == '[') | (line == ']')):
                pass
            else:
                line = line.replace(' ', '')
                line = line.replace('][', '] [')
                opstrings = line.split(' ')
                ops = []
                for op in opstrings:
                    ops.append(ast.literal_eval(op)) #this is unsafe, do not leave in open source
                for op in ops:
                    for qubit in op:
                        qubit = int(qubit)
                circuit.append(ops)
    return circuit
                
                

def test_place(circuit):
    i=2
    print(f'TQ Zones: {m.tq_options}, SQ Zones: {m.sq_options}')
    for row in circuit:
        print(i)
        i+=1
        print(place(row, m.tq_options, m.sq_options, 12))


def eval_circuit(circuit):
    net_cost = 0
    prev_state = [0,1,2,3,4,5,6,7,8,9,10,11]
    for row in circuit:
        state = place(row, m.tq_options, m.sq_options, 12)
        # print(prev_state)
        # print(state)

        # e, o = eo_sort_rounds(prev_state, state)
        # cost = calc_cost(e, o)
        
        cost = transport_cost(prev_state, state, 725) #725 is avg of even and odd swaps
        
        # print(f'Cost: {cost} us')
        # print('\n')
        net_cost += cost
        prev_state = state
    return net_cost

def eval_optimized(circuit):
    net_cost = 0
    prev_state = [0,1,2,3,4,5,6,7,8,9,10,11]
    for row in circuit:
        state = optimized_place(row, m.tq_options, m.sq_options, 12, prev_state)
        # print(prev_state)
        # print(state)

        # e, o = eo_sort_rounds(prev_state, state)
        # cost = calc_cost(e, o)
        
        cost = transport_cost(prev_state, state, 725) #725 is avg of even and odd swaps

        # print(f'Cost: {cost} us')
        # print('\n')
        net_cost += cost
        prev_state = state
    return net_cost
 
bwc = parse_circuit("brickwork_circuit.txt")
nc = eval_circuit(bwc)
oc = eval_optimized(bwc)
print(f'Regaular: {nc} us')
print(f'Optimized: {oc} us')
