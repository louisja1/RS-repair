import gurobipy as gb
from gurobipy import GRB
from table import Table
import numpy as np
from utility import global_random_seed, eps
from color_distribution import ColorDistribution
import copy


def approx(t, delta, rc, method="GRB_LP_ROUNDING", seed=None):
    if method in [
        "GRB_LP_ROUNDING",
        "GRB_LP_GREEDY_ROUNDING",
        "GRB_LP_NEW_GREEDY_ROUNDING",
    ]:
        return approx_by_grb_lp_rounding(
            t, delta, rc, rounding_method=method[4:], seed=seed
        )
    raise ValueError("Not Supported Optimizer")


def approx_by_grb_lp_rounding(t, delta, rc, rounding_method, seed):
    # initialize the candidate set as a singleton set with the emptyset as a trivial repair
    map = {t.get_empty_table().color_distribution: t.get_empty_table()}

    m = gb.Model()
    if seed is not None:
        m.Params.Seed = seed
    x = []

    for i in range(t.df.shape[0]):
        x.append(m.addVar(lb=0.0, ub=1.0, vtype=GRB.CONTINUOUS, name=f"r{i}"))

    added = {}
    edges = []
    # construct the constraints for FDs
    for fd in delta.fds:
        lhs_grouped = t.df.groupby(fd.lhs.cols)
        for _, lhs_idxs in lhs_grouped.groups.items():
            rhs_grouped = t.df.loc[lhs_idxs].groupby(fd.rhs.col)
            all_idxs = []
            for _, rhs_idxs in rhs_grouped.groups.items():
                all_idxs.append(rhs_idxs.tolist())
            for i in range(len(all_idxs)):
                for j in range(i + 1, len(all_idxs)):
                    for ii in all_idxs[i]:
                        for jj in all_idxs[j]:
                            if (ii, jj) not in added and (jj, ii) not in added:
                                m.addConstr(x[ii] + x[jj] <= 1)
                                added[(ii, jj)] = 1
                                edges.append([ii, jj])

    # construct the constraints for RC
    for color in range(t.color_distribution.c):
        expr = gb.LinExpr()
        for idx, _ in t.df[t.df[t.representative_column] == color].iterrows():
            expr += x[idx]
        expr -= gb.quicksum(x) * rc.constraint[t.labels[color]]
        m.addLConstr(expr, GRB.GREATER_EQUAL, 0)

    m.setObjective(gb.quicksum(x), GRB.MAXIMIZE)
    m.Params.LogToConsole = 0
    m.optimize()

    assert m.status == GRB.OPTIMAL

    idxs = []

    if rounding_method == "LP_ROUNDING":
        # random rounding (deprecated because it might introduce FD violations during rounding)
        r = np.random.RandomState(seed=global_random_seed)
        for v in m.getVars():
            if v.VarName != "ans" and r.rand() <= v.X:
                idxs.append(int(v.VarName[1:]))
    elif rounding_method == "LP_GREEDY_ROUNDING":
        # greedyrounding
        n_colors = t.color_distribution.c
        ii = 0
        nodes = [[], []]
        for v in m.getVars():
            if v.VarName != "ans":
                if v.X == 1.0:
                    idxs.append(int(v.VarName[1:]))
                elif v.X > 0.0 and v.X < 1.0:
                    nodes[ii].append([int(v.VarName[1:]), v.X])

        adj = _compute_adj(edges)
        while len(nodes[ii]) > 0:
            id_to_pos = {}
            for i in range(len(nodes[ii])):
                id_to_pos[nodes[ii][i][0]] = i

            pick = None
            for i in range(len(nodes[ii])):
                if pick is None or len(adj[nodes[ii][i][0]]) < len(adj[pick]):
                    pick = nodes[ii][i][0]

            nodes[ii][id_to_pos[pick]][1] = 1.0
            for nxt in adj[pick]:
                if nxt in id_to_pos:
                    nodes[ii][id_to_pos[nxt]][1] = 0.0

            nodes[1 - ii].clear()

            for i in range(len(nodes[ii])):
                if nodes[ii][i][1] < 1.0 and nodes[ii][i][1] > 0.0:
                    nodes[1 - ii].append(copy.deepcopy(nodes[ii][i]))
                elif nodes[ii][i][1] == 1.0:
                    idxs.append(nodes[ii][i][0])
            ii = 1 - ii
    elif rounding_method == "LP_NEW_GREEDY_ROUNDING":
        # repr rounding
        n_colors = t.color_distribution.c
        ii = 0
        nodes = [[], []]
        for v in m.getVars():
            if v.VarName != "ans":
                if v.X == 1.0:
                    idxs.append(int(v.VarName[1:]))
                elif v.X > 0.0 and v.X < 1.0:
                    nodes[ii].append([int(v.VarName[1:]), v.X])

        strata_to_cnt = {}
        for color in range(t.color_distribution.c):
            strata_to_cnt[color] = 0

        adj = _compute_adj(edges)
        while len(nodes[ii]) > 0:
            id_to_pos = {}
            for i in range(len(nodes[ii])):
                id_to_pos[nodes[ii][i][0]] = i

            pick = None
            pick_color = None
            for i in range(len(nodes[ii])):
                x = nodes[ii][i][0]
                x_color = t.df.loc[x, t.representative_column].item()
                if pick is None:
                    pick = x
                    pick_color = x_color
                else:
                    x_color_constraint = rc.constraint[rc.labels[x_color]]
                    pick_color_constraint = rc.constraint[rc.labels[pick_color]]
                    x_ratio = strata_to_cnt[x_color] / x_color_constraint
                    pick_ratio = strata_to_cnt[pick_color] / pick_color_constraint
                    if (x_ratio, x_color_constraint, len(adj[x])) < (
                        pick_ratio,
                        pick_color_constraint,
                        len(adj[pick]),
                    ):
                        pick = x
                        pick_color = x_color

            assert pick is not None
            strata_to_cnt[pick_color] += 1

            nodes[ii][id_to_pos[pick]][1] = 1.0
            for nxt in adj[pick]:
                if nxt in id_to_pos:
                    nodes[ii][id_to_pos[nxt]][1] = 0.0

            nodes[1 - ii].clear()

            for i in range(len(nodes[ii])):
                if nodes[ii][i][1] < 1.0 and nodes[ii][i][1] > 0.0:
                    nodes[1 - ii].append(copy.deepcopy(nodes[ii][i]))
                elif nodes[ii][i][1] == 1.0:
                    idxs.append(nodes[ii][i][0])
            ii = 1 - ii

    # get the S-repair according to the value of each variable
    t0 = Table(t.representative_column, t.df.iloc[idxs], t.labels)
    map[t0.color_distribution] = t0
    return map


def _compute_adj(edges):
    adj = {}
    for id in range(len(edges)):
        if edges[id][0] not in adj:
            adj[edges[id][0]] = []
        if edges[id][1] not in adj:
            adj[edges[id][1]] = []
        adj[edges[id][0]].append(edges[id][1])
        adj[edges[id][1]].append(edges[id][0])
    return adj
