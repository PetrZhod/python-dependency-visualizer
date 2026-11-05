"""Этап 3: рекурсивное построение графа зависимостей."""

import sys

from config import parse_arguments
from graph import GraphBuilder, print_graph
from repository import PyPIRepository
from local_repository import TestRepository

EXIT_ERROR = 1


def run(args):
    """Выбрать реальный или тестовый источник и построить граф."""
    if args.test_repo:
        repository = TestRepository(args.repository)
    else:
        repository = PyPIRepository(args.repository)
    builder = GraphBuilder(repository, args.filter_substring)
    builder.build(args.package)
    print_graph(builder)


def main(argv=None):
    """Проверить параметры, построить граф и обработать ошибки."""
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
