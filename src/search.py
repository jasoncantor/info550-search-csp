"""Graph search algorithms for the lateral-path problem.

All three functions take a problem object with:
  start, goal, neighbors(n) -> list of (next_node, edge_cost)
and an optional heuristic h(n). They return a dict with the path,
its cost, the number of nodes expanded, and the max frontier size.
"""
import heapq
from collections import deque


def _path(parent, goal):
    out = [goal]
    while parent[out[-1]] is not None:
        out.append(parent[out[-1]])
    return out[::-1]


def _cost(problem, path):
    total = 0.0
    for a, b in zip(path, path[1:]):
        total += dict(problem.neighbors(a))[b]
    return total


def bfs(problem):
    """Breadth-first search (uninformed, ignores edge costs).
    Goal test on generation, as in the textbook version."""
    start, goal = problem.start, problem.goal
    if start == goal:
        return {"path": [start], "cost": 0.0, "expanded": 0, "max_frontier": 1}
    parent = {start: None}
    frontier = deque([start])
    expanded, max_frontier = 0, 1
    while frontier:
        node = frontier.popleft()
        expanded += 1
        for nxt, _ in problem.neighbors(node):
            if nxt in parent:
                continue
            parent[nxt] = node
            if nxt == goal:
                path = _path(parent, goal)
                return {"path": path, "cost": _cost(problem, path),
                        "expanded": expanded, "max_frontier": max_frontier}
            frontier.append(nxt)
        max_frontier = max(max_frontier, len(frontier))
    return {"path": None, "cost": float("inf"), "expanded": expanded,
            "max_frontier": max_frontier}


def best_first(problem, h=None):
    """Uniform-cost search when h is None, A* otherwise.
    Goal test on expansion so the returned path is optimal."""
    h = h or (lambda n: 0.0)
    start, goal = problem.start, problem.goal
    g = {start: 0.0}
    parent = {start: None}
    counter = 0  # tie-breaker so heapq never compares nodes
    frontier = [(h(start), counter, start)]
    closed = set()
    expanded, max_frontier = 0, 1
    while frontier:
        _, _, node = heapq.heappop(frontier)
        if node in closed:
            continue
        if node == goal:
            path = _path(parent, goal)
            return {"path": path, "cost": g[goal], "expanded": expanded,
                    "max_frontier": max_frontier}
        closed.add(node)
        expanded += 1
        for nxt, c in problem.neighbors(node):
            ng = g[node] + c
            if nxt not in g or ng < g[nxt] - 1e-12:
                g[nxt] = ng
                parent[nxt] = node
                counter += 1
                heapq.heappush(frontier, (ng + h(nxt), counter, nxt))
        max_frontier = max(max_frontier, len(frontier))
    return {"path": None, "cost": float("inf"), "expanded": expanded,
            "max_frontier": max_frontier}


def ucs(problem):
    return best_first(problem, None)


def astar(problem, h):
    return best_first(problem, h)
