"""Lateral-path problem: a simulated network of hosts grouped into
segments (user LAN, servers, admin, data). An attacker or red-team path
starts at an entry host and needs to reach a high-value asset. Each
directed edge has a cost = 1 + risk, where risk models detection risk or
latency of that hop. Everything here is synthetic.
"""
import random
from collections import deque


class LateralPathProblem:
    def __init__(self, adj, start, goal, min_cost=1.0, name=""):
        self.adj = adj            # node -> list of (node, cost)
        self.start, self.goal = start, goal
        self.min_cost = min_cost
        self.name = name
        self._hops = None

    def neighbors(self, n):
        return self.adj.get(n, [])

    def hops_to_goal(self):
        """BFS on the reversed graph: fewest hops from each node to goal."""
        if self._hops is None:
            rev = {}
            for a, outs in self.adj.items():
                for b, _ in outs:
                    rev.setdefault(b, []).append(a)
            dist = {self.goal: 0}
            q = deque([self.goal])
            while q:
                n = q.popleft()
                for p in rev.get(n, []):
                    if p not in dist:
                        dist[p] = dist[n] + 1
                        q.append(p)
            self._hops = dist
        return self._hops

    def hop_heuristic(self):
        """h(n) = (fewest hops to goal) * (cheapest edge cost).
        Admissible: every hop costs at least min_cost."""
        hops = self.hops_to_goal()
        m = self.min_cost
        return lambda n: hops.get(n, float("inf")) * m


def generate(n_hosts=200, segments=5, density=0.05, risk_spread=4.0,
             seed=0):
    """Layered segment graph. Hosts are split into `segments` layers
    (entry side to crown-jewel side). Edges go mostly forward one layer,
    sometimes within a layer, rarely back. `density` sets the edge
    probability, `risk_spread` sets how much edge costs vary (cost in
    [1, 1 + risk_spread])."""
    rng = random.Random(seed)
    per = n_hosts // segments
    layer = {i: min(i // per, segments - 1) for i in range(n_hosts)}
    adj = {i: [] for i in range(n_hosts)}
    for a in range(n_hosts):
        for b in range(n_hosts):
            if a == b:
                continue
            d = layer[b] - layer[a]
            if d == 1:
                p = density
            elif d == 0:
                p = density / 2
            elif d == -1:
                p = density / 4
            else:
                continue
            if rng.random() < p:
                cost = 1.0 + rng.random() * risk_spread
                adj[a].append((b, round(cost, 3)))
    start = 0
    goal = n_hosts - 1
    # Guarantee at least one path with a chain through each segment.
    chain = [start] + [rng.randrange(s * per, (s + 1) * per)
                       for s in range(1, segments - 1)] + [goal]
    for a, b in zip(chain, chain[1:]):
        if all(x != b for x, _ in adj[a]):
            adj[a].append((b, round(1.0 + rng.random() * risk_spread, 3)))
    return LateralPathProblem(adj, start, goal, min_cost=1.0,
                              name=f"n{n_hosts}_d{density}_r{risk_spread}_s{seed}")


def small_fixed():
    """Hand-built 8-host example used in tests and the README."""
    adj = {
        "vpn":   [("ws1", 1.0), ("ws2", 2.0)],
        "ws1":   [("file", 4.0), ("jump", 1.5)],
        "ws2":   [("jump", 1.0), ("web", 1.0)],
        "web":   [("db", 6.0)],
        "file":  [("db", 2.0)],
        "jump":  [("admin", 1.0)],
        "admin": [("db", 1.0)],
        "db":    [],
    }
    return LateralPathProblem(adj, "vpn", "db", min_cost=1.0, name="fixed8")
