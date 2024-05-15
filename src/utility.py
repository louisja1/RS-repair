global_random_seed = 2023
eps = 1e-8


def compute_pairwise_violations(t, delta):
    cnt = 0
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
                                cnt += 1
                                added[(ii, jj)] = 1
    return cnt


def compute_violated_tuples(t, delta):
    idx_to_is_violated = {}
    for fd in delta.fds:
        lhs_grouped = t.df.groupby(fd.lhs.cols)
        for _, lhs_idxs in lhs_grouped.groups.items():
            rhs_grouped = t.df.loc[lhs_idxs].groupby(fd.rhs.col)
            all_idxs = []
            for _, rhs_idxs in rhs_grouped.groups.items():
                all_idxs.append(rhs_idxs.tolist())
            if len(all_idxs) > 1:
                for i in range(len(all_idxs)):
                    for ii in all_idxs[i]:
                        idx_to_is_violated[ii] = True
    return len(idx_to_is_violated)


def check_fds(t, delta):
    for fd in delta.fds:
        lhs_grouped = t.df.groupby(fd.lhs.cols)
        for _, lhs_idxs in lhs_grouped.groups.items():
            rhs_grouped = t.df.loc[lhs_idxs].groupby(fd.rhs.col)
            if len(list(rhs_grouped.groups.items())) > 1:
                print("Error: FD violated")
                print(rhs_grouped.groups)
                return False
    return True


def check_rc(t, rc):
    return rc.qualify(t.color_distribution)


def sanity_check(t, delta, rc):
    return check_fds(t, delta) and check_rc(t, rc)
