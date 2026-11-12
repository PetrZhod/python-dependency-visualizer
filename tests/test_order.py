"""Проверки порядка загрузки, фильтрации и диагностики циклов."""

import contextlib
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from graph import GraphBuilder
from local_repository import TestRepository
from order import dependency_order
import main

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


class OrderTests(unittest.TestCase):
    """Проверить топологический порядок и запуск четвёртого этапа."""

    def test_orders(self):
        """Поставить общую зависимость раньше обеих использующих ветвей."""
        cases = [
            ({"A": []}, ["A"]),
            ({"A": ["B"], "B": ["C"], "C": []}, ["C", "B", "A"]),
            ({"A": ["C", "B"], "B": ["D"], "C": ["D"], "D": []},
             ["D", "B", "C", "A"]),
        ]
        for graph, expected in cases:
            with self.subTest(graph=graph):
                self.assertEqual(dependency_order(graph, "A"), expected)

    def test_cycles(self):
        """Не выдавать произвольный порядок циклического графа за верный."""
        for graph in ({"A": ["A"]}, {"A": ["B"], "B": ["A"]}):
            with self.subTest(graph=graph):
                with self.assertRaisesRegex(ValueError, "цикл"):
                    dependency_order(graph, "A")

    def test_empty_and_unknown(self):
        """Различать исключённый корень и некорректный непустой граф."""
        self.assertEqual(dependency_order({}, "A"), [])
        for graph in ({"B": []}, {"A": ["B"]}):
            with self.assertRaises(ValueError):
                dependency_order(graph, "A")

    def test_unreachable_cycle(self):
        """Не учитывать цикл в независимой компоненте репозитория."""
        graph = {"A": [], "B": ["C"], "C": ["B"]}
        self.assertEqual(dependency_order(graph, "A"), ["A"])

    def test_filter(self):
        """Построить порядок только по оставшимся вершинам графа."""
        repo = TestRepository(EXAMPLES / "diamond.json")
        graph = GraphBuilder(repo, "B").build("A")
        self.assertEqual(dependency_order(graph, "A"), ["D", "C", "A"])
        self.assertEqual(dependency_order(GraphBuilder(repo, "A")
                                         .build("A"), "A"), [])

    def test_no_mutation(self):
        """Не менять граф и не переносить состояние между запусками."""
        graph = {"A": ["B", "B"], "B": []}
        for unused in range(2):
            self.assertEqual(dependency_order(graph, "A"), ["B", "A"])
        self.assertEqual(graph["A"], ["B", "B"])

    def test_cli(self):
        """Вывести только порядок этапа 4 без отладочной конфигурации."""
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main.main(["--package", "A", "--repository",
                              str(EXAMPLES / "diamond.json"), "--test-repo"])
        self.assertEqual(code, 0)
        self.assertEqual(output.getvalue(),
                         "Порядок загрузки: D -> B -> C -> A\n")

    def test_cli_cycle(self):
        """Вернуть код 1 и понятное сообщение вместо ложного порядка."""
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            code = main.main(["--package", "A", "--repository",
                              str(EXAMPLES / "cycle.json"), "--test-repo"])
        self.assertEqual(code, 1)
        self.assertIn("A -> B -> C -> A", output.getvalue())


if __name__ == "__main__":
    unittest.main()
