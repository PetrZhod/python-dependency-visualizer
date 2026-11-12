"""Проверки D2, SVG, ASCII-дерева, файлов и открытия изображения."""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ascii_tree import format_ascii
from d2_format import to_d2
from svg_format import to_svg
import visualization
import main

DIAMOND = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
SVG_NAMESPACE = {"s": "http://www.w3.org/2000/svg"}
EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


class VisualizationTests(unittest.TestCase):
    """Проверить форматы и ошибки без открытия окон во время автотестов."""

    def test_d2(self):
        """Сохранить все вершины и связи, включая изолированный пакет."""
        text = to_d2(DIAMOND)
        self.assertEqual(text, 'direction: down\nn0: "A"\nn1: "B"\n'
                         'n2: "C"\nn3: "D"\nn0 -> n1\nn0 -> n2\n'
                         'n1 -> n3\nn2 -> n3\n')
        self.assertIn('n0: "A"', to_d2({"A": []}))

    def test_d2_cycles_and_determinism(self):
        """Не терять петли и не зависеть от порядка словаря или дублей."""
        self.assertIn("n0 -> n0", to_d2({"A": ["A"]}))
        graph = {"B": [], "A": ["B", "B"]}
        self.assertEqual(to_d2(graph), to_d2({"A": ["B"], "B": []}))

    def test_d2_escape(self):
        """Отделять идентификатор вершины от экранированной подписи."""
        self.assertIn(r'n0: "a\"b"', to_d2({'a"b': []}))

    def test_ascii_diamond(self):
        """Отмечать общую зависимость вместо повторного раскрытия."""
        self.assertEqual(format_ascii(DIAMOND, "A"),
                         "A\n|-- B\n|   `-- D\n`-- C\n    `-- D [повтор]")

    def test_ascii_cycles(self):
        """Завершать дерево при петле и цикле из нескольких пакетов."""
        self.assertEqual(format_ascii({"A": ["A"]}, "A"),
                         "A\n`-- A [цикл]")
        graph = {"A": ["B"], "B": ["A"]}
        self.assertIn("A [цикл]", format_ascii(graph, "A"))
        self.assertEqual(format_ascii({}, "A"), "(пустой граф)")

    def test_svg_nodes_and_edges(self):
        """Получить корректный XML с четырьмя вершинами и четырьмя рёбрами."""
        root = ElementTree.fromstring(to_svg(DIAMOND, "A"))
        nodes = root.findall("s:g", SVG_NAMESPACE)
        edges = root.findall('s:path[@class="edge"]', SVG_NAMESPACE)
        self.assertEqual(len(nodes), 4)
        self.assertEqual(len(edges), 4)
        labels = {n.find("s:text", SVG_NAMESPACE).text for n in nodes}
        self.assertEqual(labels, set(DIAMOND))

    def test_svg_cycles(self):
        """Визуализировать обратное ребро и зависимость от самого себя."""
        for graph in ({"A": ["A"]}, {"A": ["B"], "B": ["A"]}):
            with self.subTest(graph=graph):
                root = ElementTree.fromstring(to_svg(graph, "A"))
                edges = root.findall('s:path[@class="edge"]', SVG_NAMESPACE)
                self.assertEqual(len(edges), len(graph))

    def test_svg_escape_and_empty(self):
        """Не допускать внедрение XML через подпись пакета."""
        name = 'a<&"b'
        root = ElementTree.fromstring(to_svg({name: []}, name))
        self.assertEqual(root.find('.//s:text', SVG_NAMESPACE).text, name)
        ElementTree.fromstring(to_svg({}, "A"))

    def test_saved_files_and_viewer(self):
        """Сохранить UTF-8 файлы и открыть локальный URI изображения."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            with patch.object(visualization, "OUTPUT_DIRECTORY", output):
                with patch("visualization.webbrowser.open", return_value=True):
                    with contextlib.redirect_stdout(io.StringIO()):
                        d2_path, svg_path = visualization.publish_graph(
                            DIAMOND, "A")
            self.assertEqual(d2_path.read_text(encoding="utf-8"),
                             to_d2(DIAMOND))
            self.assertEqual(svg_path.read_text(encoding="utf-8"),
                             to_svg(DIAMOND, "A"))

    def test_viewer_failure(self):
        """Сохранить результат и объяснить ошибку открытия браузера."""
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(visualization, "OUTPUT_DIRECTORY",
                              Path(directory)):
                with patch("visualization.webbrowser.open", return_value=False):
                    with contextlib.redirect_stdout(io.StringIO()):
                        with self.assertRaisesRegex(ValueError, "Браузер"):
                            visualization.publish_graph({"A": []}, "A")
            self.assertTrue((Path(directory) / "A.svg").exists())

    def test_write_error(self):
        """Сообщить об ошибке записи, если output является файлом."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "blocked"
            output.write_text("file")
            with patch.object(visualization, "OUTPUT_DIRECTORY", output):
                with self.assertRaises(OSError):
                    visualization.publish_graph({"A": []}, "A")

    def test_cli_ascii_flag(self):
        """Выводить дерево только по флагу и не печатать порядок этапа 4."""
        base = ["--package", "A", "--repository",
                str(EXAMPLES / "diamond.json"), "--test-repo"]
        for extra, expected in (([], False), (["--ascii-tree"], True)):
            output = io.StringIO()
            with patch("main.publish_graph"):
                with contextlib.redirect_stdout(output):
                    code = main.main(base + extra)
            self.assertEqual(code, 0)
            self.assertEqual("|-- B" in output.getvalue(), expected)
            self.assertNotIn("Порядок загрузки", output.getvalue())

    def test_cli_image_error(self):
        """Вернуть код 1 при ошибке записи или открытия изображения."""
        with patch("main.publish_graph", side_effect=OSError("read only")):
            with contextlib.redirect_stderr(io.StringIO()):
                with contextlib.redirect_stdout(io.StringIO()):
                    result = main.main(["--package", "A", "--repository",
                                        str(EXAMPLES / "single.json"),
                                        "--test-repo"])
        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
