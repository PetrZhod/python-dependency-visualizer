"""Загрузка тестового графа из JSON без сетевых запросов."""

import json
from pathlib import Path

from config import validate_package


def unique_object(pairs):
    """Отклонить повторяющиеся имена пакетов в объекте JSON."""
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError(f"Имя пакета повторяется: {name}")
        result[name] = value
    return result


def validate_graph(data):
    """Проверить заглавные имена, списки рёбер и существование целей."""
    if not isinstance(data, dict):
        raise ValueError("Тестовый репозиторий должен быть объектом JSON")
    for name, targets in data.items():
        validate_package(name, True)
        if not isinstance(targets, list):
            raise ValueError(f"Зависимости {name} должны быть списком")
        for target in targets:
            if not isinstance(target, str):
                raise ValueError(f"Зависимости {name} должны быть строками")
            validate_package(target, True)
            if target not in data:
                raise ValueError(f"Пакет {target} отсутствует в репозитории")
    return {name: sorted(set(targets)) for name, targets in data.items()}


class TestRepository:
    """Предоставлять зависимости тестовых пакетов с тем же интерфейсом."""

    def __init__(self, path):
        """Прочитать UTF-8 JSON и проверить весь тестовый репозиторий."""
        try:
            text = Path(path).read_text(encoding="utf-8-sig")
            data = json.loads(text, object_pairs_hook=unique_object)
        except (OSError, ValueError, UnicodeError) as error:
            raise ValueError(
                f"Не удалось загрузить тестовый граф: {error}"
            ) from error
        self.graph = validate_graph(data)

    def normalize(self, name):
        """Сохранить регистр заглавного тестового имени."""
        validate_package(name, True)
        return name

    def dependencies(self, name):
        """Вернуть независимую копию списка или ошибку отсутствующего пакета."""
        name = self.normalize(name)
        if name not in self.graph:
            raise ValueError(f"Пакет {name} отсутствует в тестовом репозитории")
        return list(self.graph[name])
