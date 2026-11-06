"""Privileged-access approval CSP (adapted from my CYBR 484 review CSP).

Variables: privileged-access requests (for example "grant Domain Admin to
           user X for change ticket Y").
Domain:    the approvers who could sign off on each request.
Constraints:
  C1 separation of duty (unary): an approver cannot approve a request from
     their own team, and an approver who already holds the requested
     privilege cannot approve it. Applied when domains are built.
  C2 conflict (binary): two requests that touch the same system or are
     part of the same change chain must have different approvers, so no
     single person can approve a full privilege escalation path.
  C3 workload (global): each approver can approve at most `cap` requests.
Tightness is controlled by the conflict probability p_conflict.
Everything here is synthetic.
"""
import random


class AccessCSP:
    def __init__(self, variables, domains, conflicts, cap, name=""):
        self.variables = list(variables)
        self.domains = {v: list(d) for v, d in domains.items()}
        self.neighbors = {v: set() for v in self.variables}
        for a, b in conflicts:
            self.neighbors[a].add(b)
            self.neighbors[b].add(a)
        self.conflicts = list(conflicts)
        self.cap = cap
        self.name = name

    def consistent(self, var, val, assign):
        """Check var=val against the current partial assignment."""
        for n in self.neighbors[var]:
            if assign.get(n) == val:
                return False          # C2
        load = sum(1 for x in assign.values() if x == val)
        return load < self.cap        # C3

    def validate(self, assign):
        errs = []
        for v in self.variables:
            if v not in assign:
                errs.append(f"{v} unassigned")
            elif assign[v] not in self.domains[v]:
                errs.append(f"{v} value outside domain (SoD)")
        for a, b in self.conflicts:
            if a in assign and assign.get(a) == assign.get(b):
                errs.append(f"{a},{b} same approver")
        counts = {}
        for x in assign.values():
            counts[x] = counts.get(x, 0) + 1
        if any(c > self.cap for c in counts.values()):
            errs.append("cap exceeded")
        return errs


def generate(n_requests=30, n_approvers=6, n_teams=4, p_conflict=0.2,
             holds_rate=0.10, cap=None, seed=0):
    rng = random.Random(seed)
    approvers = [f"A{i}" for i in range(n_approvers)]
    approver_team = {a: i % n_teams for i, a in enumerate(approvers)}
    reqs = [f"R{i:02d}" for i in range(n_requests)]
    domains = {}
    for r in reqs:
        team = rng.randrange(n_teams)
        dom = [a for a in approvers
               if approver_team[a] != team          # C1 own team
               and rng.random() >= holds_rate]      # C1 already holds it
        if len(dom) < 2:  # keep at least two eligible approvers
            pool = [a for a in approvers if approver_team[a] != team]
            dom = sorted(set(dom) | set(rng.sample(pool, 2)), key=approvers.index)
        domains[r] = dom
    conflicts = [(a, b) for i, a in enumerate(reqs) for b in reqs[i + 1:]
                 if rng.random() < p_conflict]
    if cap is None:
        cap = -(-n_requests // n_approvers) + 2      # ceil + slack
    return AccessCSP(reqs, domains, conflicts, cap,
                     name=f"n{n_requests}_m{n_approvers}_p{p_conflict}_s{seed}")


def small_fixed():
    """Tiny 5-request instance used in tests and the README."""
    variables = ["DA_grant", "CloudAdmin", "DB_root", "FW_change", "Backup_admin"]
    domains = {
        "DA_grant":     ["Chen", "Blair"],      # Alex holds DA (SoD)
        "CloudAdmin":   ["Alex", "Chen"],       # Blair holds Cloud Admin
        "DB_root":      ["Alex", "Blair", "Chen"],
        "FW_change":    ["Alex", "Chen"],
        "Backup_admin": ["Blair", "Chen"],
    }
    conflicts = [("DA_grant", "CloudAdmin"), ("DA_grant", "DB_root"),
                 ("CloudAdmin", "FW_change"), ("DB_root", "Backup_admin"),
                 ("FW_change", "DB_root")]
    return AccessCSP(variables, domains, conflicts, cap=2, name="fixed5")
