"""Grid mazes: generation, paths, and placing things to collect. No pygame or OpenCV here."""
import random
from collections import deque

SIZES = {"small": (8, 5), "medium": (11, 6), "large": (14, 8)}  # (columns, rows) for a 16:9 wall
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


class Maze:
    """A maze on a cols x rows grid of cells (c, r). Passages are the open edges between cells."""

    def __init__(self, cols, rows, seed=None, loops=0.08):
        self.cols, self.rows = cols, rows
        self.rng = random.Random(seed)
        self.passages = set()
        self._carve()
        self._add_loops(loops)
        self.start = (0, rows - 1)
        dist, _ = self.bfs(self.start)
        self.goal = max(dist, key=lambda cell: (dist[cell], cell[0]))

    @staticmethod
    def _edge(a, b):
        return (a, b) if a <= b else (b, a)

    def inside(self, cell):
        return 0 <= cell[0] < self.cols and 0 <= cell[1] < self.rows

    def _carve(self):
        """Depth-first (recursive backtracker) maze: one path between any two cells."""
        start = (self.rng.randrange(self.cols), self.rng.randrange(self.rows))
        seen, stack = {start}, [start]
        while stack:
            c, r = stack[-1]
            options = [(c + dc, r + dr) for dc, dr in DIRS
                       if self.inside((c + dc, r + dr)) and (c + dc, r + dr) not in seen]
            if not options:
                stack.pop()
                continue
            nxt = self.rng.choice(options)
            self.passages.add(self._edge((c, r), nxt))
            seen.add(nxt)
            stack.append(nxt)

    def _add_loops(self, fraction):
        """Open a few extra walls so there is sometimes more than one way (kinder for children)."""
        walls = [self._edge((c, r), (c + dc, r + dr))
                 for c in range(self.cols) for r in range(self.rows) for dc, dr in ((1, 0), (0, 1))
                 if self.inside((c + dc, r + dr)) and self._edge((c, r), (c + dc, r + dr)) not in self.passages]
        self.rng.shuffle(walls)
        for e in walls[:int(len(walls) * fraction)]:
            self.passages.add(e)

    def is_open(self, a, b):
        return self._edge(a, b) in self.passages

    def neighbors(self, cell):
        c, r = cell
        return [(c + dc, r + dr) for dc, dr in DIRS
                if self.inside((c + dc, r + dr)) and self.is_open(cell, (c + dc, r + dr))]

    def bfs(self, start, limit=None):
        dist, parent = {start: 0}, {start: None}
        q = deque([start])
        while q:
            cur = q.popleft()
            if limit is not None and dist[cur] >= limit:
                continue
            for n in self.neighbors(cur):
                if n not in dist:
                    dist[n] = dist[cur] + 1
                    parent[n] = cur
                    q.append(n)
        return dist, parent

    def path(self, a, b, limit=None):
        """Cells from a to b through open passages (inclusive), or None if b is farther than limit."""
        dist, parent = self.bfs(a, limit)
        if b not in dist:
            return None
        out = [b]
        while out[-1] != a:
            out.append(parent[out[-1]])
        return out[::-1]

    def place_items(self, count):
        """Spread `count` cells over the maze, away from the start, the goal and each other."""
        if count <= 0:
            return []
        dist, _ = self.bfs(self.start)
        far = max(dist.values())
        candidates = [cell for cell, d in dist.items()
                      if 0.2 * far <= d and cell not in (self.start, self.goal)]
        chosen = []
        for _ in range(count):
            def score(cell):
                gaps = [abs(cell[0] - o[0]) + abs(cell[1] - o[1]) for o in chosen + [self.start, self.goal]]
                return min(gaps) + self.rng.random() * 0.5
            pick = max((c for c in candidates if c not in chosen), key=score, default=None)
            if pick is None:
                break
            chosen.append(pick)
        return chosen
