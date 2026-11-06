"""Sanity checks. Run with:  python -m tests.test_basic"""
import heapq
import itertools

from src.search import bfs, ucs, astar
from src.csp import solve
from problems import lateral_path, access_csp


def dijkstra(p):
    dist = {p.start: 0.0}
    pq = [(0.0, p.start)]
    while pq:
        d, n = heapq.heappop(pq)
        if d > dist[n]:
            continue
        for m, c in p.neighbors(n):
            if d + c < dist.get(m, float("inf")):
                dist[m] = d + c
                heapq.heappush(pq, (d + c, m))
    return dist.get(p.goal, float("inf"))


def brute_force_csp(csp):
    vs = csp.variables
    for combo in itertools.product(*(csp.domains[v] for v in vs)):
        if not csp.validate(dict(zip(vs, combo))):
            return True
    return False


def main():
    p = lateral_path.small_fixed()
    assert ucs(p)["cost"] == 4.5 and astar(p, p.hop_heuristic())["cost"] == 4.5
    assert bfs(p)["cost"] == 7.0
    for s in range(20):
        g = lateral_path.generate(n_hosts=120, density=0.06, risk_spread=3.0, seed=s)
        opt = dijkstra(g)
        assert abs(ucs(g)["cost"] - opt) < 1e-9
        assert abs(astar(g, g.hop_heuristic())["cost"] - opt) < 1e-9
        assert bfs(g)["cost"] >= opt - 1e-9
        h = g.hop_heuristic()
        assert h(g.start) <= opt + 1e-9  # admissible at the start node
    print("search tests passed (20 random graphs match Dijkstra)")

    for s in range(30):
        csp = access_csp.generate(n_requests=8, n_approvers=3, p_conflict=0.35,
                                  cap=3, seed=s)
        truth = brute_force_csp(csp)
        for m in ("bt", "fc", "mrv", "mrv_fc"):
            r = solve(csp, m)
            assert (r["status"] == "solved") == truth, (s, m, r["status"], truth)
            if r["solution"]:
                assert not csp.validate(r["solution"])
    print("csp tests passed (30 small instances match brute force)")


if __name__ == "__main__":
    main()
