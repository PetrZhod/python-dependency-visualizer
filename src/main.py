"""Этап 2: получение и вывод всех прямых объявленных зависимостей."""

import sys

from config import parse_arguments
from repository import PyPIRepository

EXIT_ERROR = 1


def run(args):
    """Получить зависимости через JSON API, не вызывая менеджер пакетов."""
    if args.test_repo:
        raise ValueError("Чтение тестового графа реализуется на этапе 3")
    repository = PyPIRepository(args.repository)
    dependencies = repository.dependencies(args.package)
    print(f"Прямые зависимости {repository.normalize(args.package)}:")
    if not dependencies:
        print("Объявленных зависимостей нет")
    for declaration in dependencies:
        print(declaration)


def main(argv=None):
    """Проверить параметры и сообщить о сетевой ошибке без traceback."""
    args = parse_arguments(argv)
    try:
        run(args)
    except (ValueError, OSError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
