"""ASCII-дерево с конечным обходом циклов и общих зависимостей."""


class AsciiTree:
    """Разворачивать ветвь один раз, отмечая циклы и повторные вершины."""

    def __init__(self, graph, labels=None):
        """Создать состояние одного представления графа."""
        self.graph = graph
        self.labels = labels or {}
        self.seen = set()
        self.active = set()
        self.lines = []

    def visit(self, name, prefix="", connector="", last=True):
        """Вывести вершину и рекурсивно раскрыть только новую ветвь."""
        display = self.labels.get(name, name)
        if name in self.active:
            self.lines.append(prefix + connector + display + " [цикл]")
            return
        if name in self.seen:
            self.lines.append(prefix + connector + display + " [повтор]")
            return
        self.lines.append(prefix + connector + display)
        self.seen.add(name)
        self.active.add(name)
        padding = "    " if last else "|   "
        child_prefix = prefix + padding if connector else prefix
        targets = sorted(set(self.graph[name]))
        for index, target in enumerate(targets):
            is_last = index == len(targets) - 1
            branch = "`-- " if is_last else "|-- "
            self.visit(target, child_prefix, branch, is_last)
        self.active.remove(name)


def format_ascii(graph, root, labels=None):
    """Вернуть ASCII-дерево без дублирования раскрытых подграфов."""
    if not graph:
        return "(пустой граф)"
    tree = AsciiTree(graph, labels)
    tree.visit(root)
    return "\n".join(tree.lines)
