# A Routing library that contains all the functions needed to give final qubit layout and an associated cost

class RoutingLibrary:

    def oe_sort(self, q1l, q2l):
        #odd/even sort to determine the cost of routhing from q1l to q2l
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


