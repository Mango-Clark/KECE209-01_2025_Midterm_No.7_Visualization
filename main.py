import os
import networkx as nx
import matplotlib.pyplot as plt
from itertools import product
from collections import Counter


# union-find(Disjoint Set) 구현
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


# 원본 K4와 레이아웃 정의
G = nx.complete_graph(["A", "B", "C", "D"])
edges = list(G.edges())
pos = {"A": (0, 0), "B": (2, 0), "C": (1, 3**-0.5), "D": (1, 3**0.5)}

# 출력 폴더 생성
os.makedirs("./Img", exist_ok=True)

# n = 0,1,2 에 대해 모든 중복 순열 반복
for n in range(3):
    for chosen in product(edges, repeat=n):
        # 파일명과 제목용 edge_names
        edge_names = ", ".join(f"{x}{y}" for x, y in chosen) or "None"
        safe_names = edge_names.replace(", ", "-")
        fname = f"n={n}_{safe_names}.png"
        path = os.path.join("Img", fname)

        # Original 엣지 색 (shorted 엣지는 파란색)
        colors_orig = [
            "blue" if (e in chosen or (e[1], e[0]) in chosen) else "black"
            for e in G.edges()
        ]

        # union-find로 병합 집합 구성
        uf = UnionFind(G.nodes())
        for x, y in chosen:
            uf.union(x, y)

        # 그룹별 매핑 및 병합 이름 생성
        groups = {}
        for node in G.nodes():
            root = uf.find(node)
            groups.setdefault(root, []).append(node)
        name_map = {r: "".join(sorted(mems)) for r, mems in groups.items()}

        # merged 그래프 H 생성: shorted 엣지 제거, self-loop 제거, 멀티엣지 집계
        counts = Counter()
        for x, y in G.edges():
            if (x, y) in chosen or (y, x) in chosen:
                continue
            a = name_map[uf.find(x)]
            b = name_map[uf.find(y)]
            if a == b:
                continue
            counts[tuple(sorted((a, b)))] += 1

        H = nx.MultiGraph()
        H.add_nodes_from(name_map.values())
        for (a, b), cnt in counts.items():
            for _ in range(cnt):
                H.add_edge(a, b)

        # H 레이아웃: 각 그룹의 최소 좌표
        posH = {}
        for root, members in groups.items():
            xs = [pos[m][0] for m in members]
            ys = [pos[m][1] for m in members]
            posH[name_map[root]] = (min(xs), min(ys))

        # 한 창에 Original / Opened / Merged
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5))

        # — Original network —
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

        # — Opened network (shorted 엣지 제거) —
        # 남길 엣지만 선택
        opened_edges = [
            e for e in G.edges() if not ((e in chosen) or ((e[1], e[0]) in chosen))
        ]
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

        # — Merged network —
        # 멀티엣지 각각을 약간씩 곡선 처리해 그리기
        for (a, b), cnt in counts.items():
            for i in range(cnt):
                rad = 0.2 * (i - (cnt - 1) / 2)
                nx.draw_networkx_edges(
                    H,
                    posH,
                    edgelist=[(a, b)],
                    ax=ax3,
                    edge_color="black",
                    width=3,
                    connectionstyle=f"arc3,rad={rad}",
                )
        faceH = ["white" if ("A" in n or "B" in n) else "lightgreen" for n in H.nodes()]
        edgeH = ["red" if ("A" in n or "B" in n) else "black" for n in H.nodes()]
        nx.draw_networkx_nodes(
            H,
            posH,
            ax=ax3,
            node_color=faceH,
            edgecolors=edgeH,
            linewidths=2,
            node_size=800,
        )
        nx.draw_networkx_labels(H, posH, ax=ax3, font_size=14)
        ax3.set_title(f"Resistor {edge_names} shorted")
        ax3.axis("off")
        ax3.set_xlim(right=2.3)

        plt.tight_layout()
        fig.savefig(path)
        plt.close(fig)
