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


def test_fixed_search():
    p = lateral_path.small_fixed()
    assert ucs(p)["cost"] == 4.5 and astar(p, p.hop_heuristic())["cost"] == 4.5
    assert bfs(p)["cost"] == 7.0
    assert bfs(p)["path"] == ["vpn", "ws1", "file", "db"]
    assert ucs(p)["path"] == ["vpn", "ws1", "jump", "admin", "db"]


def test_start_equals_goal():
    p = lateral_path.LateralPathProblem({"x": []}, "x", "x", min_cost=1.0, name="same")
    for r in (bfs(p), ucs(p), astar(p, lambda n: 0.0)):
        assert r["path"] == ["x"] and r["cost"] == 0.0 and r["expanded"] == 0


def test_unreachable_goal():
    p = lateral_path.LateralPathProblem(
        {"a": [("b", 1.0)], "b": [], "c": []}, "a", "c", min_cost=1.0, name="gap"
    )
    for r in (bfs(p), ucs(p), astar(p, lambda n: 0.0)):
        assert r["path"] is None and r["cost"] == float("inf")


def test_random_search_matches_dijkstra():
    for s in range(20):
        g = lateral_path.generate(n_hosts=120, density=0.06, risk_spread=3.0, seed=s)
        opt = dijkstra(g)
        assert abs(ucs(g)["cost"] - opt) < 1e-9
        assert abs(astar(g, g.hop_heuristic())["cost"] - opt) < 1e-9
        assert bfs(g)["cost"] >= opt - 1e-9
        h = g.hop_heuristic()
        assert h(g.start) <= opt + 1e-9  # admissible at the start node
        # hop heuristic is admissible for every node that can reach the goal
        hops = g.hops_to_goal()
        for n, d in dijkstra_all(g).items():
            if n in hops:
                assert h(n) <= d + 1e-9


def dijkstra_all(p):
    """Shortest-path distances from every node to the goal on the reverse graph."""
    rev = {}
    for a, outs in p.adj.items():
        for b, c in outs:
            rev.setdefault(b, []).append((a, c))
    dist = {p.goal: 0.0}
    pq = [(0.0, p.goal)]
    while pq:
        d, n = heapq.heappop(pq)
        if d > dist[n]:
            continue
        for m, c in rev.get(n, []):
            if d + c < dist.get(m, float("inf")):
                dist[m] = d + c
                heapq.heappush(pq, (d + c, m))
    return dist


def test_astar_expands_at_most_ucs_on_fixed():
    p = lateral_path.small_fixed()
    assert astar(p, p.hop_heuristic())["expanded"] <= ucs(p)["expanded"]


def test_fixed_csp_all_methods_agree():
    csp = access_csp.small_fixed()
    statuses = {}
    for m in ("bt", "fc", "mrv", "mrv_fc", "mrv_fc_lcv"):
        r = solve(csp, m)
        statuses[m] = r["status"]
        if r["solution"]:
            assert not csp.validate(r["solution"])
    assert set(statuses.values()) == {"solved"}


def test_csp_matches_brute_force():
    for s in range(30):
        csp = access_csp.generate(n_requests=8, n_approvers=3, p_conflict=0.35,
                                  cap=3, seed=s)
        truth = brute_force_csp(csp)
        for m in ("bt", "fc", "mrv", "mrv_fc", "mrv_fc_lcv"):
            r = solve(csp, m)
            assert (r["status"] == "solved") == truth, (s, m, r["status"], truth)
            if r["solution"]:
                assert not csp.validate(r["solution"])


def test_csp_validate_rejects_partial():
    csp = access_csp.small_fixed()
    errs = csp.validate({"DA_grant": "Chen"})
    assert any("unassigned" in e for e in errs)


def main():
    test_fixed_search()
    test_start_equals_goal()
    test_unreachable_goal()
    test_random_search_matches_dijkstra()
    test_astar_expands_at_most_ucs_on_fixed()
    print("search tests passed (fixed, edge cases, 20 random graphs match Dijkstra)")
    test_fixed_csp_all_methods_agree()
    test_csp_matches_brute_force()
    test_csp_validate_rejects_partial()
    print("csp tests passed (fixed5, 30 small instances match brute force, validate)")


if __name__ == "__main__":
    main()
