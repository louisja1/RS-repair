import networkx as nx
from table import Table
import numpy as np
import pandas as pd
import random


def add_randomness(G, seed=None):
    edges = list(G.edges())
    if seed is not None:
        random.seed(seed)
    random.shuffle(edges)

    shuffled_graph = nx.Graph()
    shuffled_graph.add_nodes_from(G.nodes())
    shuffled_graph.add_edges_from(edges)
    return shuffled_graph


def build_violation_graph(t, delta, seed=None):
    G = nx.Graph()

    # Add vertices for each tuple
    num_tuples = t.df.shape[0]
    for i in range(num_tuples):
        G.add_node(i)

    # Check FD violations and add edges
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
                            if not G.has_edge(ii, jj):
                                G.add_edge(ii, jj)
    # add randomness
    G = add_randomness(G, seed=seed)

    return G


def find_vertex_cover(graph):
    # Compute a maximal matching
    matching = nx.algorithms.matching.maximal_matching(graph)
    vertex_cover = {u for edge in matching for u in edge}
    return vertex_cover
    # vertex cover is the set that going to remove


# input: a Table t, a FDSet delta
# output: (Sub-)Table (without conflicts)
def vertex_cover_approximation(t, delta, seed=None):
    violation_graph = build_violation_graph(t, delta, seed=seed)
    vertex_cover = find_vertex_cover(violation_graph)
    # remove tuple in vertex cover and get a subtable
    idxs = [i for i in range(t.df.shape[0]) if i not in vertex_cover]
    opt_t = Table(t.representative_column, t.df.iloc[idxs], t.labels)
    return opt_t
