"""Расположение вершин по расстоянию от корня без сторонних библиотек."""

from collections import deque

MARGIN = 45
MIN_WIDTH = 130
CHAR_WIDTH = 9
BOX_HEIGHT = 44
COLUMN_GAP = 65
ROW_GAP = 100
LOOP_SPACE = 90


def graph_levels(graph, root):
    """Вычислить кратчайшую глубину BFS, сохранив конечность при циклах."""
    levels = {root: 0}
    queue = deque([root])
    while queue:
        name = queue.popleft()
        for target in sorted(set(graph[name])):
            if target not in levels:
                levels[target] = levels[name] + 1
                queue.append(target)
    return levels


def graph_layout(graph, root, labels=None):
    """Вернуть координаты, размер прямоугольника и полотна SVG."""
    if not graph:
        return {}, MIN_WIDTH, (400, 150)
    levels = graph_levels(graph, root)
    rows = {}
    for name, level in levels.items():
        rows.setdefault(level, []).append(name)
    names = [(labels or {}).get(name, name) for name in graph]
    box_width = max(MIN_WIDTH, max(map(len, names))
                    * CHAR_WIDTH + 24)
    row_width = max(map(len, rows.values()))
    width = MARGIN * 2 + row_width * (box_width + COLUMN_GAP) + LOOP_SPACE
    height = MARGIN * 2 + len(rows) * (BOX_HEIGHT + ROW_GAP)
    positions = {}
    for level, names in rows.items():
        for index, name in enumerate(sorted(names)):
            x = MARGIN + index * (box_width + COLUMN_GAP)
            y = MARGIN + level * (BOX_HEIGHT + ROW_GAP)
            positions[name] = (x, y)
    return positions, box_width, (width, height)
