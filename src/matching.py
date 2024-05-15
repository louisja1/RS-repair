import gurobipy as gb
from gurobipy import gurobipy
from gurobipy import GRB
import numpy as np
from utility import global_random_seed, eps
import copy
from color_distribution import ColorDistribution


# le -> ri -> list of ColorDistribution
# ri -> le -> list of ColorDistribution
def matching(l_edges, r_edges, n_colors, rc, labels, method):
    if method in ["GRB_ILP", "GRB_LP_ROUNDING", "GRB_LP_FRACTIONAL_LOOP_ELIMINATION"]:
        return grb_matching(l_edges, r_edges, n_colors, rc, labels, method=method[4:])
    else:
        raise ValueError("Not Supported Optimizer")


def grb_matching(l_edges, r_edges, n_colors, rc, labels, method):
    m = gb.Model()
    s = m.addVar(vtype=GRB.CONTINUOUS, name="ans")
    x = {}

    for le in l_edges.keys():
        for ri in l_edges[le].keys():
            for which in range(len(l_edges[le][ri])):
                if method == "ILP":
                    x[le, ri, which] = m.addVar(
                        vtype=GRB.BINARY, name=f"x({le}|{ri}|{which})"
                    )
                elif method in ["LP_ROUNDING", "LP_FRACTIONAL_LOOP_ELIMINATION"]:
                    x[le, ri, which] = m.addVar(
                        lb=0.0,
                        ub=1.0,
                        vtype=GRB.CONTINUOUS,
                        name=f"x({le}|{ri}|{which})",
                    )

    for le in l_edges.keys():
        expr = gb.LinExpr()
        for ri in l_edges[le].keys():
            for which in range(len(l_edges[le][ri])):
                expr += x[le, ri, which]
        m.addLConstr(expr, GRB.LESS_EQUAL, 1)

    for ri in r_edges.keys():
        expr = gb.LinExpr()
        for le in r_edges[ri].keys():
            for which in range(len(r_edges[ri][le])):
                expr += x[le, ri, which]
        m.addLConstr(expr, GRB.LESS_EQUAL, 1)

    for color in range(n_colors):
        expr = gb.LinExpr()
        expr += s * rc.constraint[labels[color]]
        for le in l_edges.keys():
            for ri in l_edges[le].keys():
                for which in range(len(l_edges[le][ri])):
                    count = l_edges[le][ri][which].get_c(color)
                    expr -= x[le, ri, which] * count
        m.addLConstr(expr, GRB.LESS_EQUAL, 0)

    m.setObjective(s, GRB.MAXIMIZE)
    m.Params.LogToConsole = 0
    m.optimize()

    assert m.status == GRB.OPTIMAL

    y = []
    if method in ["ILP", "LP_ROUNDING"]:
        r = np.random.RandomState(seed=global_random_seed)
        for v in m.getVars():
            if v.VarName != "ans":
                if (method == "ILP" and v.X == 1) or (
                    method == "LP_ROUNDING" and r.rand() <= v.X
                ):
                    _v = v.VarName[2:-1].split("|")
                    le, ri, which = _v[0], _v[1], int(_v[2])
                    y.append((le, ri, which))
        return y
    elif method == "LP_FRACTIONAL_LOOP_ELIMINATION":
        edges = [[], []]
        for v in m.getVars():
            if v.VarName != "ans":
                _v = v.VarName[2:-1].split("|")
                le, ri, which = _v[0], _v[1], int(_v[2])
                if v.X == 1.0:
                    y.append((le, ri, which))
                elif v.X > 0.0 and v.X < 1.0:
                    edges[0].append([le, ri, which, v.X])

        # eliminate loops
        ii = 0
        while len(edges[ii]) > 0:
            loop = _find_fractional_loop(edges[ii])
            if len(loop) == 0:
                break
            epsilon = 1.0
            for id in loop:
                epsilon = min(epsilon, min(edges[ii][id][3], 1 - edges[ii][id][3]))

            _d = [ColorDistribution(n_colors), ColorDistribution(n_colors)]
            for i in range(len(loop)):
                id = loop[i]
                le, ri, which = edges[ii][id][0], edges[ii][id][1], edges[ii][id][2]
                _d[i % 2] += l_edges[le][ri][which]

            if not _d[0].better_than(_d[1], rc, labels):
                epsilon *= -1

            for id in loop:
                edges[ii][id][3] += epsilon
                epsilon *= -1.0
            edges[1 - ii].clear()
            for i in range(len(edges[ii])):
                if edges[ii][i][3] < eps:
                    edges[ii][i][3] = 0.0
                if edges[ii][i][3] > 1 - eps:
                    edges[ii][i][3] = 1.0

                if edges[ii][i][3] < 1.0 and edges[ii][i][3] > 0.0:
                    edges[1 - ii].append(copy.deepcopy(edges[ii][i]))
                elif edges[ii][i][3] == 1.0:
                    y.append((edges[ii][i][0], edges[ii][i][1], edges[ii][i][2]))
            ii = 1 - ii

        # eliminate trees
        cds = []
        for i in range(len(edges[ii])):
            le, ri, which = edges[ii][i][0], edges[ii][i][1], edges[ii][i][2]
            cds.append(l_edges[le][ri][which])
        _post_optimize(edges[ii], n_colors, cds, rc, labels)
        for i in range(len(edges[ii])):
            if edges[ii][i][3] < eps:
                edges[ii][i][3] = 0.0
            if edges[ii][i][3] > 1 - eps:
                edges[ii][i][3] = 1.0

            if edges[ii][i][3] == 1.0:
                y.append((edges[ii][i][0], edges[ii][i][1], edges[ii][i][2]))
        return y


