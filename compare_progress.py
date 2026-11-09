"""Focused comparison for final-report progress.

Compares BFS, UCS, A* (hop heuristic), and A* (layer heuristic) on
lateral-path instances, and BT / FC / MRV / MRV+FC / MRV+FC+LCV on
access-approval CSP instances. Writes a plain-text results table.

Usage:  python compare_progress.py
        python compare_progress.py --out results/nov9_comparison.txt
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np

from src.search import bfs, ucs, astar
from src.csp import solve
from problems import lateral_path, access_csp


def timed(fn, *args):
    t0 = time.perf_counter()
    out = fn(*args)
    out["ms"] = (time.perf_counter() - t0) * 1000
    return out


def run_search(seeds, out):
    out.append("=" * 78)
    out.append("SEARCH: BFS vs UCS vs A*(hop) vs A*(layer)")
    out.append("Means over seeds. ratio = path cost / UCS optimal cost.")
    out.append("=" * 78)
    hdr = (f"{'hosts':>5} {'dens':>5} {'spread':>6} | {'alg':<8} "
           f"{'expanded':>9} {'cost':>7} {'ratio':>6} {'ms':>7}")
    out.append(hdr)
    out.append("-" * len(hdr))
    settings = [
        (200, 0.05, 0.5),
        (200, 0.05, 4.0),
        (200, 0.10, 4.0),
        (500, 0.05, 0.5),
        (500, 0.05, 4.0),
        (500, 0.10, 4.0),
    ]
    for n, dens, spread in settings:
        buckets = {k: [] for k in ("BFS", "UCS", "A*hop", "A*layer")}
        for s in seeds:
            p = lateral_path.generate(n_hosts=n, density=dens,
                                      risk_spread=spread, seed=s)
            r_bfs = timed(bfs, p)
            r_ucs = timed(ucs, p)
            r_hop = timed(lambda q: astar(q, q.hop_heuristic()), p)
            r_lay = timed(lambda q: astar(q, q.layer_heuristic()), p)
            opt = r_ucs["cost"]
            assert abs(r_hop["cost"] - opt) < 1e-9
            assert abs(r_lay["cost"] - opt) < 1e-9
            for name, r in (("BFS", r_bfs), ("UCS", r_ucs),
                            ("A*hop", r_hop), ("A*layer", r_lay)):
                buckets[name].append((r["expanded"], r["cost"],
                                      r["cost"] / opt, r["ms"]))
        for name, vals in buckets.items():
            a = np.array(vals)
            out.append(
                f"{n:>5} {dens:>5} {spread:>6} | {name:<8} "
                f"{a[:,0].mean():>9.1f} {a[:,1].mean():>7.2f} "
                f"{a[:,2].mean():>6.3f} {a[:,3].mean():>7.2f}"
            )
        # A* hop vs layer vs UCS node counts
        u = np.array(buckets["UCS"])[:, 0].mean()
        h = np.array(buckets["A*hop"])[:, 0].mean()
        l = np.array(buckets["A*layer"])[:, 0].mean()
        out.append(
            f"      share of UCS nodes: A*hop={100*h/u:5.1f}%  "
            f"A*layer={100*l/u:5.1f}%"
        )
        out.append("")
    out.append("")


def run_csp(seeds, limit, out):
    methods = ("bt", "fc", "mrv", "mrv_fc", "mrv_fc_lcv")
    out.append("=" * 78)
    out.append("CSP: BT vs FC vs MRV vs MRV+FC vs MRV+FC+LCV")
    out.append(f"5 approvers, node limit {limit:,} assignments per run.")
    out.append("=" * 78)
    hdr = (f"{'reqs':>4} {'p_conf':>6} | {'method':<10} {'assign':>10} "
           f"{'backtr':>10} {'ms':>9} {'solved':>6} {'unsat':>5} {'cutoff':>6}")
    out.append(hdr)
    out.append("-" * len(hdr))
    for n in (30, 40):
        for pc in (0.15, 0.20, 0.25, 0.30):
            stats = {m: [] for m in methods}
            for s in seeds:
                csp = access_csp.generate(n_requests=n, n_approvers=5,
                                          p_conflict=pc, seed=s)
                statuses = {}
                for m in methods:
                    r = timed(solve, csp, m, limit)
                    if r["status"] == "solved":
                        assert not csp.validate(r["solution"])
                    statuses[m] = r["status"]
                    stats[m].append(r)
                done = {v for v in statuses.values() if v != "cutoff"}
                assert len(done) <= 1, f"solvers disagree: {statuses}"
            for m, rs in stats.items():
                a = np.mean([r["assignments"] for r in rs])
                b = np.mean([r["backtracks"] for r in rs])
                t = np.mean([r["ms"] for r in rs])
                c = {k: sum(r["status"] == k for r in rs)
                     for k in ("solved", "unsat", "cutoff")}
                out.append(
                    f"{n:>4} {pc:>6} | {m:<10} {a:>10.1f} {b:>10.1f} "
                    f"{t:>9.2f} {c['solved']:>6} {c['unsat']:>5} {c['cutoff']:>6}"
                )
            out.append("")
    out.append("")


def fixed_examples(out):
    out.append("=" * 78)
    out.append("FIXED SMALL EXAMPLES")
    out.append("=" * 78)
    p = lateral_path.small_fixed()
    for name, r in (
        ("BFS", bfs(p)),
        ("UCS", ucs(p)),
        ("A*hop", astar(p, p.hop_heuristic())),
        ("A*layer", astar(p, p.layer_heuristic())),
    ):
        out.append(
            f"  {name:<8} path {' -> '.join(r['path'])}  "
            f"cost {r['cost']}  expanded {r['expanded']}"
        )
    csp = access_csp.small_fixed()
    for m in ("bt", "fc", "mrv", "mrv_fc", "mrv_fc_lcv"):
        r = solve(csp, m)
        valid = (not csp.validate(r["solution"])) if r["solution"] else "n/a"
        out.append(
            f"  {m:<10} {r['status']}  assignments {r['assignments']}  "
            f"backtracks {r['backtracks']}  valid {valid}"
        )
    out.append("")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/nov9_comparison.txt")
    ap.add_argument("--seeds", type=int, default=5)
    args = ap.parse_args()
    seeds = list(range(args.seeds))
    limit = 50_000
    lines = [
        f"Run started {time.strftime('%Y-%m-%d %H:%M:%S')}  seeds={seeds}",
        f"Python {sys.version.split()[0]}, NumPy {np.__version__}",
        "",
    ]
    fixed_examples(lines)
    run_search(seeds, lines)
    run_csp(seeds, limit, lines)
    lines.append("Done.")
    text = "\n".join(lines) + "\n"
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    print(text)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
