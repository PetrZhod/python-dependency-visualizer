"""Параметры командной строки и их проверка."""

import argparse
import re
from pathlib import Path
from urllib.parse import urlsplit

PACKAGE_PATTERN = r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?"
TEST_PATTERN = r"[A-Z]+"
MIN_PORT = 1


def build_parser():
    """Описать все пять пользовательских параметров."""
    parser = argparse.ArgumentParser(
        description="Анализ зависимостей Python-пакетов",
        allow_abbrev=False,
    )
    parser.add_argument("--package", required=True,
                        help="имя анализируемого пакета")
    parser.add_argument("--repository", required=True,
                        help="URL JSON API либо путь к тестовому файлу")
    parser.add_argument("--test-repo", action="store_true",
                        help="использовать тестовый репозиторий")
    parser.add_argument("--ascii-tree", action="store_true",
                        help="выбрать ASCII-дерево для этапа визуализации")
    parser.add_argument("--filter", default="", dest="filter_substring",
                        help="подстрока для исключения пакетов")
    return parser


def validate_package(name, test_mode=False):
    """Проверить имя реального или тестового пакета."""
    pattern = TEST_PATTERN if test_mode else PACKAGE_PATTERN
    if re.fullmatch(pattern, name) is None:
        if test_mode:
            raise ValueError("--package: нужны заглавные латинские буквы A-Z")
        raise ValueError(
            "--package: нужны латинские буквы, цифры, '.', '_' и '-'; "
            "начало и конец имени — буква или цифра"
        )


def parse_url(value):
    """Разобрать URL и проверить пробелы, кодировку и номер порта."""
    if not value or any(char.isspace() for char in value):
        raise ValueError("--repository: URL пуст или содержит пробелы")
    if any(not char.isprintable() for char in value):
        raise ValueError("--repository: недопустимые символы в URL")
    try:
        parsed = urlsplit(value)
        port = parsed.port
        host = parsed.hostname
    except ValueError as error:
        raise ValueError("--repository: некорректный URL или порт") from error
    if port is not None and port < MIN_PORT:
        raise ValueError("--repository: порт должен быть от 1 до 65535")
    return parsed, host


def validate_url(value):
    """Проверить HTTP(S) URL без обращения к серверу."""
    parsed, host = parse_url(value)
    if parsed.scheme not in {"http", "https"} or not host:
        raise ValueError("--repository: нужен URL http:// или https://")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("--repository: логин и пароль в URL не допускаются")
    if parsed.query or parsed.fragment:
        raise ValueError("--repository: нужен базовый URL без query и fragment")


def validate_repository(value, test_mode):
    """Проверить URL или доступный для чтения тестовый файл."""
    if not test_mode:
        validate_url(value)
        return
    if not value or not value.strip():
        raise ValueError("--repository: не задан путь к тестовому файлу")
    path = Path(value)
    if not path.is_file():
        raise ValueError("--repository: тестовый файл не существует")
    try:
        with path.open("rb") as stream:
            stream.read(1)
    except OSError as error:
        raise ValueError("--repository: файл недоступен для чтения") from error


def validate_filter(value):
    """Разрешить пустой фильтр и печатную непустую подстроку."""
    if value and not value.strip():
        raise ValueError("--filter: нельзя использовать одни пробелы")
    if any(not char.isprintable() for char in value):
        raise ValueError("--filter: управляющие символы не допускаются")


def parse_arguments(argv=None):
    """Прочитать параметры и вывести ошибки с кодом завершения 2."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        validate_package(args.package, args.test_repo)
        validate_repository(args.repository, args.test_repo)
        validate_filter(args.filter_substring)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    return args
