import sys

sys.path.append("./src")
from functional_dependency import FD, LHS, RHS, FDSet
import numpy as np
import random

# helper functions for computing errors


def parse(fd_in_str):
    assert "->" in fd_in_str
    lhs_in_str = fd_in_str.split("->")[0].strip()
    rhs_in_str = fd_in_str.split("->")[1].strip()
    l_rhs = rhs_in_str.split(",")

    fds = []
    for i in range(len(l_rhs)):
        rhs = l_rhs[i]
        fds.append(FD(LHS(lhs_in_str.split(",")), RHS(rhs)))
        # assert fds[-1].check_names(table)
    return fds


def load_fds(filename):
    fds = []
    with open(filename, "r") as fin:
        for line in fin.readlines():
            fds.extend(parse(line))
    return FDSet(fds)


def make_col_int(df, *args):
    for col in args:
        df[col] = df[col].astype(float)
        df[col] = df[col].astype(int)


def make_col_string(df, *args):
    for col in args:
        df[col] = df[col].astype(str)


def compute_pairwise_violations(df, delta):
    cnt = 0
    added = {}
    for fd in delta.fds:
        lhs_grouped = df.groupby(fd.lhs.cols)
        for _, lhs_idxs in lhs_grouped.groups.items():
            rhs_grouped = df.loc[lhs_idxs].groupby(fd.rhs.col)
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


def compute_violated_tuples(df, delta):
    idx_to_is_violated = {}
    for fd in delta.fds:
        lhs_grouped = df.groupby(fd.lhs.cols)
        for _, lhs_idxs in lhs_grouped.groups.items():
            rhs_grouped = df.loc[lhs_idxs].groupby(fd.rhs.col)
            all_idxs = []
            for _, rhs_idxs in rhs_grouped.groups.items():
                all_idxs.append(rhs_idxs.tolist())
            if len(all_idxs) > 1:
                for i in range(len(all_idxs)):
                    for ii in all_idxs[i]:
                        idx_to_is_violated[ii] = True
    return len(idx_to_is_violated)


def compute_total_pairs(df):
    return df.shape[0] * (df.shape[0] - 1) // 2


def compute_error_cell(dirty_df, clean_df, delta):
    # compare with original clean datasets, to compute #error cells/#total cells (only consider columns in FDs RHS for now)
    column_ls = set()
    for fd in delta.fds:
        for col in fd.lhs.cols:
            column_ls.add(col)
        column_ls.add(fd.rhs.col)
    # for fd in delta.fds:
    #    column_ls.add(fd.rhs.col) ##only consider RHS for now

    cnt = 0
    err_tuple_tracker = set()

    make_col_int(
        dirty_df, "ID", "RAC1P", "SEX", "REGION", "ST", "CIT", "NATIVITY", "DIS"
    )
    # make_col_string(dirty_df, 'PINCP', 'COW', 'MSP', 'SCHL', 'MIL')
    for i in dirty_df["ID"]:
        for j in column_ls:
            if (
                dirty_df.loc[dirty_df["ID"] == i, j].iloc[0]
                != clean_df.loc[clean_df["ID"] == i, j].iloc[0]
            ):
                cnt += 1
                err_tuple_tracker.add(i)
    err_tuple = len(err_tuple_tracker)
    return cnt / (dirty_df.shape[0] * len(column_ls)), err_tuple / dirty_df.shape[0]


def compute_error_tuple(dirty_df, clean_df):
    # compare with original clean datasets, to compute #error tuples/#total tuples
    cnt = 0
    for i in dirty_df["ID"]:
        if not dirty_df.loc[dirty_df["ID"] == i].equals(
            clean_df.loc[clean_df["ID"] == i]
        ):
            cnt += 1
    return cnt / dirty_df.shape[0]


def display_violation(dir, df, clean, fd_ls):
    if df.shape[0] > 0:
        for fd in fd_ls:
            fd_filename = f"datagen/pums_info/{fd}.txt"
            delta = load_fds(fd_filename)
            pairwise_violations = compute_pairwise_violations(df, delta)
            total_pairs = compute_total_pairs(df)
            violated_tuples = compute_violated_tuples(df, delta)
            err_cell, err_tuple = compute_error_cell(df, clean, delta)
            print("FD rules:", delta)
            # print(f"Pairwise Violation Ratio: {np.round(100. * pairwise_violations / total_pairs, 3) if df.shape[0] > 0 else 0}%\n")
            print(
                f"Pairwise Violation Ratio: {np.round(100. * pairwise_violations / total_pairs, 3)}% ({pairwise_violations} / {total_pairs})\n"
            )
            print(
                f"Percentage of Violated Tuples: {np.round(100. * violated_tuples / df.shape[0], 3)}% ({violated_tuples} / {df.shape[0]})\n"
            )
            print(f"error rate of cell: {np.round(100.*err_cell,3)}%\n")
            print(f"error rate of tuple: {np.round(100.*err_tuple,3)}%\n")


def write_violation(dir, df, clean, fd_ls):
    filename = dir + f"violation.txt"
    with open(filename, "w") as f:
        if df.shape[0] > 0:
            for fd in fd_ls:
                fd_filename = f"pums_info/{fd}.txt"
                delta = load_fds(fd_filename)
                pairwise_violations = compute_pairwise_violations(df, delta)
                total_pairs = compute_total_pairs(df)
                violated_tuples = compute_violated_tuples(df, delta)
                err_cell, err_tuple = compute_error_cell(df, clean, delta)
                print("delta:", delta)
                f.write(f"{delta}\n")
                f.write(
                    f"Pairwise Violation Ratio: {np.round(100. * pairwise_violations / total_pairs, 3)}% ({pairwise_violations} / {total_pairs})\n"
                    f"Percentage of Violated Tuples: {np.round(100. * violated_tuples / df.shape[0], 3)}% ({violated_tuples} / {df.shape[0]})\n"
                    f"error rate of cell: {np.round(100.*err_cell,3)}%\n"
                    f"error rate of tuple: {np.round(100.*err_tuple,3)}%\n"
                )
