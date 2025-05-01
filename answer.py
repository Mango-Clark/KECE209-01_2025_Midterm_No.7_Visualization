import os
import networkx as nx
import matplotlib.pyplot as plt
from itertools import product
from fractions import Fraction


# -- Union-Find for merging nodes (shorted case) --
class UnionFind:
    def __init__(self, elements):
        self.parent = {e: e for e in elements}

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        rx, ry = self.find(x), self.find(y)
        if rx != ry:
            self.parent[ry] = rx


# -- Solve linear system A x = b with Gauss elimination (Fractions) --
def solve_linear(A, b):
    n = len(A)
    # Augment matrix
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    # Forward elimination
    for i in range(n):
        # pivot
        if M[i][i] == 0:
            # find non-zero pivot and swap
            for j in range(i + 1, n):
                if M[j][i] != 0:
                    M[i], M[j] = M[j], M[i]
                    break
        # normalize pivot row
        pivot = M[i][i]
        for k in range(i, n + 1):
            M[i][k] /= pivot
        # eliminate below
        for j in range(i + 1, n):
            factor = M[j][i]
            for k in range(i, n + 1):
                M[j][k] -= factor * M[i][k]
    # Back substitution
    x = [Fraction(0) for _ in range(n)]
    for i in reversed(range(n)):
        val = M[i][n]
        for k in range(i + 1, n):
            val -= M[i][k] * x[k]
        x[i] = val
    return x


# -- Compute effective resistance exactly via node-voltage method --
def effective_resistance_fraction(nodes, conductance, u, v):
    """
    nodes: list of node labels
    conductance: dict mapping frozenset({i,j}) to Fraction (or int) conductance
    u, v: node labels between which to compute resistance
    """
    # Reference node v: potential zero
    # Unknowns: potentials at other nodes in order nodes_unk
    nodes_unk = [node for node in nodes if node != v]
    idx = {node: i for i, node in enumerate(nodes_unk)}
    n = len(nodes_unk)
    # build Laplacian submatrix L'
    A = [[Fraction(0) for _ in range(n)] for __ in range(n)]
    b = [Fraction(0) for _ in range(n)]
    for i, node_i in enumerate(nodes_unk):
        # injection: 1 at u, 0 otherwise
        b[i] = Fraction(1) if node_i == u else Fraction(0)
        # sum conductances from i to all neighbors
        diag = Fraction(0)
        for node_j in nodes:
            if node_i == node_j:
                continue
            # conductance between i and j
            g = conductance.get(frozenset((node_i, node_j)), 0)
            if g:
                if node_j != v:
                    j = idx[node_j]
                    A[i][j] = A[i][j] - Fraction(g)
                diag += Fraction(g)
        A[i][i] = Fraction(diag)
    # solve A * V = b
    V = solve_linear(A, b)
    # potential at u
    if u == v:
        return Fraction(0)
    return V[idx[u]]


# -- Setup tetrahedral network K4 --
nodes = ["A", "B", "C", "D"]
edges = list(product(nodes, nodes))  # placeholder

# actual unique edges
edges = [("A", "B"), ("A", "C"), ("A", "D"), ("B", "C"), ("B", "D"), ("C", "D")]

# compute expected resistances for n=0,1,2
R_short = []
R_open = []

for n in range(3):
    total_short = Fraction(0)
    total_open = Fraction(0)
    outcomes = list(product(edges, repeat=n))
    for chosen in outcomes:
        # SHORT case: contract chosen edges
        uf = UnionFind(nodes)
        for u, v in chosen:
            uf.union(u, v)
        # groups (root -> members)
        groups = {}
        for node in nodes:
            root = uf.find(node)
            groups.setdefault(root, []).append(node)
        # compute merged nodes list
        merged_nodes = ["".join(sorted(mems)) for mems in groups.values()]
        # conductance dict for shorted graph
        cond_short = {}
        # count parallel edges
        counts = {}
        for e in edges:
            if e in chosen or (e[1], e[0]) in chosen:
                continue
            a = "".join(sorted(groups[uf.find(e[0])]))
            b = "".join(sorted(groups[uf.find(e[1])]))
            if a == b:
                continue
            key = frozenset((a, b))
            counts[key] = counts.get(key, 0) + 1
        # fill conductance dict as Fraction
        for key, cnt in counts.items():
            cond_short[key] = Fraction(cnt, 1)
        # compute R_short between merged A and merged B
        rootA = uf.find("A")
        rootB = uf.find("B")
        nodeA = "".join(sorted(groups[rootA]))
        nodeB = "".join(sorted(groups[rootB]))
        R_s = effective_resistance_fraction(merged_nodes, cond_short, nodeA, nodeB)
        total_short += R_s

        # OPEN case: remove chosen edges
        cond_open = {}
        counts_o = {}
        for e in edges:
            if e in chosen or (e[1], e[0]) in chosen:
                continue
            key = frozenset(e)
            counts_o[key] = counts_o.get(key, 0) + 1
        for key, cnt in counts_o.items():
            cond_open[key] = Fraction(cnt, 1)
        # graph remains nodes A,B,C,D
        # compute R_open between A,B
        # if no conductance between components, R = infinity (skip or treat)
        # but for open-case, removing edges could disconnect graph => R_open = Infinity
        # but expectation excludes infinite? Probably treat infinite as Infinity.
        # Here we assume connectivity always maintained for n<=2 in tetrahedron.
        R_o = effective_resistance_fraction(nodes, cond_open, "A", "B")
        total_open += R_o

    exp_short = total_short / Fraction(len(outcomes), 1)
    exp_open = total_open / Fraction(len(outcomes), 1)
    R_short.append(exp_short)
    R_open.append(exp_open)

# -- Plot with exact fractional annotations --
import matplotlib.ticker as mtick

x = [0, 1, 2]
y_short = [float(r) for r in R_short]
y_open = [float(r) for r in R_open]

fig = plt.figure(figsize=(6, 4))
plt.plot(x, y_short, "-o", color="red", label=r"$R_\mathrm{short}^{(n)}$")
plt.plot(x, y_open, "-o", color="blue", label=r"$R_\mathrm{open}^{(n)}$")
ax = plt.gca()
for xi, rs in zip(x, R_short):
    ax.annotate(
        f"{rs}",  # label text (a Fraction)
        xy=(xi, float(rs)),  # point to annotate
        xytext=(0, 5),  # offset: 0pt horiz, +5pt vert
        textcoords="offset points",
        ha="center",
        va="bottom",
        color="red",
    )
for xi, ro in zip(x, R_open):
    ax.annotate(
        f"{ro}",
        xy=(xi, float(ro)),
        xytext=(0, -5),
        textcoords="offset points",
        ha="center",
        va="top",
        color="blue",
    )
ymin, ymax = ax.get_ylim()
yrange = ymax - ymin
ax.set_ylim(ymin - 0.1 * yrange, ymax + 0.1 * yrange)
plt.xticks(x)
plt.xlabel("n (number of rolls)")
plt.ylabel("Expected Resistance between A and B (Ω)")
plt.title("Expected resistance of A and B")
plt.legend()
plt.grid(True)
plt.tight_layout()
fig.savefig("answer.png")
plt.close(fig)
