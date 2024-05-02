from table import Table
from representative_constraint import RepresentativeConstraint
import math
import random
from utility import global_random_seed


# PostClean
def postclean(r, rc):
    assert isinstance(r, Table)
    assert isinstance(rc, RepresentativeConstraint)

    random.seed(global_random_seed)
    for t in range(r.nrows(), -1, -1):
        b = True
        min_demand = {}
        for i in range(rc.c):
            fraction = rc.constraint[rc.labels[i]]
            min_demand[i] = math.ceil(t * fraction.numerator / fraction.denominator)
            if min_demand[i] > r.color_distribution.get_c(i):
                b = False
                break
        t0 = 0
        for i in min_demand:
            t0 += min_demand[i]
        if b and t0 <= t:
            while t0 < t:
                i = random.randint(0, rc.c - 1)
                while min_demand[i] >= r.color_distribution.get_c(i):
                    i = random.randint(0, rc.c - 1)
                min_demand[i] += 1
                t0 += 1
            return r.get_subtable_by_nums(min_demand)
    return r.get_empty_table()


def postclean_for_set(repairs, rc):
    optimal = None
    for _, r in repairs.items():
        rprime = postclean(r, rc)
        if optimal is None or rprime.nrows() > optimal.nrows():
            optimal = rprime
    return optimal
