import numpy as np


class ColorDistribution:
    # A class to maintain the distribution of sensitive values of the sensitive attribute
    def __init__(self, c, d=None):
        self.c = c
        self.d = {}
        for i in range(c):
            self.d[i] = 0
        if d is not None:
            self.set(d)

    def sum(self):
        _sum = 0
        for i in range(self.c):
            _sum += self.d[i]
        return _sum

    def add_c(self, i):
        self.d[i] += 1

    def get_c(self, i):
        return self.d[i]

    def set(self, d):
        for k in d:
            self.d[k] += d[k]

    def as_ordered_list(self):
        return [(i, self.d[i]) for i in range(self.c)]

    def get_all_subdist(self):
        _d = [[], [ColorDistribution(self.c)]]
        ii = 0
        for i in range(self.c):
            for old_dist in _d[1 - ii]:
                for k in range(self.d[i] + 1):
                    _d[ii].append(old_dist + ColorDistribution(self.c, {i: k}))
            _d[1 - ii].clear()
            ii = 1 - ii
        return _d[1 - ii]

    def __add__(self, other):
        if isinstance(other, np.int64) or isinstance(other, int):
            if isinstance(other, np.int64):
                other = other.item()
            res = {}
            for i in range(self.c):
                res[i] = self.d[i]
            res[other] += 1
            return ColorDistribution(self.c, res)
        if not isinstance(other, ColorDistribution):
            raise TypeError("Unsupported operand type for +")
        if self.c != other.c:
            raise TypeError("Inequal dimension for +")
        res = {}
        for i in range(self.c):
            res[i] = self.d[i] + other.d[i]
        return ColorDistribution(self.c, res)

    def __sub__(self, other):
        if not isinstance(other, ColorDistribution):
            raise TypeError("Unsupported operand type for -")
        if self.c != other.c:
            raise TypeError("Inequal dimension for -")
        res = {}
        for i in range(self.c):
            if self.d[i] < other.d[i]:
                raise ValueError("Value out-of-bound for -")
            res[i] = self.d[i] - other.d[i]
        return ColorDistribution(self.c, res)

    def __iadd__(self, other):
        if not isinstance(other, ColorDistribution):
            raise TypeError("Unsupported operand type for +")
        if self.c != other.c:
            raise TypeError("Inequal dimension for +")
        for i in range(self.c):
            self.d[i] += other.d[i]
        return self

    def __isub__(self, other):
        if not isinstance(other, ColorDistribution):
            raise TypeError("Unsupported operand type for -")
        if self.c != other.c:
            raise TypeError("Inequal dimension for -")
        for i in range(self.c):
            if self.d[i] < other.d[i]:
                raise ValueError("Value out-of-bound for -")
            self.d[i] -= other.d[i]
        return self

    def __hash__(self):
        return hash(tuple(self.as_ordered_list()))

    def __eq__(self, other):
        if not isinstance(other, ColorDistribution):
            return False
        if self.c != other.c:
            return False
        for i in range(self.c):
            if self.d[i] != other.d[i]:
                return False
        return True

    def __lt__(self, other):
        if not isinstance(other, ColorDistribution):
            raise TypeError("Unsupported operand type for <")
        if self.c != other.c:
            raise ValueError("Inequal dimension for <")
        flag = False
        for i in range(self.c):
            if self.d[i] > other.d[i]:
                return False
            if self.d[i] < other.d[i]:
                flag = True
        return flag

    def better_than(self, other, rc, labels):
        if other < self:
            return True
        min0 = None
        min1 = None
        for i in range(self.c):
            if rc.constraint[labels[i]] == 0:
                continue
            times0 = self.d[i] / rc.constraint[labels[i]]
            if min0 is None or min0 > times0:
                min0 = times0
            times1 = other.d[i] / rc.constraint[labels[i]]
            if min1 is None or min1 > times1:
                min1 = times1
        if min0 is None and min1 is None:
            return self.sum() > other.sum()
        if min0 == min1:
            return self.sum() > other.sum()
        return min0 > min1

    def __str__(self):
        return ",".join([f"({i},{self.d[i]})" for i in range(self.c)])
