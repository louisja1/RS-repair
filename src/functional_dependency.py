import copy


class LHS:
    def __init__(self, cols):
        self.cols = list(cols)

    def size(self):
        return len(self.cols)

    def remove(self, col):
        self.cols.remove(col)

    def contains(self, col):
        return col is None or col in self.cols

    def contains_lhs(self, other):
        for col in other.cols:
            if not self.contains(col):
                return False
        return True

    def get_closure(self, fdset):
        closure = self.copy()
        flag = True
        while flag:
            flag = False
            for fd in fdset.fds:
                if closure.contains_lhs(fd.lhs) and not closure.contains(fd.rhs.col):
                    closure.cols.append(fd.rhs.col)
                    flag = True
        return closure

    def copy(self):
        return LHS(copy.deepcopy(self.cols))

    def __eq__(self, other):
        return sorted(self.cols) == sorted(other.cols)

    def __repr__(self):
        return ",".join(self.cols)

    def __str__(self):
        return self.__repr__()


class RHS:
    def __init__(self, col):
        self.col = col

    def copy(self):
        return RHS(copy.deepcopy(self.col))

    def __repr__(self):
        return self.col

    def __str__(self):
        return self.__repr__()


class FD:
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def is_trivial(self):
        return self.lhs.contains(self.rhs.col)

    def is_consensus(self):
        return len(self.lhs.cols) == 0

    def disagree(self, row1, row2):
        for col in self.lhs.cols:
            if col not in row1.index:
                return False
            if col not in row2.index:
                return False
            if row1[col] != row2[col]:
                return False
        if self.rhs.col not in row1.index:
            return False
        if self.rhs.col not in row2.index:
            return False
        return row1[self.rhs.col] != row2[self.rhs.col]

    def check_names(self, table):
        for col in self.lhs.cols:
            if col not in table.df.columns:
                return False
        if self.rhs.col not in table.df.columns:
            return False
        return True

    def copy(self):
        return FD(self.lhs.copy(), self.rhs.copy())

    def __repr__(self):
        return str(self.lhs) + "->" + str(self.rhs)

    def __str__(self):
        return self.__repr__()


class FDSet:
    def __init__(self, fds):
        self.fds = list(fds)
        self.n = len(fds)
        self.eliminate_trivial_fds()

    def empty(self):
        self.eliminate_trivial_fds()
        return self.n == 0

    def eliminate_trivial_fds(self):
        new_fds = []
        for fd in self.fds:
            if not fd.is_trivial():
                new_fds.append(copy.deepcopy(fd))
        self.fds = new_fds
        self.n = len(new_fds)

    # return a col/None
    def find_common_lhs(self):
        if self.n == 0:
            return None
        for col in self.fds[0].lhs.cols:
            flag = True
            for j in range(1, self.n):
                if not self.fds[j].lhs.contains(col):
                    flag = False
                    break
            if flag:
                return col
        return None

    # find the id of a consensus FD/None
    def find_consensus_fd_id(self):
        for i in range(self.n):
            if self.fds[i].is_consensus():
                return i
        return None

    # find lhs marriage, return lhs1 and lhs2 or a single None
    def find_lhs_marriage(self):
        for i in range(len(self.fds)):
            for j in range(i + 1, len(self.fds)):
                lhs1 = self.fds[i].lhs.copy()
                lhs2 = self.fds[j].lhs.copy()
                if lhs1 == lhs2:
                    continue
                if lhs1.get_closure(self) == lhs2.get_closure(self):
                    flag = True
                    for k in range(len(self.fds)):
                        if (not self.fds[k].lhs.contains_lhs(lhs1)) and (
                            not self.fds[k].lhs.contains_lhs(lhs2)
                        ):
                            flag = False
                            break
                    if flag:
                        return lhs1, lhs2
        return None

    # return most frequent col in lhs, and a fd id that contains it
    def find_most_frequent_col(self):
        col_to_freq = {}
        for fd in self.fds:
            for col in set(fd.lhs.cols):
                if col not in col_to_freq:
                    col_to_freq[col] = 0
                col_to_freq[col] += 1
        res = None
        for k, v in col_to_freq.items():
            if res is None or v > col_to_freq[res]:
                res = k
        if res is not None:
            for i in range(len(self.fds)):
                if self.fds[i].lhs.contains(res):
                    return res, i
        return None, None

    def find_maximum_closure_col(self):
        col_to_closure_size = {}
        for fd in self.fds:
            for col in fd.lhs.cols:
                if col not in col_to_closure_size:
                    col_to_closure_size[col] = LHS([col]).get_closure(self).size()
        res = None
        for k, v in col_to_closure_size.items():
            if res is None or v > col_to_closure_size[res]:
                res = k
        return res

    def remove_cols(self, cols):
        _fds = []
        for fd in self.fds:
            lhs_cols = []
            for col in fd.lhs.cols:
                if col not in cols:
                    lhs_cols.append(col)
            rhs_col = None if fd.rhs.col in cols else fd.rhs.col
            _fds.append(FD(LHS(lhs_cols), RHS(rhs_col)))
        return FDSet(_fds)

    def get_all_cols(self):
        cols = []
        for fd in self.fds:
            cols.extend(fd.lhs.copy().cols)
            cols.append(fd.rhs.col)
        return set(cols)

    def copy(self):
        _fds = []
        for i in range(self.n):
            _fds.append(self.fds[i].copy())
        return FDSet(_fds)

    def get_subfdset_by_ids(self, ids):
        _fds = []
        for id in ids:
            _fds.append(self.fds[id].copy())
        return FDSet(_fds)

    def __repr__(self):
        return "{" + "    ".join([str(x) for x in self.fds]) + "}"


# Input: str in the format as "LHS -> RHS", the reference of a table
# Output: a list of FDs (multiple FDs if RHS contains more than one attribute)
def parse(fd_in_str, table):
    assert "->" in fd_in_str
    lhs_in_str = fd_in_str.split("->")[0].strip()
    rhs_in_str = fd_in_str.split("->")[1].strip()
    l_rhs = rhs_in_str.split(",")

    fds = []
    for i in range(len(l_rhs)):
        rhs = l_rhs[i]
        fds.append(FD(LHS(lhs_in_str.split(",")), RHS(rhs)))
        assert fds[-1].check_names(table)
    return fds


def load_fdset(filename, table):
    fds = []
    with open(filename, "r") as fin:
        for line in fin.readlines():
            fds.extend(parse(line, table))
    return FDSet(fds)
