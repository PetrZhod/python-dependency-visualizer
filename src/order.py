"""Порядок загрузки: зависимости раньше использующих их пакетов."""


class LoadOrder:
    """Выполнять рекурсивный DFS с тремя состояниями вершин."""

    def __init__(self, graph):
        """Запомнить граф и создать независимое состояние обхода."""
        self.graph = graph
        self.finished = set()
        self.active = []
        self.result = []

    def visit(self, name):
        """Добавить пакет после его зависимостей или сообщить о цикле."""
        if name in self.active:
            position = self.active.index(name)
            cycle = self.active[position:] + [name]
            raise ValueError("Нет порядка загрузки: цикл "
                             + " -> ".join(cycle))
        if name in self.finished:
            return
        if name not in self.graph:
            raise ValueError(f"Пакет {name} отсутствует в графе")
        self.active.append(name)
        for target in sorted(set(self.graph[name])):
            self.visit(target)
        self.active.pop()
        self.finished.add(name)
        self.result.append(name)


def dependency_order(graph, root):
    """Вернуть детерминированный порядок достижимых вершин без дублей."""
    if not graph:
        return []
    visitor = LoadOrder(graph)
    visitor.visit(root)
    return visitor.result
