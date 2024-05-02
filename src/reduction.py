import copy
from enum import Enum
from matching import matching
from exact import exact, exact_by_grb_ilp_wo_rc
from approx import approx
from table import Table
import numpy as np
from scipy.optimize import linear_sum_assignment
from tqdm import tqdm
from vertex_cover_approx import vertex_cover_approximation
from postclean import postclean_for_set


class AfterReduction(Enum):
    ERROR = 0
    ILP = 1
    LP_ROUNDING = 2
    MOST_FREQUENT_COL = 3
    # MAXIMUM_CLOSURE_COL = 4
    LP_GREEDY_ROUNDING = 5
    LP_NEW_GREEDY_ROUNDING = 6


# lhschain
# input: a Table t, a FDSet delta
# output: a mapping ColorDistribution -> (Sub-)Table (without conflicts)
def s_repair(
    t,
    delta,
    rc=None,
    after_reduction=AfterReduction.ERROR,
    matching_method="GRB_ILP",
    seed=None,
):
    # trivial
    delta.eliminate_trivial_fds()
    if delta.n == 0:
        # no FD
        _t = t.copy()
        return {_t.color_distribution: _t}
    # common lhs
    col = delta.find_common_lhs()
    if col is not None:
        # initialization
        m = [{t.get_empty_table().color_distribution: t.get_empty_table()}, {}]
        ii = 0
        for val in t.get_distinct_vals_of(col):
            m0 = s_repair(
                t.get_subtable_by_filter(col, val),
                delta.remove_cols([col]),
                rc,
                after_reduction,
            )
            for s in m[ii]:
                for s0 in m0:
                    s_plus_s0 = s + s0
                    if s_plus_s0 not in m[1 - ii]:
                        all_s = list(m[1 - ii].keys())
                        flag = True
                        for ss in all_s:
                            if ss < s_plus_s0:
                                del m[1 - ii][ss]
                            if s_plus_s0 < ss:
                                flag = False
                                break
                        if flag:
                            m[1 - ii][s_plus_s0] = m[ii][s] + m0[s0]
            m[ii].clear()
            ii = 1 - ii
        return m[ii]
    # consensus
    fd_id = delta.find_consensus_fd_id()
    if fd_id is not None:
        # initialization
        m = {}
        col = delta.fds[fd_id].rhs.col
        for val in t.get_distinct_vals_of(col):
            m0 = s_repair(
                t.get_subtable_by_filter(col, val),
                delta.remove_cols([col]),
                rc,
                after_reduction,
            )
            for s0 in m0:
                if s0 not in m:
                    all_s = list(m.keys())
                    flag = True
                    for s in all_s:
                        if s < s0:
                            del m[s]
                        if s0 < s:
                            flag = False
                            break
                    if flag:
                        m[s0] = m0[s0].copy()
        if len(m) == 0:
            m = {t.get_empty_table().color_distribution: t.get_empty_table()}
        return m
    # lhs marriage (deprecated as future work)
    lhs_marriage_or_none = delta.find_lhs_marriage()
    if lhs_marriage_or_none is not None:
        # initialization
        m = {}

        l_edges = {}
        r_edges = {}
        n_colors = t.color_distribution.c

        repairs = {}

        lhs1, lhs2 = lhs_marriage_or_none
        combos = t.group_by_two_lhs(lhs1, lhs2)
        for _, row in combos.iterrows():
            predicates = []
            for col in combos.columns:
                predicates.append(f"({col} == '{row[col]}')")
            m0 = s_repair(
                t.get_subtable_by_query(" & ".join(predicates)),
                delta.remove_cols(copy.deepcopy(lhs1.cols) + copy.deepcopy(lhs2.cols)),
                rc,
                after_reduction,
            )
            le = ",".join([row[col] for col in lhs1.cols])
            ri = ",".join([row[col] for col in lhs2.cols])
            if le not in l_edges:
                l_edges[le] = {}
            if ri not in l_edges[le]:
                l_edges[le][ri] = []
            if ri not in r_edges:
                r_edges[ri] = {}
            if le not in r_edges[ri]:
                r_edges[ri][le] = []
            if le not in repairs:
                repairs[le] = {}
            if ri not in repairs[le]:
                repairs[le][ri] = []
            for k, v in m0.items():
                l_edges[le][ri].append(k)
                r_edges[ri][le].append(k)
                repairs[le][ri].append(v)

        res = matching(l_edges, r_edges, n_colors, rc, t.labels, matching_method)
        t0 = t.get_empty_table()
        for le, ri, which in res:
            t0 = t0 + repairs[le][ri][which]
        m[t0.color_distribution] = t0
        return m
    #    print('After reduction:', after_reduction)
    if after_reduction == AfterReduction.ERROR:
        raise ValueError("Reach a failure after reduction")
    elif after_reduction == AfterReduction.ILP:
        assert rc is not None
        return exact(t, delta, rc, method="GRB_ILP", seed=seed)
    elif after_reduction == AfterReduction.LP_ROUNDING:
        assert rc is not None
        return approx(t, delta, rc, method="GRB_LP_ROUNDING", seed=seed)
    elif after_reduction == AfterReduction.LP_GREEDY_ROUNDING:
        assert rc is not None
        return approx(t, delta, rc, method="GRB_LP_GREEDY_ROUNDING", seed=seed)
    elif after_reduction == AfterReduction.LP_NEW_GREEDY_ROUNDING:
        assert rc is not None
        return approx(t, delta, rc, method="GRB_LP_NEW_GREEDY_ROUNDING", seed=seed)
    elif after_reduction == AfterReduction.MOST_FREQUENT_COL:
        assert not delta.empty()
        t0 = t.copy()
        delta0 = delta.copy()
        while not delta0.empty():
            col, fd_id = delta0.find_most_frequent_col()
            m = s_repair(
                t0,
                delta0.get_subfdset_by_ids([fd_id]),
                rc=rc,
                after_reduction=AfterReduction.ERROR,
                matching_method="GRB_ILP",
                seed=seed,
            )
            t0 = postclean_for_set(m, rc)
            delta0 = delta0.get_subfdset_by_ids(
                list(range(0, fd_id)) + list(range(fd_id + 1, delta0.n))
            )
        return {t0.color_distribution: t0}
    else:
        raise NotImplementedError


