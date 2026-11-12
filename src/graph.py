"""Рекурсивный DFS для транзитивного графа с фильтром и циклами."""

from repository import requirement_name


class GraphBuilder:
    """Строить только достижимую часть графа и фиксировать обратные рёбра."""

    def __init__(self, repository, substring=""):
        """Запомнить источник, фильтр и состояние одного построения."""
        self.repository = repository
        self.substring = substring.casefold()
        self.graph = {}
        self.active = []
        self.cycles = []

    def excluded(self, name):
        """Проверить подстроку без учёта регистра в имени пакета."""
        return bool(self.substring and self.substring in name.casefold())

    def build(self, root):
        """Сбросить предыдущее состояние и рекурсивно обойти корень."""
        self.graph = {}
        self.active = []
        self.cycles = []
        self.visit(self.repository.normalize(root))
        return self.graph

    def visit(self, name):
        """Выполнить рекурсивный DFS, посещая каждую вершину один раз."""
        if self.excluded(name) or name in self.graph:
            return
        self.graph[name] = []
        self.active.append(name)
        declarations = self.repository.dependencies(name)
        targets = {self.repository.normalize(requirement_name(item))
                   for item in declarations}
        for target in sorted(targets):
            self.connect(name, target)
        self.active.pop()

    def connect(self, source, target):
        """Добавить разрешённое ребро и распознать цикл в активном пути."""
        if self.excluded(target):
            return
        self.graph[source].append(target)
        if target in self.active:
            position = self.active.index(target)
            self.cycles.append(tuple(self.active[position:] + [target]))
        else:
            self.visit(target)


def print_graph(builder):
    """Показать список смежности и найденные DFS циклические пути."""
    if not builder.graph:
        print("Корневой пакет исключён фильтром")
    for name, dependencies in sorted(builder.graph.items()):
        targets = ", ".join(dependencies) if dependencies else "(нет)"
        print(f"{name} -> {targets}")
    for cycle in builder.cycles:
        print("Цикл: " + " -> ".join(cycle))
