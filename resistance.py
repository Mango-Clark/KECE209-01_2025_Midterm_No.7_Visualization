import os
import networkx as nx
import matplotlib.pyplot as plt
from itertools import product
from collections import Counter
import numpy as np


# union-find(Disjoint Set) implementation
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


# effective resistance via Laplacian pseudoinverse
def effective_resistance(G, u, v):
    nodes = list(G.nodes())
    L = nx.laplacian_matrix(G, nodelist=nodes, weight="weight").toarray()
    L_plus = np.linalg.pinv(L)
    idx = {node: i for i, node in enumerate(nodes)}
    return L_plus[idx[u], idx[u]] + L_plus[idx[v], idx[v]] - 2 * L_plus[idx[u], idx[v]]


# Original K4 and layout
G = nx.complete_graph(["A", "B", "C", "D"])
edges = list(G.edges())
pos = {"A": (0, 0), "B": (2, 0), "C": (1, 3**-0.5), "D": (1, 3**0.5)}

# Ensure output folder exists
os.makedirs("./Img_resistor", exist_ok=True)


# compute R_original
R_original = effective_resistance(G, "A", "B")

# Loop over n = 0,1,2 and all repeated-permutation choices
for n in range(3):
    for chosen in product(edges, repeat=n):
        # prepare names
        edge_names = ", ".join(f"{x}{y}" for x, y in chosen) or "None"
        safe_names = edge_names.replace(", ", "-")
        fname = f"n={n}_{safe_names}.png"
        path = os.path.join("Img_resistor", fname)

        # color original edges
        colors_orig = [
            "blue" if (e in chosen or (e[::-1] in chosen)) else "black"
            for e in G.edges()
        ]

        # build union-find sets
        uf = UnionFind(G.nodes())
        for x, y in chosen:
            uf.union(x, y)

        # prepare name_map for merged nodes
        groups = {}
        for node in G.nodes():
            root = uf.find(node)
            groups.setdefault(root, []).append(node)
        name_map = {r: "".join(sorted(mems)) for r, mems in groups.items()}

        # --- Opened graph (remove chosen edges) ---
        opened_edges = [e for e in G.edges() if not (e in chosen or e[::-1] in chosen)]
        G_open = nx.Graph()
        G_open.add_nodes_from(G.nodes())
        for u, v in opened_edges:
            G_open.add_edge(u, v, weight=1)

        # compute R_open
        R_open = effective_resistance(G_open, "A", "B")

        # --- Merged graph: counts for multiedges ---
        counts = Counter()
        for x, y in G.edges():
            if (x, y) in chosen or (y, x) in chosen:
                continue
            a, b = name_map[uf.find(x)], name_map[uf.find(y)]
            if a == b:
                continue
            counts[tuple(sorted((a, b)))] += 1

        # build MultiGraph for drawing
        H_multi = nx.MultiGraph()
        H_multi.add_nodes_from(name_map.values())
        for (a, b), cnt in counts.items():
            for _ in range(cnt):
                H_multi.add_edge(a, b)

        # build weighted Graph for resistance
        H_res = nx.Graph()
        H_res.add_nodes_from(name_map.values())
        for (a, b), cnt in counts.items():
            H_res.add_edge(a, b, weight=cnt)

        # compute R_merge
        mergedA = name_map[uf.find("A")]
        mergedB = name_map[uf.find("B")]
        R_short = (
            0.0 if mergedA == mergedB else effective_resistance(H_res, mergedA, mergedB)
        )

        # layout for merged
        posH = {}
        for root, members in groups.items():
            xs = [pos[m][0] for m in members]
            ys = [pos[m][1] for m in members]
            posH[name_map[root]] = (min(xs), min(ys))

        # plot
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))

        # Original
        nx.draw_networkx_edges(G, pos, ax=ax1, edge_color=colors_orig, width=3)
        face = ["white" if ("A" in n or "B" in n) else "lightgreen" for n in G.nodes()]
        edgecol = ["red" if ("A" in n or "B" in n) else "black" for n in G.nodes()]
        nx.draw_networkx_nodes(
            G,
            pos,
            ax=ax1,
            node_color=face,
            edgecolors=edgecol,
            linewidths=2,
            node_size=800,
        )
        nx.draw_networkx_labels(G, pos, ax=ax1, font_size=14)
        ax1.set_title("Resistor network plot")
        ax1.axis("off")
        ax1.text(
            0.5,
            -0.15,
            f"R = {R_original:.4f} Ω",
            transform=ax1.transAxes,
            ha="center",
            va="top",
        )

        # Opened
        nx.draw_networkx_edges(
            G, pos, edgelist=opened_edges, ax=ax2, edge_color="black", width=3
        )
        nx.draw_networkx_nodes(
            G,
            pos,
            ax=ax2,
            node_color=face,
            edgecolors=edgecol,
            linewidths=2,
            node_size=800,
        )
        nx.draw_networkx_labels(G, pos, ax=ax2, font_size=14)
        ax2.set_title(f"Resistor {edge_names} opened")
        ax2.axis("off")
        # annotate R_open under plot2
        ax2.text(
            0.5,
            -0.15,
            f"R = {R_open:.4f} Ω",
            transform=ax2.transAxes,
            ha="center",
            va="top",
        )

        # Shorted
        for (a, b), cnt in counts.items():
            for i in range(cnt):
                rad = 0.2 * (i - (cnt - 1) / 2)
                nx.draw_networkx_edges(
                    H_multi,
                    posH,
                    edgelist=[(a, b)],
                    ax=ax3,
                    edge_color="black",
                    width=3,
                    connectionstyle=f"arc3,rad={rad}",
                )
        faceH = [
            "white" if ("A" in n or "B" in n) else "lightgreen" for n in H_multi.nodes()
        ]
        edgeH = ["red" if ("A" in n or "B" in n) else "black" for n in H_multi.nodes()]
        nx.draw_networkx_nodes(
            H_multi,
            posH,
            ax=ax3,
            node_color=faceH,
            edgecolors=edgeH,
            linewidths=2,
            node_size=800,
        )
        nx.draw_networkx_labels(H_multi, posH, ax=ax3, font_size=14)
        ax3.set_title(f"Resistor {edge_names} shorted")
        ax3.axis("off")
        ax3.set_xlim(right=2.3)
        # annotate R_merge under plot3
        ax3.text(
            0.5,
            -0.15,
            f"R = {R_short:.4f} Ω",
            transform=ax3.transAxes,
            ha="center",
            va="top",
        )

        plt.tight_layout()
        fig.savefig(path)
        plt.close(fig)
