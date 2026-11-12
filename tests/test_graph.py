"""Проверки рекурсивного DFS, фильтров, циклов и тестового репозитория."""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from graph import GraphBuilder, print_graph
from local_repository import TestRepository, validate_graph
import main


class GraphTests(unittest.TestCase):
    """Создавать независимый граф для каждого сценария."""

    def prepare_repository(self, data):
        """Создать временный репозиторий с автоматической уборкой."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "repository.json"
        self.path.write_text(json.dumps(data), encoding="utf-8")
        return TestRepository(self.path)

    def test_chain(self):
        """Получить не только прямую, но и транзитивную зависимость."""
        data = {"A": ["B"], "B": ["C"], "C": []}
        builder = GraphBuilder(self.prepare_repository(data))
        self.assertEqual(builder.build("A"), data)
        self.assertEqual(builder.cycles, [])

    def test_diamond(self):
        """Посетить общую зависимость двух ветвей ровно один раз."""
        data = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        repo = self.prepare_repository(data)
        with patch.object(repo, "dependencies", wraps=repo.dependencies) as spy:
            self.assertEqual(GraphBuilder(repo).build("A"), data)
        self.assertEqual(spy.call_count, len(data))

    def test_cycle(self):
        """Завершить обход цикла и сохранить ребро к активной вершине."""
        data = {"A": ["B"], "B": ["C"], "C": ["A"]}
        builder = GraphBuilder(self.prepare_repository(data))
        self.assertEqual(builder.build("A"), data)
        self.assertEqual(builder.cycles, [("A", "B", "C", "A")])

    def test_self_cycle(self):
        """Не зациклиться на зависимости пакета от самого себя."""
        builder = GraphBuilder(self.prepare_repository({"A": ["A"]}))
        self.assertEqual(builder.build("A"), {"A": ["A"]})
        self.assertEqual(builder.cycles, [("A", "A")])

    def test_filter_prunes_branch(self):
        """Исключить вершину и не анализировать её единственных потомков."""
        data = {"A": ["B", "C"], "B": ["D"], "C": [], "D": []}
        repo = self.prepare_repository(data)
        builder = GraphBuilder(repo, "b")
        with patch.object(repo, "dependencies", wraps=repo.dependencies) as spy:
            self.assertEqual(builder.build("A"), {"A": ["C"], "C": []})
        self.assertEqual(spy.call_count, 2)

    def test_shared_child_after_filter(self):
        """Сохранить потомка, если к нему остался другой разрешённый путь."""
        data = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        builder = GraphBuilder(self.prepare_repository(data), "B")
        self.assertEqual(builder.build("A"),
                         {"A": ["C"], "C": ["D"], "D": []})

    def test_filter_root(self):
        """Не запрашивать зависимости исключённого корня."""
        repo = self.prepare_repository({"A": []})
        with patch.object(repo, "dependencies") as spy:
            self.assertEqual(GraphBuilder(repo, "A").build("A"), {})
            spy.assert_not_called()

    def test_disconnected_nodes(self):
        """Не обходить компоненты, недостижимые из выбранного корня."""
        repo = self.prepare_repository({"A": [], "B": ["C"], "C": ["B"]})
        builder = GraphBuilder(repo)
        self.assertEqual(builder.build("A"), {"A": []})
        self.assertEqual(builder.cycles, [])

    def test_builder_reuse(self):
        """При новом построении очищать результаты предыдущего обхода."""
        repo = self.prepare_repository({"A": ["A"], "B": []})
        builder = GraphBuilder(repo)
        builder.build("A")
        self.assertEqual(builder.build("B"), {"B": []})
        self.assertEqual(builder.cycles, [])

    def test_long_chain(self):
        """Построить многоуровневый граф рекурсивным DFS."""
        names = ["A" * length for length in range(1, 81)]
        data = {name: [target] for name, target in zip(names, names[1:])}
        data[names[-1]] = []
        self.assertEqual(GraphBuilder(self.prepare_repository(data))
                         .build(names[0]), data)

    def test_unknown_root(self):
        """Сообщить об отсутствующем корневом пакете."""
        with self.assertRaises(ValueError):
            GraphBuilder(self.prepare_repository({"A": []})).build("B")

    def test_invalid_graphs(self):
        """Отклонить неверные типы, имена и отсутствующие цели рёбер."""
        for data in ([], None, {"a": []}, {"A": None}, {"A": [12]},
                     {"A": ["b"]}, {"A": ["B"]}, {"A1": []}):
            with self.subTest(data=data):
                with self.assertRaises(ValueError):
                    validate_graph(data)

    def test_empty_graph(self):
        """Принять пустой репозиторий, но отклонить запрос пакета из него."""
        repo = self.prepare_repository({})
        with self.assertRaises(ValueError):
            repo.dependencies("A")

    def test_duplicate_edges(self):
        """Убрать повторяющиеся рёбра, не меняя исходные данные."""
        data = {"A": ["B", "B"], "B": []}
        self.assertEqual(validate_graph(data), {"A": ["B"], "B": []})
        self.assertEqual(data["A"], ["B", "B"])

    def test_invalid_json_and_duplicates(self):
        """Отклонить повреждённый JSON, дубли ключей и неверный UTF-8."""
        self.prepare_repository({"A": []})
        for raw in (b"{", b'{"A": [], "A": []}', b"\xff"):
            self.path.write_bytes(raw)
            with self.assertRaises(ValueError):
                TestRepository(self.path)

    def test_missing_file(self):
        """Сообщить об исчезнувшем файле тестового репозитория."""
        self.prepare_repository({"A": []})
        self.path.unlink()
        with self.assertRaises(ValueError):
            TestRepository(self.path)

    def test_bom_and_copy(self):
        """Прочитать BOM и не выдавать изменяемую часть графа наружу."""
        self.prepare_repository({"A": ["B"], "B": []})
        self.path.write_text('{"A":["B"],"B":[]}', encoding="utf-8-sig")
        repo = TestRepository(self.path)
        result = repo.dependencies("A")
        result.clear()
        self.assertEqual(repo.dependencies("A"), ["B"])

    def test_output_cycle(self):
        """Вывести список смежности и диагностический путь цикла."""
        builder = GraphBuilder(self.prepare_repository({"A": ["A"]}))
        builder.build("A")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            print_graph(builder)
        self.assertEqual(output.getvalue(), "A -> A\nЦикл: A -> A\n")

    def test_cli_test_mode(self):
        """Выполнить весь третий этап без обращения к сети."""
        self.prepare_repository({"A": ["B"], "B": []})
        output = io.StringIO()
        with patch("repository.urlopen", side_effect=AssertionError("network")):
            with contextlib.redirect_stdout(output):
                result = main.main(["--package", "A", "--repository",
                                    str(self.path), "--test-repo"])
        self.assertEqual(result, 0)
        self.assertIn("B -> A", output.getvalue())
        self.assertNotIn("package=", output.getvalue())

    def test_cli_runtime_error(self):
        """При неверном тестовом графе вернуть код 1 без traceback."""
        self.prepare_repository({"A": []})
        self.path.write_text("{", encoding="utf-8")
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            result = main.main(["--package", "A", "--repository",
                                str(self.path), "--test-repo"])
        self.assertEqual(result, 1)
        self.assertIn("Ошибка:", output.getvalue())

    def test_cli_recursion_limit(self):
        """Обработать слишком глубокую рекурсию без аварийного traceback."""
        self.prepare_repository({"A": []})
        with patch.object(main.GraphBuilder, "build",
                          side_effect=RecursionError):
            with contextlib.redirect_stderr(io.StringIO()):
                result = main.main(["--package", "A", "--repository",
                                    str(self.path), "--test-repo"])
        self.assertEqual(result, 1)

    def test_real_repository_graph(self):
        """Нормализовать реальные имена и обойти условные декларации."""
        records = {
            "https://example.org/root-pkg/json": {"info": {
                "name": "Root_Pkg", "requires_dist": [
                    "Child>=1; python_version < '3.11'",
                    "Child[http]; extra == 'dev'",
                ],
            }},
            "https://example.org/child/json": {"info": {
                "name": "child", "requires_dist": None,
            }},
        }
        with patch("repository.read_json", side_effect=records.__getitem__):
            repo = main.PyPIRepository("https://example.org")
            self.assertEqual(GraphBuilder(repo).build("Root_Pkg"),
                             {"root-pkg": ["child"], "child": []})

    def test_excluded_output(self):
        """Объяснить пустой результат при исключении корня фильтром."""
        repo = self.prepare_repository({"A": []})
        builder = GraphBuilder(repo, "a")
        builder.build("A")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            print_graph(builder)
        self.assertIn("исключён фильтром", output.getvalue())


if __name__ == "__main__":
    unittest.main()
