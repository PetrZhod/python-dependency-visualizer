"""Этап 5: D2, изображение графа и дополнительное ASCII-дерево."""

import sys

from ascii_tree import format_ascii
from config import parse_arguments
from d2_format import to_d2
from graph import GraphBuilder
from package_labels import package_labels
from local_repository import TestRepository
from repository import PyPIRepository
from visualization import publish_graph

EXIT_ERROR = 1


def run(args):
    """Построить граф, сформировать D2, показать изображение и дерево."""
    if args.test_repo:
        repository = TestRepository(args.repository)
    else:
        repository = PyPIRepository(args.repository)
    builder = GraphBuilder(repository, args.filter_substring)
    graph = builder.build(args.package)
    root = repository.normalize(args.package)
    if not graph:
        print("Корневой пакет исключён фильтром")
    options = {} if args.test_repo else {
        "labels": package_labels(repository, graph),
    }
    print(to_d2(graph, **options), end="")
    if args.ascii_tree:
        print(format_ascii(graph, root, **options))
    publish_graph(graph, root, **options)


def main(argv=None):
    """Обработать ошибки данных, записи файлов и открытия изображения."""
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