def _compute_adj(edges):
    ltr = {}
    rtl = {}
    for id in range(len(edges)):
        if edges[id][0] not in ltr:
            ltr[edges[id][0]] = []
        if edges[id][1] not in rtl:
            rtl[edges[id][1]] = []
        ltr[edges[id][0]].append(id)
        rtl[edges[id][1]].append(id)
    return ltr, rtl


def _visit_tree(edges, paths, adj, vis):
    side = (len(paths[0]) + len(paths[1])) % 2
    node = edges[paths[1 - side][-1]][side]
    for nxt in adj[side][node]:
        if not vis[nxt]:
            paths[side].append(nxt)
            vis[nxt] = True
            _visit_tree(edges, paths, adj, vis)


def _post_optimize(edges, n_colors, cds, rc, labels):
    ltr, rtl = _compute_adj(edges)
    vis = {id: False for id in range(len(edges))}
    for id in range(len(edges)):
        if (
            not vis[id]
            and len(ltr[edges[id][0]]) == 1
            and edges[id][3] > 0
            and edges[id][3] < 1
        ):
            paths = [[id], []]
            vis[id] = True
            _visit_tree(edges=edges, paths=paths, adj=[ltr, rtl], vis=vis)

            _d = [ColorDistribution(n_colors), ColorDistribution(n_colors)]
            for path_i in range(2):
                for id in paths[path_i]:
                    _d[path_i] += cds[id]

            path_i = 0 if _d[0].better_than(_d[1], rc, labels) else 1
            for id in paths[path_i]:
                edges[id][3] = 1.0
            for id in paths[1 - path_i]:
                edges[id][3] = 0.0


def _find(edges, path, vis, adj):
    if len(path) > 1 and edges[path[-1]][0] == edges[path[0]][0]:
        return True
    other_side = len(path) % 2
    for to in adj[other_side][edges[path[-1]][other_side]]:
        if not vis[to]:
            vis[to] = True
            path.append(to)
            flag = _find(edges, path, vis, adj)
            if flag:
                return True
            path.pop()
            vis[to] = False
    return False


def _find_fractional_loop(edges):
    ltr, rtl = _compute_adj(edges)
    path = []
    vis = {id: False for id in range(len(edges))}
    for id in range(len(edges)):
        vis[id] = True
        path.append(id)
        # start from left side
        if _find(edges=edges, path=path, vis=vis, adj=[ltr, rtl]):
            return path
        path.pop()
        vis[id] = False
    return path
