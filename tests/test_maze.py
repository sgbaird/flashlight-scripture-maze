import pytest

from maze import Maze, SIZES


@pytest.mark.parametrize("size", sorted(SIZES))
@pytest.mark.parametrize("seed", range(5))
def test_every_cell_reachable_and_goal_far(size, seed):
    cols, rows = SIZES[size]
    m = Maze(cols, rows, seed=seed)
    dist, _ = m.bfs(m.start)
    assert len(dist) == cols * rows
    assert dist[m.goal] == max(dist.values())
    assert dist[m.goal] >= (cols + rows) // 2


def test_path_follows_passages_and_respects_limit():
    m = Maze(11, 6, seed=1)
    p = m.path(m.start, m.goal)
    assert p[0] == m.start and p[-1] == m.goal
    for a, b in zip(p, p[1:]):
        assert m.is_open(a, b)
    assert m.path(m.start, m.goal, limit=2) is None
    near = m.neighbors(m.start)[0]
    assert m.path(m.start, near, limit=1) == [m.start, near]


def test_items_spread_out():
    m = Maze(11, 6, seed=3)
    items = m.place_items(5)
    assert len(items) == len(set(items)) == 5
    assert m.start not in items and m.goal not in items


def test_walls_block():
    m = Maze(8, 5, seed=0)
    closed = [(a, b) for a in [(c, r) for c in range(8) for r in range(5)]
              for b in [(a[0] + 1, a[1])] if m.inside(b) and not m.is_open(a, b)]
    assert closed, "a maze should have walls"
    a, b = closed[0]
    assert b not in m.neighbors(a)
