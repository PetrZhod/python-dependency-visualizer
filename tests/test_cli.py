"""Проверки полного CLI второго этапа без внешней сети."""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import main


class CliTests(unittest.TestCase):
    """Проверять вывод прямых зависимостей и обработку ошибок запуска."""

    def arguments(self):
        """Вернуть параметры настоящего репозитория для подменённого запроса."""
        return ["--package", "demo", "--repository", "https://example.org"]

    def test_direct_output(self):
        """Вывести все декларации, не печатая конфигурацию этапа 1."""
        data = {"info": {"name": "demo", "requires_dist": [
            "one>=1", "two; extra == 'dev'",
        ]}}
        output = io.StringIO()
        with patch("repository.read_json", return_value=data):
            with contextlib.redirect_stdout(output):
                result = main.main(self.arguments())
        self.assertEqual(result, 0)
        self.assertIn("one>=1", output.getvalue())
        self.assertIn("two; extra == 'dev'", output.getvalue())
        self.assertNotIn("package=", output.getvalue())

    def test_no_dependencies(self):
        """Сообщить, что в метаданных нет объявленных зависимостей."""
        data = {"info": {"name": "demo", "requires_dist": None}}
        output = io.StringIO()
        with patch("repository.read_json", return_value=data):
            with contextlib.redirect_stdout(output):
                self.assertEqual(main.main(self.arguments()), 0)
        self.assertIn("Объявленных зависимостей нет", output.getvalue())

    def test_network_error(self):
        """Вернуть код 1 при ошибке чтения, не выводя traceback."""
        output = io.StringIO()
        with patch("repository.read_json", side_effect=ValueError("network")):
            with contextlib.redirect_stderr(output):
                self.assertEqual(main.main(self.arguments()), 1)
        self.assertIn("Ошибка:", output.getvalue())
        self.assertNotIn("Traceback", output.getvalue())

    def test_reserved_test_mode(self):
        """Объяснить, что загрузка тестового графа относится к этапу 3."""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "repository.json"
            path.write_text('{"A": []}', encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()):
                result = main.main(["--package", "A", "--repository",
                                    str(path), "--test-repo"])
        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
