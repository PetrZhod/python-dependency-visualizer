"""Проверки всех пяти параметров и ошибок конфигурации."""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import config


class ConfigTests(unittest.TestCase):
    """Проверять допустимые и ошибочные параметры без сетевых запросов."""

    def valid_arguments(self):
        """Вернуть минимальную корректную командную строку."""
        return ["--package", "requests", "--repository",
                "https://pypi.org/pypi"]

    def assert_invalid(self, arguments, text=""):
        """Проверить код 2 и текст ошибки argparse."""
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            with self.assertRaises(SystemExit) as caught:
                config.parse_arguments(arguments)
        self.assertEqual(caught.exception.code, 2)
        self.assertIn(text, output.getvalue())

    def test_defaults(self):
        """По умолчанию выключить оба флага и фильтр."""
        args = config.parse_arguments(self.valid_arguments())
        self.assertFalse(args.test_repo)
        self.assertFalse(args.ascii_tree)
        self.assertEqual(args.filter_substring, "")

    def test_all_options(self):
        """Принять все параметры и путь, содержащий пробелы."""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "test repository.json"
            path.write_text('{"A": []}', encoding="utf-8")
            args = config.parse_arguments([
                "--package", "A", "--repository", str(path), "--test-repo",
                "--ascii-tree", "--filter", "B",
            ])
        self.assertTrue(args.test_repo)
        self.assertTrue(args.ascii_tree)
        self.assertEqual(args.filter_substring, "B")

    def test_required(self):
        """Потребовать имя пакета и адрес репозитория."""
        for args in ([], ["--package", "a"],
                     ["--repository", "https://example.org"]):
            with self.subTest(args=args):
                self.assert_invalid(args)

    def test_package_names(self):
        """Принять корректные имена пакетов Python."""
        for name in ("a", "Requests", "my-package", "a_b", "a.b", "1a"):
            config.validate_package(name)

    def test_invalid_package_names(self):
        """Отклонить пустые имена, пробелы и ограничения версий."""
        for name in ("", "bad name", "_a", "a-", "a/b", "a>=1", "пакет"):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    config.validate_package(name)

    def test_test_names(self):
        """В тестовом режиме требовать заглавные латинские буквы."""
        config.validate_package("ABC", True)
        for name in ("a", "A1", "А", "A-B"):
            with self.assertRaises(ValueError):
                config.validate_package(name, True)

    def test_urls(self):
        """Принять HTTP, HTTPS, порт и IPv6."""
        for value in ("https://pypi.org", "http://localhost:8000/pypi",
                      "https://[::1]/pypi"):
            config.validate_url(value)

    def test_invalid_urls(self):
        """Отклонить неверные схемы, порты, хосты и реквизиты."""
        values = ("", "ftp://host", "https://", "file.json", "https://a b",
                  "https://x:abc", "https://x:65536", "https://x:0",
                  "https://[bad", "https://u:p@host", "https://x?q=1",
                  "https://x/#fragment", "https://x/\x00")
        for value in values:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    config.validate_url(value)

    def test_bad_test_path(self):
        """Отклонить пустой путь, папку и отсутствующий файл."""
        with tempfile.TemporaryDirectory() as folder:
            for value in ("", " ", folder, str(Path(folder) / "missing")):
                with self.assertRaises(ValueError):
                    config.validate_repository(value, True)

    def test_unreadable_file(self):
        """Сообщить об ошибке доступа к тестовому файлу."""
        with patch.object(Path, "is_file", return_value=True):
            with patch.object(Path, "open", side_effect=PermissionError):
                with self.assertRaises(ValueError):
                    config.validate_repository("exists.json", True)

    def test_filter(self):
        """Принять пустой фильтр и непустую подстроку."""
        for value in ("", "cert", "B", "a-b"):
            config.validate_filter(value)
        for value in (" ", "a\nb", "\t", "a\x00b"):
            with self.assertRaises(ValueError):
                config.validate_filter(value)

    def test_missing_values(self):
        """Проверить отсутствие значения у каждой строковой опции."""
        for name in ("--package", "--repository", "--filter"):
            self.assert_invalid(self.valid_arguments() + [name])

    def test_bad_boolean_values(self):
        """Не принимать значения у флагов test-repo и ascii-tree."""
        for name in ("--test-repo=maybe", "--ascii-tree=maybe"):
            self.assert_invalid(self.valid_arguments() + [name])

    def test_unknown_options(self):
        """Отклонить неизвестные опции и сокращения их названий."""
        for name in ("--unknown", "--ascii", "--repo"):
            self.assert_invalid(self.valid_arguments() + [name])

    def test_help(self):
        """Показать справку с кодом 0 без обязательных параметров."""
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                config.parse_arguments(["--help"])
        self.assertEqual(caught.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
