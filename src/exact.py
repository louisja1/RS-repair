import gurobipy as gb
from gurobipy import GRB
from table import Table
from tqdm import tqdm


def exact(t, delta, rc, method="GRB_ILP", seed=None):
    if method == "GRB_ILP":
        return exact_by_grb_ilp(t, delta, rc, seed)
    raise ValueError("Not Supported Optimizer")


# globalilp
# input: a Table t, a FDSet delta
# output: a mapping ColorDistribution -> (Sub-)Table (without conflicts)
def exact_by_grb_ilp(t, delta, rc, seed):
    map = {t.get_empty_table().color_distribution: t.get_empty_table()}

    m = gb.Model()
    # multi-threading
    m.setParam("Threads", 30)
    # add seed
    if seed is not None:
        m.Params.Seed = seed
    x = []

    for i in range(t.df.shape[0]):
        x.append(m.addVar(vtype=GRB.BINARY, name=f"r{i}"))

    # add constraints for FDs
    added = {}
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
                            if (ii, jj) not in added:
                                m.addConstr(x[ii] + x[jj] <= 1)
                                added[(ii, jj)] = 1

    # add constraints for RC
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
    for v in m.getVars():
        if v.VarName != "ans" and v.X != 0:
            idxs.append(int(v.VarName[1:]))
    t0 = Table(t.representative_column, t.df.iloc[idxs], t.labels)
    map[t0.color_distribution] = t0
    return map


# ilp-baseline
# input: a Table t, a FDSet delta
# output: (Sub-)Table (without conflicts)
def exact_by_grb_ilp_wo_rc(t, delta, seed):
    m = gb.Model()
    m.setParam("Threads", 30)

    x = []
    if seed is not None:
        m.Params.Seed = seed

    for i in range(t.df.shape[0]):
        x.append(m.addVar(vtype=GRB.BINARY, name=f"r{i}"))

    added = {}
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
                            if (ii, jj) not in added:
                                m.addConstr(x[ii] + x[jj] >= 1)
                                added[(ii, jj)] = 1

    m.setObjective(gb.quicksum(x[i] for i in range(len(x))), GRB.MINIMIZE)

    print("Start Optimization")
    m.Params.LogToConsole = 0
    m.optimize()

    assert m.status == GRB.OPTIMAL

    idxs = [i for i, v in enumerate(m.getVars()) if v.X == 0]

    t0 = Table(t.representative_column, t.df.iloc[idxs], t.labels)

    return t0
