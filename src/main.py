"""Этап 1: вывод проверенной конфигурации CLI."""

from config import parse_arguments


def main(argv=None):
    """Показать пять настроек в формате ключ-значение."""
    args = parse_arguments(argv)
    print(f"package={args.package}")
    print(f"repository={args.repository}")
    print(f"test_repo={args.test_repo}")
    print(f"ascii_tree={args.ascii_tree}")
    print(f"filter={args.filter_substring}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
