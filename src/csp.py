"""Backtracking CSP solvers: plain BT, BT+FC, BT+MRV, BT+MRV+forward checking,
and the same with least-constraining-value (LCV) ordering.
(BT+FC without MRV is included to separate the two effects.)

Metrics counted the same way for all solvers:
  assignments  values tried (var=val attempts)
  backtracks   times a variable ran out of values and search went back
A node limit stops runaway searches; a stopped run is reported as
'cutoff' rather than solved or unsatisfiable.
"""


class Cutoff(Exception):
    pass


class Solver:
    def __init__(self, csp, mrv=False, fc=False, lcv=False, limit=200_000):
        self.csp, self.mrv, self.fc, self.lcv = csp, mrv, fc, lcv
        self.limit = limit
        self.assignments = 0
        self.backtracks = 0

    def legal_values(self, var, assign, doms):
        return [v for v in doms[var] if self.csp.consistent(var, v, assign)]

    def select(self, assign, doms):
        unassigned = [v for v in self.csp.variables if v not in assign]
        if not self.mrv:
            return unassigned[0]          # static order
        if self.fc:
            # with FC, domains are already pruned of conflicts
            return min(unassigned, key=lambda v: (len(doms[v]), -len(self.csp.neighbors[v])))
        return min(unassigned,
                   key=lambda v: (len(self.legal_values(v, assign, doms)),
                                  -len(self.csp.neighbors[v])))

    def order_values(self, var, assign, doms):
        """Return values for var. With LCV, prefer values that leave the
        most options open for unassigned neighbors (C2) and that leave
        the most remaining workload slots (C3)."""
        vals = list(doms[var])
        if not self.lcv:
            return vals

        def score(val):
            if not self.csp.consistent(var, val, assign):
                return -1
            # how many neighbor domain slots would remain if var=val
            left = 0
            for n in self.csp.neighbors[var]:
                if n in assign:
                    continue
                for nv in doms[n]:
                    if nv != val:
                        left += 1
            # remaining capacity for this approver after assigning val
            load = sum(1 for x in assign.values() if x == val)
            left += max(0, self.csp.cap - load - 1)
            return left

        return sorted(vals, key=score, reverse=True)

    def forward_check(self, var, val, assign, doms):
        """Prune val from unassigned neighbors (C2). If val's approver is
        now at cap, prune it from every unassigned variable (C3)."""
        new = dict(doms)
        at_cap = sum(1 for x in assign.values() if x == val) >= self.csp.cap
        for v in self.csp.variables:
            if v in assign:
                continue
            if at_cap or v in self.csp.neighbors[var]:
                if val in new[v]:
                    new[v] = [x for x in new[v] if x != val]
                    if not new[v]:
                        return None
        return new

    def _bt(self, assign, doms):
        if len(assign) == len(self.csp.variables):
            return dict(assign)
        var = self.select(assign, doms)
        for val in self.order_values(var, assign, doms):
            if not self.csp.consistent(var, val, assign):
                continue
            self.assignments += 1
            if self.assignments > self.limit:
                raise Cutoff()
            assign[var] = val
            nd = doms
            if self.fc:
                nd = self.forward_check(var, val, assign, doms)
            if nd is not None:
                res = self._bt(assign, nd)
                if res is not None:
                    return res
            del assign[var]
        self.backtracks += 1
        return None

    def solve(self):
        try:
            sol = self._bt({}, dict(self.csp.domains))
            return {"status": "solved" if sol else "unsat", "solution": sol}
        except Cutoff:
            return {"status": "cutoff", "solution": None}


def solve(csp, method, limit=200_000):
    mrv = method in ("mrv", "mrv_fc", "mrv_fc_lcv")
    fc = method in ("fc", "mrv_fc", "mrv_fc_lcv")
    lcv = method in ("lcv", "mrv_fc_lcv")
    s = Solver(csp, mrv=mrv, fc=fc, lcv=lcv, limit=limit)
    out = s.solve()
    out.update(assignments=s.assignments, backtracks=s.backtracks)
    return out
