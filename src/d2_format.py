"""Детерминированное представление графа на языке диаграмм D2."""

import json


def to_d2(graph):
    """Сохранить все вершины и рёбра с безопасными идентификаторами D2."""
    names = sorted(graph)
    identifiers = {name: f"n{index}" for index, name in enumerate(names)}
    lines = ["direction: down"]
    for name in names:
        label = json.dumps(name, ensure_ascii=False)
        lines.append(f"{identifiers[name]}: {label}")
    for name in names:
        for target in sorted(set(graph[name])):
            lines.append(f"{identifiers[name]} -> {identifiers[target]}")
    return "\n".join(lines) + "\n"
