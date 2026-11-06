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
- **A\***: `h(n) = fewest hops from n to the goal * cheapest edge cost`.
  Every hop costs at least the cheapest edge, so h never overestimates
  (admissible). Hops come from one reverse BFS from the goal, and that
  setup time is included in the A* timing.

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

A node limit (50,000 assignments) stops runaway searches; those runs are
reported as `cutoff`, not as solved or unsatisfiable.

## Hypotheses
- **H1 (A* vs UCS).** A* expands fewer nodes than UCS on every setting, and
  the savings are biggest when `risk_spread` is low, because then the hop
  heuristic is close to the true cost-to-go.
- **H2 (BFS path quality).** BFS expands fewer nodes than UCS but returns
  worse paths, and its cost gap grows with density and cost spread,
  because more alternative routes means the fewest-hop route is less
  likely to be the cheapest.
- **H3 (CSP heuristics).** MRV and forward checking cut assignments and
  backtracks versus plain BT, and the gap is largest near the
  solvable-to-unsolvable transition, where plain BT thrashes.

## Layout
```
src/search.py            BFS, UCS, A*
src/csp.py               BT, BT+FC, BT+MRV, BT+MRV+FC
problems/lateral_path.py lateral-path generator + fixed 8-host example
problems/access_csp.py   access-approval CSP generator + fixed 5-request example
tests/test_basic.py      checks UCS/A* against Dijkstra, CSP against brute force
experiments.py           runs all comparisons and prints metrics
results_run.txt          saved output of the full run
```

## How to run
Python 3 with NumPy (only used for summary statistics).
```
pip install -r requirements.txt
python -m tests.test_basic      # correctness checks
python experiments.py           # full run, about 25 seconds
python experiments.py --quick   # 3 seeds, a few seconds
```

## Metrics
- Search: nodes expanded, path cost, cost ratio vs optimal, percent of
  runs where the path was optimal, wall time (ms).
- CSP: assignments tried, backtracks, wall time (ms), and counts of
  solved / unsat / cutoff runs. Note: with forward checking, a domain
  wipe-out rejects a value before recursing, so it is not counted as a
  backtrack; compare assignments first.

## Status
Progress-report stage: problem code and all algorithms run, tests pass,
and a first round of results is in `results_run.txt`. Planned for the
final report: more instance sizes, plots, repeated timing, and an
adversarial-search or MDP/RL extension if time allows.
