"""Dependency-free (numpy/scipy only) bridge finding + sink-rooted dependent-load accumulation on an undirected multigraph."""
import numpy as np

def build_csr(n, eu, ev):
    m = len(eu)
    src = np.concatenate([eu, ev]); dst = np.concatenate([ev, eu]); ids = np.concatenate([np.arange(m), np.arange(m)])
    order = np.argsort(src, kind="stable")
    src, dst, ids = src[order], dst[order], ids[order]
    indptr = np.zeros(n + 1, dtype=np.int64)
    np.cumsum(np.bincount(src, minlength=n), out=indptr[1:])
    return indptr, dst.astype(np.int64), ids.astype(np.int64)

def dfs_bridges(n, eu, ev, root):
    """Iterative Tarjan lowlink from `root` over the component of `root`. Returns dict with
    disc (-1 = unreached), parent, parent_edge, is_bridge_edge (bool per edge), order (discovery order of reached nodes)."""
    indptr, nbr, eid = build_csr(n, eu, ev)
    indptr_l, nbr_l, eid_l = indptr.tolist(), nbr.tolist(), eid.tolist()
    disc = [-1] * n; low = [0] * n; parent = [-1] * n; pedge = [-1] * n
    ptr = indptr_l[:-1]
    ptr = list(ptr)
    is_bridge = np.zeros(len(eu), dtype=bool)
    order = []
    t = 0
    disc[root] = low[root] = t; t += 1; order.append(root)
    stack = [root]
    while stack:
        u = stack[-1]
        i = ptr[u]
        if i < indptr_l[u + 1]:
            ptr[u] = i + 1
            w = nbr_l[i]; e = eid_l[i]
            if e == pedge[u]:
                continue
            if disc[w] == -1:
                parent[w] = u; pedge[w] = e; disc[w] = low[w] = t; t += 1; order.append(w); stack.append(w)
            else:
                if disc[w] < low[u]:
                    low[u] = disc[w]
        else:
            stack.pop()
            if stack:
                p = stack[-1]
                if low[u] < low[p]:
                    low[p] = low[u]
                if low[u] > disc[p]:
                    is_bridge[pedge[u]] = True
    return dict(disc=np.array(disc), parent=np.array(parent), parent_edge=np.array(pedge), is_bridge=is_bridge,
                order=np.array(order, dtype=np.int64))

def sink_rooted_loads(n, res, w_list):
    """Given the DFS result rooted at the sink, accumulate subtree weights (one or more weight vectors in w_list, each length n)
    and, for every reached node, the load of the TOPMOST bridge on its path to the sink and the number of bridges on the path.
    Returns top_load (list of arrays), nb (int array, -1 for unreached), top_bridge_child (node id whose parent edge is the topmost bridge, -1 if none)."""
    order, parent, pedge, is_bridge = res["order"], res["parent"], res["parent_edge"], res["is_bridge"]
    sub = [np.array(w, dtype=np.float64).copy() for w in w_list]
    # reverse-order accumulation of subtree sums
    for u in order[::-1]:
        p = parent[u]
        if p >= 0:
            for s in sub:
                s[p] += s[u]
    nb = np.full(n, -1, dtype=np.int32); topc = np.full(n, -1, dtype=np.int64)
    root = order[0]; nb[root] = 0
    ob = order.tolist(); par = parent.tolist(); pe = pedge.tolist()
    nb_l = nb.tolist(); topc_l = topc.tolist()
    for u in ob[1:]:
        p = par[u]
        e = pe[u]
        if is_bridge[e]:
            nb_l[u] = nb_l[p] + 1
            topc_l[u] = u if topc_l[p] == -1 else topc_l[p]
        else:
            nb_l[u] = nb_l[p]
            topc_l[u] = topc_l[p]
    nb = np.array(nb_l, dtype=np.int32); topc = np.array(topc_l, dtype=np.int64)
    top_loads = []
    for s in sub:
        tl = np.where(topc >= 0, s[np.maximum(topc, 0)], 0.0)
        top_loads.append(tl)
    return top_loads, nb, topc, sub
