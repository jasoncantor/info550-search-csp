# Classical AI Search and CSP on Cyber-Themed Problems

INFO 550 / ISTA 450 course project (Fall 2026), Jason Mitchell Cantor.

This project compares course algorithms across two problem families drawn
from cybersecurity. All data is synthetic and generated from fixed seeds.

## Problem A: lateral-path search
A directed network of hosts split into five segments (entry side to the
high-value asset side). Edges go mostly forward one segment, sometimes
within a segment, and rarely back. Each edge cost is `1 + risk`, where
risk stands for detection risk or latency of that hop. The task is to
find the cheapest path from the entry host to the high-value asset.

Algorithms (in `src/search.py`):
- **BFS**: uninformed, ignores costs (goal test on generation).
- **Uniform-Cost Search (UCS)**: optimal, no heuristic.
- **A\***: two admissible heuristics for comparison:
  - `hop_heuristic`: `h(n) = fewest hops from n to the goal * cheapest edge cost`.
    Hops come from one reverse BFS from the goal, and that setup time is
    included in the A* timing.
  - `layer_heuristic`: `h(n) = remaining segment distance * cheapest edge cost`.
    Weaker than the hop heuristic, so it expands more nodes, but still
    returns optimal paths.

Scaling knobs: number of hosts, edge density, and `risk_spread` (how much
edge costs vary, cost in `[1, 1 + risk_spread]`).

## Problem B: privileged-access approval CSP
Adapted from a constraint model I built for CYBR 484.
- Variables: privileged-access requests.
- Domains: approvers allowed to sign off on each request.
- C1 separation of duty (unary): no approver from the requester's team,
  and no approver who already holds the requested privilege.
- C2 conflict (binary): requests on the same system or change chain need
  different approvers, so one person cannot approve a whole escalation path.
- C3 workload (global): each approver signs at most `cap` requests.

Tightness is controlled by `p_conflict` (chance two requests conflict).

Algorithms (in `src/csp.py`):
- **bt**: plain backtracking, static variable order.
- **fc**: backtracking + forward checking (added to separate the effects).
- **mrv**: backtracking + minimum remaining values.
- **mrv_fc**: backtracking + MRV + forward checking.
- **mrv_fc_lcv**: MRV + forward checking + least-constraining-value ordering.
- **lcv**: plain backtracking with LCV value ordering only.

A node limit (50,000 assignments) stops runaway searches; those runs are
reported as `cutoff`, not as solved or unsatisfiable.

## Hypotheses
- **H1 (A* vs UCS).** A* expands fewer nodes than UCS on every setting, and
  the savings are biggest when `risk_spread` is low, because then the hop
  heuristic is close to the true cost-to-go. A weaker layer heuristic should
  sit between hop-A* and UCS.
- **H2 (BFS path quality).** BFS expands fewer nodes than UCS but returns
  worse paths, and its cost gap grows with density and cost spread,
  because more alternative routes means the fewest-hop route is less
  likely to be the cheapest.
- **H3 (CSP heuristics).** MRV and forward checking cut assignments and
  backtracks versus plain BT, and the gap is largest near the
  solvable-to-unsolvable transition, where plain BT thrashes. LCV should
  help most on the harder solvable instances.

## Layout
```
src/search.py              BFS, UCS, A*
src/csp.py                 BT, BT+FC, BT+MRV, BT+MRV+FC, LCV variants
problems/lateral_path.py   lateral-path generator + fixed 8-host example
problems/access_csp.py     access-approval CSP generator + fixed 5-request example
tests/test_basic.py        checks UCS/A* against Dijkstra, CSP against brute force
experiments.py             full comparison run (original progress-report suite)
compare_progress.py        focused hop vs layer and LCV comparison
results/nov9_comparison.txt  measured output from compare_progress.py
results_run.txt            saved output of the original full run
```

## How to run
Python 3 with NumPy (only used for summary statistics).
```
pip install -r requirements.txt
python -m tests.test_basic           # correctness checks
python experiments.py                # full run, about 25 seconds
python experiments.py --quick        # 3 seeds, a few seconds
python compare_progress.py           # focused progress comparison
```

## Metrics
- Search: nodes expanded, path cost, cost ratio vs optimal, percent of
  runs where the path was optimal, wall time (ms).
- CSP: assignments tried, backtracks, wall time (ms), and counts of
  solved / unsat / cutoff runs. Note: with forward checking, a domain
  wipe-out rejects a value before recursing, so it is not counted as a
  backtrack; compare assignments first.

## Progress toward Final Report
Final report due December 4, 2026.

### Done
- Problem generators, BFS, UCS, A*, and four CSP solvers (progress report).
- Correctness tests against Dijkstra and brute-force CSP enumeration.
- First full experiment suite and `results_run.txt` (Nov 6).
- Extended edge-case tests (start=goal, unreachable goal, partial validate).
- Second A* heuristic (`layer_heuristic`) for heuristic-quality comparison.
- Least-constraining-value ordering (`mrv_fc_lcv`, `lcv`).
- Focused comparison run in `results/nov9_comparison.txt` (Nov 9):
  - On 500 hosts, density 0.05, spread 0.5, A*hop used 3.8% of UCS nodes;
    A*layer used 33.4%. Both stayed optimal.
  - On 30 requests at p_conflict 0.15, mrv_fc_lcv solved all 5 seeds with
    30.0 mean assignments (no backtracks); plain BT averaged 4981.2.
  - On 40 requests at p_conflict 0.20, mrv_fc_lcv cut mean assignments
    from 109.4 (mrv_fc) to 95.6.

### Remaining
- Plots (matplotlib) and repeated timing runs to reduce noise.
- More instance sizes and seeds for the final tables.
- Closer look at MRV degree tie-breaking versus LCV on hard CSP bands.
- Optional extension if time allows: adversarial search or a small MDP
  version of the lateral-path problem.
- Write the full hypothesis analysis for the final report.

### Final report outline (draft)
1. Introduction and problem motivation (cyber-themed, course algorithms).
2. Problem A definition, algorithms, and heuristics (hop vs layer).
3. Problem B definition, constraints, and solver variants (including LCV).
4. Experimental design (seeds, limits, metrics).
5. Results for H1, H2, and H3, with tables and plots.
6. Discussion: what worked, surprises (MRV vs FC wall time, LCV gains).
7. Limitations and future work.
8. Conclusion.
