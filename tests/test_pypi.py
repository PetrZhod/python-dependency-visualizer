"""Проверки чтения метаданных без менеджеров пакетов и внешней сети."""

import contextlib
import io
import json
import sys
import threading
import tempfile
from functools import partial
import unittest
from http.server import SimpleHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import repository as source


@contextlib.contextmanager
def metadata_server():
    """Обслуживать статический JSON стандартным HTTP-сервером."""
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "pypi/demo/json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({"info": {
            "name": "demo", "requires_dist": [
                "one>=1", "two; python_version < '3.11'",
            ],
        }}), encoding="utf-8")
        handler = partial(SimpleHTTPRequestHandler, directory=folder)
        with HTTPServer(("127.0.0.1", 0), handler) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                yield f"http://127.0.0.1:{server.server_port}/pypi"
            finally:
                server.shutdown()
                thread.join(timeout=3)


class RepositoryTests(unittest.TestCase):
    """Проверять URL, JSON, Requires-Dist, кеш и ошибки HTTP."""

    def metadata(self, dependencies=None):
        """Вернуть минимальный корректный ответ JSON API."""
        return {"info": {"name": "demo", "requires_dist": dependencies}}

    def test_normalization(self):
        """Считать регистр, точки, дефисы и подчёркивания эквивалентными."""
        self.assertEqual(source.canonical_name("My__Package.Name"),
                         "my-package-name")

    def test_requirement_names(self):
        """Извлечь имя, сохранив декларации с extras, версиями и маркерами."""
        for item in ("demo", "demo>=1", "demo[http] (>=1)",
                     "demo; extra == 'test'", "demo @ https://example.org/a"):
            self.assertEqual(source.requirement_name(item), "demo")
        self.assertEqual(source.requirement_name("A"), "A")

    def test_invalid_requirement_names(self):
        """Отклонить отсутствующие имена и нестроковые декларации."""
        for item in ("", " ", "???", 12, None, "-demo", "demo/"):
            with self.assertRaises(ValueError):
                source.requirement_name(item)

    def test_base_urls(self):
        """Дополнить короткий адрес PyPI и сохранить пользовательский путь."""
        self.assertEqual(source.repository_base("https://pypi.org/"),
                         "https://pypi.org/pypi")
        self.assertEqual(source.repository_base("http://localhost:8000/api/"),
                         "http://localhost:8000/api")
        with self.assertRaises(ValueError):
            source.repository_base("https://pypi.org/simple/")

    def test_missing_dependencies(self):
        """Принять null, отсутствующее поле и пустой список."""
        for data in (self.metadata(), self.metadata([]),
                     {"info": {"name": "demo"}}):
            self.assertEqual(source.metadata_dependencies(data, "demo"), [])

    def test_declarations(self):
        """Сохранить условные и дополнительные зависимости без вычисления."""
        items = ["b>=1", "a; extra == 'dev'", "b>=1"]
        actual = source.metadata_dependencies(self.metadata(items), "demo")
        self.assertEqual(actual, ["a; extra == 'dev'", "b>=1"])

    def test_invalid_metadata(self):
        """Отклонить неверный объект, чужое имя и неверный список."""
        cases = ([], {}, {"info": []}, {"info": {}},
                 {"info": {"name": "other"}}, self.metadata("not a list"),
                 self.metadata([None]), self.metadata(["???"]))
        for data in cases:
            with self.subTest(data=data):
                with self.assertRaises(ValueError):
                    source.metadata_dependencies(data, "demo")

    def test_cache_and_copies(self):
        """Повторно не скачивать пакет и не выдавать изменяемый кеш наружу."""
        data = self.metadata(["one"])
        repo = source.PyPIRepository("https://example.org/api")
        with patch.object(source, "read_json", return_value=data) as mocked:
            result = repo.dependencies("Demo")
            result.append("not-in-cache")
            self.assertEqual(repo.dependencies("demo"), ["one"])
            mocked.assert_called_once_with("https://example.org/api/demo/json")

    def test_json_loading(self):
        """Декодировать UTF-8 с BOM через настоящий JSON-парсер."""
        raw = json.dumps(self.metadata(["one"])).encode("utf-8-sig")
        with patch.object(source, "urlopen", return_value=io.BytesIO(raw)):
            self.assertEqual(source.read_json("https://example.org"),
                             self.metadata(["one"]))

    def test_invalid_json(self):
        """Сообщить о некорректном JSON и кодировке."""
        for raw in (b"{", b"<html>error</html>", b"\xff"):
            with patch.object(source, "urlopen", return_value=io.BytesIO(raw)):
                with self.assertRaises(ValueError):
                    source.read_json("https://example.org")

    def test_response_limit(self):
        """Не принимать ответ больше установленного ограничения."""
        with patch.object(source, "MAX_METADATA_BYTES", 3):
            with patch.object(source, "urlopen",
                              return_value=io.BytesIO(b"1234")):
                with self.assertRaises(ValueError):
                    source.read_json("https://example.org")

    def test_network_errors(self):
        """Обработать 404, другие HTTP-ошибки, DNS и тайм-аут."""
        errors = (HTTPError("https://x", 404, "missing", None, None),
                  HTTPError("https://x", 500, "failure", None, None),
                  URLError("DNS failure"), TimeoutError("timeout"))
        for error in errors:
            with patch.object(source, "urlopen", side_effect=error):
                with self.assertRaises(ValueError):
                    source.read_json("https://example.org")

    def test_local_http_integration(self):
        """Загрузить JSON реальным HTTP-запросом к локальному серверу."""
        with contextlib.redirect_stderr(io.StringIO()):
            with metadata_server() as base:
                actual = source.PyPIRepository(base).dependencies("demo")
        self.assertEqual(actual, ["one>=1",
                                 "two; python_version < '3.11'"])


if __name__ == "__main__":
    unittest.main()
