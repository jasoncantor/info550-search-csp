"""Run all comparisons and print metrics.

Usage:  python experiments.py            (full run, fixed seeds)
        python experiments.py --quick    (fewer seeds, for a fast check)
Pure Python standard library plus NumPy for the summary statistics.
"""
import sys
import time
import numpy as np

from src.search import bfs, ucs, astar
from src.csp import solve
from problems import lateral_path, access_csp


def timed(fn, *args):
    t0 = time.perf_counter()
    out = fn(*args)
    out["ms"] = (time.perf_counter() - t0) * 1000
    return out


def problem_a(seeds):
    print("=" * 78)
    print("PROBLEM A: lateral-path search (BFS vs UCS vs A* with hop heuristic)")
    print("Metric means over seeds. cost_ratio = path cost / optimal cost.")
    print("=" * 78)
    hdr = (f"{'hosts':>5} {'dens':>5} {'spread':>6} | {'alg':<5} {'expanded':>9} "
           f"{'cost':>7} {'ratio':>6} {'optimal%':>8} {'ms':>7}")
    print(hdr)
    print("-" * len(hdr))
    rows = []
    for n in (200, 500):
        for dens in (0.02, 0.05, 0.10):
            for spread in (0.5, 4.0):
                res = {"BFS": [], "UCS": [], "A*": []}
                for s in seeds:
                    p = lateral_path.generate(n_hosts=n, density=dens,
                                              risk_spread=spread, seed=s)
                    r_bfs = timed(bfs, p)
                    r_ucs = timed(ucs, p)
                    # A* time includes building the hop heuristic (reverse BFS)
                    r_ast = timed(lambda q: astar(q, q.hop_heuristic()), p)
                    opt = r_ucs["cost"]
                    assert abs(r_ast["cost"] - opt) < 1e-9, "A* not optimal"
                    for k, r in (("BFS", r_bfs), ("UCS", r_ucs), ("A*", r_ast)):
                        res[k].append((r["expanded"], r["cost"], r["cost"] / opt,
                                       r["ms"]))
                for k, vals in res.items():
                    a = np.array(vals)
                    opt_pct = 100 * np.mean(a[:, 2] < 1 + 1e-9)
                    print(f"{n:>5} {dens:>5} {spread:>6} | {k:<5} {a[:,0].mean():>9.1f} "
                          f"{a[:,1].mean():>7.2f} {a[:,2].mean():>6.3f} {opt_pct:>7.0f}% "
                          f"{a[:,3].mean():>7.2f}")
                    rows.append((n, dens, spread, k, a[:, 0].mean()))
                print()
    # A* savings vs UCS by spread
    print("A* nodes expanded as a share of UCS nodes expanded:")
    for n in (200, 500):
        for dens in (0.02, 0.05, 0.10):
            line = []
            for spread in (0.5, 4.0):
                u = [r[4] for r in rows if r[:4] == (n, dens, spread, "UCS")][0]
                a = [r[4] for r in rows if r[:4] == (n, dens, spread, "A*")][0]
                line.append(f"spread {spread}: {100*a/u:5.1f}%")
            print(f"  hosts {n}, density {dens}:  " + "   ".join(line))
    print()


def problem_b(seeds, limit):
    methods = ("bt", "fc", "mrv", "mrv_fc")
    print("=" * 78)
    print("PROBLEM B: privileged-access approval CSP")
    print("bt = plain backtracking (static order), fc = BT + forward checking,")
    print("mrv = BT + MRV, mrv_fc = BT + MRV + forward checking.")
    print(f"5 approvers, node limit {limit:,} assignments per run.")
    print("Means over all seeds (cutoff runs count at the limit).")
    print("=" * 78)
    hdr = (f"{'reqs':>4} {'p_conf':>6} {'edges':>6} | {'method':<7} {'assign':>10} {'backtr':>10} "
           f"{'ms':>9} {'solved':>6} {'unsat':>5} {'cutoff':>6}")
    print(hdr)
    print("-" * len(hdr))
    for n in (30, 40):
        for pc in (0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40):
            stats = {m: [] for m in methods}
            edges = []
            for s in seeds:
                csp = access_csp.generate(n_requests=n, n_approvers=5,
                                          p_conflict=pc, seed=s)
                edges.append(len(csp.conflicts))
                statuses = {}
                for m in methods:
                    r = timed(solve, csp, m, limit)
                    if r["status"] == "solved":
                        assert not csp.validate(r["solution"]), "invalid solution"
                    statuses[m] = r["status"]
                    stats[m].append(r)
                done = {v for v in statuses.values() if v != "cutoff"}
                assert len(done) <= 1, f"solvers disagree: {statuses}"
            for m, rs in stats.items():
                a = np.mean([r["assignments"] for r in rs])
                b = np.mean([r["backtracks"] for r in rs])
                t = np.mean([r["ms"] for r in rs])
                c = {k: sum(r["status"] == k for r in rs) for k in ("solved", "unsat", "cutoff")}
                print(f"{n:>4} {pc:>6} {np.mean(edges):>6.1f} | {m:<7} {a:>10.1f} {b:>10.1f} "
                      f"{t:>9.2f} {c['solved']:>6} {c['unsat']:>5} {c['cutoff']:>6}")
            print()


def fixed_examples():
    print("=" * 78)
    print("FIXED SMALL EXAMPLES")
    print("=" * 78)
    p = lateral_path.small_fixed()
    for name, r in (("BFS", bfs(p)), ("UCS", ucs(p)), ("A*", astar(p, p.hop_heuristic()))):
        print(f"  {name:<4} path {' -> '.join(r['path'])}  cost {r['cost']}  expanded {r['expanded']}")
    csp = access_csp.small_fixed()
    for m in ("bt", "fc", "mrv", "mrv_fc"):
        r = solve(csp, m)
        print(f"  {m:<7} {r['status']}  assignments {r['assignments']}  backtracks {r['backtracks']}  "
              f"valid {not csp.validate(r['solution']) if r['solution'] else 'n/a'}")
        if m == "mrv_fc":
            print("          " + ", ".join(f"{k}={v}" for k, v in r["solution"].items()))
    print()


if __name__ == "__main__":
    quick = "--quick" in sys.argv
    seeds = list(range(3)) if quick else list(range(10))
    limit = 10_000 if quick else 50_000
    print(f"Run started {time.strftime('%Y-%m-%d %H:%M:%S')}  seeds={seeds}")
    print(f"Python {sys.version.split()[0]}, NumPy {np.__version__}\n")
    fixed_examples()
    problem_a(seeds)
    problem_b(seeds, limit)
    print("Done.")
