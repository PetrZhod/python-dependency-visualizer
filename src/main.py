"""Этап 4: порядок загрузки зависимостей заданного пакета."""

import sys

from config import parse_arguments
from graph import GraphBuilder
from local_repository import TestRepository
from order import dependency_order
from repository import PyPIRepository

EXIT_ERROR = 1


def run(args):
    """Построить граф и вывести зависимости раньше использующих их пакетов."""
    if args.test_repo:
        repository = TestRepository(args.repository)
    else:
        repository = PyPIRepository(args.repository)
    builder = GraphBuilder(repository, args.filter_substring)
    graph = builder.build(args.package)
    order = dependency_order(graph, repository.normalize(args.package))
    if not order:
        print("Корневой пакет исключён фильтром")
        return
    print("Порядок загрузки: " + " -> ".join(order))


def main(argv=None):
    """Обработать параметры, циклы, слишком глубокий граф и ошибки данных."""
    args = parse_arguments(argv)
    try:
        run(args)
    except RecursionError:
        print("Ошибка: граф слишком глубок для рекурсивного DFS",
              file=sys.stderr)
        return EXIT_ERROR
    except (ValueError, OSError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
