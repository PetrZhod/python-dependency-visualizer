"""Версии только реальных пакетов на этапе 5 и дополнительный пример."""

import contextlib
import functools
import io
import sys
import tempfile
import threading
import unittest
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ascii_tree import format_ascii
from d2_format import to_d2
from package_labels import package_labels
from repository import PyPIRepository
from svg_format import to_svg
from svg_layout import graph_layout
import main
import visualization

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
NS = {"s": "http://www.w3.org/2000/svg"}


@contextlib.contextmanager
def snapshot_server():
    """Предоставить снимок реальных метаданных стандартным HTTP-сервером."""
    handler = functools.partial(SimpleHTTPRequestHandler,
                                directory=str(EXAMPLES / "pypi"))
    with HTTPServer(("127.0.0.1", 0), handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}"
        finally:
            server.shutdown()
            thread.join(timeout=3)


class VersionTests(unittest.TestCase):
    """Не подменять версию исследованных метаданных версией окружения."""

    def test_version_cache(self):
        """Извлечь версию и зависимости одним запросом, учитывая регистр."""
        data = {"info": {"name": "demo", "version": "1.2.3",
                         "requires_dist": []}}
        repo = PyPIRepository("https://example.org")
        with patch("repository.read_json", return_value=data) as fetch:
            self.assertEqual(repo.version("Demo"), "1.2.3")
            self.assertEqual(repo.dependencies("demo"), [])
            self.assertEqual(repo.version("demo"), "1.2.3")
        fetch.assert_called_once_with("https://example.org/demo/json")

    def test_bad_versions(self):
        """Отклонить неверный тип, пустую версию и управляющие символы."""
        for version in [12, [], "", " ", "1\n2"]:
            data = {"info": {"name": "demo", "version": version}}
            repo = PyPIRepository("https://example.org")
            with patch("repository.read_json", return_value=data):
                with self.assertRaises(ValueError):
                    repo.dependencies("demo")
            self.assertEqual(repo.cache, {})

    def test_missing_version(self):
        """Не выдумывать номер при отсутствии версии в пользовательском API."""
        repo = PyPIRepository("https://example.org")
        with patch("repository.read_json", return_value={"info": {
                "name": "demo", "requires_dist": []}}):
            labels = package_labels(repo, {"demo": []})
        self.assertEqual(labels, {"demo": "demo (версия не указана)"})

    def test_all_formats(self):
        """Показать версии в D2, SVG и дереве, не меняя имена вершин."""
        graph = {"demo": ["child"], "child": []}
        labels = {"demo": "demo (1.0)", "child": "child (2.0)"}
        self.assertIn('n1: "demo (1.0)"', to_d2(graph, labels))
        self.assertEqual(format_ascii(graph, "demo", labels),
                         "demo (1.0)\n`-- child (2.0)")
        root = ElementTree.fromstring(to_svg(graph, "demo", labels))
        text = {node.text for node in root.findall('.//s:text', NS)}
        self.assertEqual(text, set(labels.values()))
        self.assertEqual(graph, {"demo": ["child"], "child": []})

    def test_real_http_cli(self):
        """Получить четыре реальные вершины с версиями через HTTP."""
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(visualization, "OUTPUT_DIRECTORY",
                              Path(directory)):
                with patch("visualization.webbrowser.open", return_value=True):
                    with contextlib.redirect_stdout(output):
                        with contextlib.redirect_stderr(io.StringIO()):
                            with snapshot_server() as url:
                                result = main.main(["--package", "Jinja2",
                                                    "--repository", url,
                                                    "--ascii-tree"])
            self.assertEqual(result, 0)
            saved = Path(directory) / "jinja2.svg"
            svg = ElementTree.fromstring(saved.read_text(encoding="utf-8"))
        for label in ["jinja2 (3.1.6)", "babel (2.9.1)",
                      "markupsafe (3.0.3)", "pytz (2026.4)"]:
            self.assertIn(label, output.getvalue())
        self.assertEqual(len(svg.findall('s:g', NS)), 4)
        self.assertEqual(len(svg.findall('s:path[@class="edge"]', NS)), 3)

    def test_test_repo_unchanged(self):
        """Не добавлять версии к буквам тестового графа ни в одном выводе."""
        output = io.StringIO()
        with patch("main.publish_graph") as publish:
            with contextlib.redirect_stdout(output):
                result = main.main(["--package", "A", "--repository",
                                    str(EXAMPLES / "chain.json"),
                                    "--test-repo", "--ascii-tree"])
        self.assertEqual(result, 0)
        self.assertIn('n0: "A"', output.getvalue())
        self.assertIn("A\n`-- B\n    `-- C", output.getvalue())
        self.assertNotIn("версия", output.getvalue())
        publish.assert_called_once_with({"A": ["B"], "B": ["C"],
                                         "C": []}, "A")

    def test_cycle_labels(self):
        """Сохранить распознавание цикла при отображении версии."""
        graph = {"demo": ["demo"]}
        labels = {"demo": "demo (1.0)"}
        self.assertIn("demo (1.0) [цикл]",
                      format_ascii(graph, "demo", labels))
        self.assertIn("n0 -> n0", to_d2(graph, labels))

    def test_layout_label_width(self):
        """Увеличить ячейки изображения с учётом длины подписи версии."""
        graph = {"demo": []}
        labels = {"demo": "demo (1234567890.1234567890.1234567890)"}
        unused, width, size = graph_layout(graph, "demo")
        unused, labeled_width, size = graph_layout(graph, "demo", labels)
        self.assertGreater(labeled_width, width)


if __name__ == "__main__":
    unittest.main()
