# A Routing library that contains all the functions needed to give final qubit layout and an associated cost

class RoutingLibrary:

    def oe_sort(self, q1l, q2l):
        '''odd/even sort to determine the cost of routhing from q1l to q2l'''
        rounds = flips = 0
        p = [q2l.index(q) for q in q1l]

        while q1l != q2l:
            e = o = 0
            # even cycle
            for i in range(0, len(q1l)-1, 2):
                if p[i] > p[i+1]:
                    e = 1
                    flips += 1
                    q1l[i], q1l[i+1] = q1l[i+1], q1l[i]
                    p[i], p[i+1] = p[i+1], p[i]
            # odd cycle
            for i in range(1, len(q1l)-1, 2):
                if p[i] > p[i+1]:
                    o = 1
                    flips += 1
                    q1l[i], q1l[i+1] = q1l[i+1], q1l[i]
                    p[i], p[i+1] = p[i+1], p[i]
            rounds += e + o

        return rounds, flips

    def placement_check(self, ops, tq_options, sq_options, state):
        '''ensure that the qubits end up in the right gating zones'''
        #assume ops look like this [[1,2],[3],[4],[5,6],[7],[8],[9,10]]
        for op in ops:
            if len(op) == 2: #tq operation
                q1 = op[0]
                q2 = op[1]
                #check that the q1 is next to q2 and they are in the right zone
                #for now assuming that it does not matter which qubit is where in the tq zone, can be modified once we have a better idea of what ops looks like
                assert ((state.index(q1) in tq_options) | (state.index(q2) in tq_options)) & ((state.index(q2) == state.index(q1) + 1) | (state.index(q1) == state.index(q2) + 1))
                         # q1 in tq zone                   # q2 in tq zone                     # [q1, q2]                                 # [q2, q1]                  
            if len(op) == 1: #sq operation
                q = op[0]
                assert(state.index(q) in sq_options)
        
    def simple_cost(self, max_distance, qb_swap_time):
        '''simple cost output, can be modified as necessary'''
        return max_distance * qb_swap_time

