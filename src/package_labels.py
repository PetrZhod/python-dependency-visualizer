"""Подписи реальных пакетов с версией исследованных метаданных."""


def package_labels(repository, graph):
    """Сохранить имена вершин и добавить версии только в их подписи."""
    labels = {}
    for name in graph:
        version = repository.version(name) or "версия не указана"
        labels[name] = f"{name} ({version})"
    return labels