# dp_baseline
# input: a Table t, a FDSet delta
# output: a maximized sub-Table w.o. violations


class AfterReduction_wo_rc(Enum):
    ERROR = 0
    APPROX = 1
    ILP = 2


def s_repair_wo_rc(
    t, delta, after_reduction=AfterReduction_wo_rc.APPROX, seed=None
):  # do approximation if no reduction
    # trivial
    delta.eliminate_trivial_fds()
    if delta.n == 0:
        # no FD
        return t
    # common lhs
    col = delta.find_common_lhs()
    if col is not None:
        # initialization
        res = t.get_empty_table()
        for val in t.get_distinct_vals_of(col):
            t0 = s_repair_wo_rc(
                t.get_subtable_by_filter(col, val),
                delta.remove_cols([col]),
            )
            res += t0
        return res
    # consensus
    fd_id = delta.find_consensus_fd_id()
    if fd_id is not None:
        # initialization
        col = delta.fds[fd_id].rhs.col
        res = t.get_empty_table()
        for val in t.get_distinct_vals_of(col):
            t0 = s_repair_wo_rc(
                t.get_subtable_by_filter(col, val), delta.remove_cols([col])
            )
            if t0.nrows() > res.nrows():
                res = t0
        return res
    # lhs marriage
    lhs_marriage_or_none = delta.find_lhs_marriage()
    if lhs_marriage_or_none is not None:
        # initialization
        edges = []
        lhs1, lhs2 = lhs_marriage_or_none
        combos = t.group_by_two_lhs(lhs1, lhs2)
        le_to_idx = {}
        le_cnt = 0
        ri_to_idx = {}
        ri_cnt = 0
        sub_repairs = {}
        for _, row in combos.iterrows():
            predicates = []
            for col in combos.columns:
                predicates.append(f"({col} == '{row[col]}')")
            t0 = s_repair_wo_rc(
                t.get_subtable_by_query(" & ".join(predicates)),
                delta.remove_cols(copy.deepcopy(lhs1.cols) + copy.deepcopy(lhs2.cols)),
            )
            le = ",".join([row[col] for col in lhs1.cols])
            ri = ",".join([row[col] for col in lhs2.cols])
            edges.append((le, ri, t0.nrows()))
            if le not in le_to_idx:
                le_to_idx[le] = le_cnt
                le_cnt += 1
            if ri not in ri_to_idx:
                ri_to_idx[ri] = ri_cnt
                ri_cnt += 1
            sub_repairs[(le_to_idx[le], ri_to_idx[ri])] = t0
        c = np.full(shape=(le_cnt, ri_cnt), fill_value=(1 << 31) - 1, dtype=int)
        for edge in edges:
            c[le_to_idx[edge[0]], ri_to_idx[edge[1]]] = -edge[2]
        le_idx, ri_idx = linear_sum_assignment(c)
        res = t.get_empty_table()
        for i in range(len(le_idx)):
            if (le_idx[i], ri_idx[i]) in sub_repairs:
                res += sub_repairs[(le_idx[i], ri_idx[i])]
        return res

    if after_reduction == AfterReduction_wo_rc.ERROR:
        raise ValueError("Reach a failure after reduction")
    elif after_reduction == AfterReduction_wo_rc.APPROX:
        res = vertex_cover_approximation(t, delta, seed=seed)
        return res
    elif after_reduction == AfterReduction_wo_rc.ILP:
        res = exact_by_grb_ilp_wo_rc(t, delta, seed=seed)
        return res
    else:
        raise NotImplementedError


class ReductionState(Enum):
    SUCCESS = 0
    FAILURE = 1
    APPROXIMATION = 2


def validate_reduction(_delta):
    delta = _delta.copy()
    flag = True
    while delta.n > 0 and flag:
        flag = False
        _n = delta.n
        delta.eliminate_trivial_fds()
        if delta.n < _n:
            flag = True
            continue
        col = delta.find_common_lhs()
        if col is not None:
            delta = delta.remove_cols([col])
            flag = True
            continue
        fd_id = delta.find_consensus_fd_id()
        if fd_id is not None:
            col = delta.fds[fd_id].rhs.col
            delta = delta.remove_cols([col])
            flag = True
            continue
        lhs_marriage_or_none = delta.find_lhs_marriage()
        if lhs_marriage_or_none is not None:
            lhs1, lhs2 = lhs_marriage_or_none
            delta = delta.remove_cols(
                copy.deepcopy(lhs1.cols) + copy.deepcopy(lhs2.cols)
            )
            flag = True
            continue
    return delta.n == 0
