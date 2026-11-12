"""Проверить измеримые ограничения учебного перечня нарушений."""

import ast
import io
import re
import tokenize
from pathlib import Path

MAX_PYTHON_LINE = 80
MAX_TEXT_LINE = 120
MAX_FUNCTION_LINES = 40
MAX_FILE_LINES = 1000
MAX_PARAMETERS = 7
MAX_COMPLEXITY = 10
TEXT_SUFFIXES = {".py", ".md", ".json", ".bat", ".sh", ".txt"}


def complexity(node):
    """Приближённо подсчитать ветвления, условия и генераторы функции."""
    total = 1
    decisions = (ast.If, ast.For, ast.While, ast.IfExp, ast.ExceptHandler)
    for item in ast.walk(node):
        if isinstance(item, decisions):
            total += 1
        elif isinstance(item, ast.BoolOp):
            total += len(item.values) - 1
        elif isinstance(item, ast.comprehension):
            total += 1 + len(item.ifs)
    return total


def parameter_count(node):
    """Посчитать параметры, включая self, *args и **kwargs."""
    args = node.args
    return (len(args.posonlyargs) + len(args.args) + len(args.kwonlyargs)
            + bool(args.vararg) + bool(args.kwarg))


def function_issues(node):
    """Проверить имя, документацию, длину, параметры и сложность функции."""
    issues = []
    if re.fullmatch(r"[a-z_][a-z0-9_]*", node.name) is None:
        issues.append(f"имя {node.name} не соответствует snake_case")
    if not ast.get_docstring(node):
        issues.append(f"нет docstring: {node.name}")
    if node.end_lineno - node.lineno + 1 > MAX_FUNCTION_LINES:
        issues.append(f"функция длиннее 40 строк: {node.name}")
    if parameter_count(node) > MAX_PARAMETERS:
        issues.append(f"больше 7 параметров: {node.name}")
    if complexity(node) > MAX_COMPLEXITY:
        issues.append(f"сложность больше 10: {node.name}")
    return issues


def numeric_literal(value):
    """Распознать числовой литерал, исключая логические значения."""
    if isinstance(value, ast.UnaryOp):
        value = value.operand
    return (isinstance(value, ast.Constant)
            and isinstance(value.value, (int, float))
            and not isinstance(value.value, bool))


def node_issues(node):
    """Проверить функции, классы и числовые литералы в сравнениях."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return function_issues(node)
    if isinstance(node, ast.ClassDef):
        if not ast.get_docstring(node):
            return [f"нет docstring класса {node.name}"]
    if isinstance(node, ast.Compare):
        if any(numeric_literal(item) for item in
               [node.left] + list(node.comparators)):
            return [f"числовой литерал в сравнении, строка {node.lineno}"]
    return []


def python_issues(text):
    """Проверить AST, docstring модуля и отсутствие Python-комментариев."""
    tree = ast.parse(text)
    issues = []
    if not ast.get_docstring(tree):
        issues.append("нет docstring модуля")
    for node in ast.walk(tree):
        issues.extend(node_issues(node))
    tokens = tokenize.generate_tokens(io.StringIO(text).readline)
    if any(token.type == tokenize.COMMENT for token in tokens):
        issues.append("есть Python-комментарии вместо документации")
    return issues


def file_issues(path):
    """Проверить длины строк и файла, затем ограничения Python."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    issues = []
    if len(lines) > MAX_FILE_LINES:
        issues.append("файл длиннее 1000 строк")
    limit = MAX_PYTHON_LINE if path.suffix == ".py" else MAX_TEXT_LINE
    for number, line in enumerate(lines, start=1):
        if len(line) > limit:
            issues.append(f"строка {number} длиннее {limit} символов")
    if "\u200b" in text:
        issues.append("есть невидимый символ U+200B")
    if path.suffix == ".py":
        issues.extend(python_issues(text))
    return issues


def main():
    """Проверить текстовые файлы проекта и вернуть ненулевой код при ошибке."""
    root = Path(__file__).resolve().parents[1]
    failures = []
    for path in sorted(root.rglob("*")):
        if ".git" in path.parts or not path.is_file():
            continue
        if path.suffix in TEXT_SUFFIXES or path.name == ".gitignore":
            failures.extend(f"{path.relative_to(root)}: {item}"
                            for item in file_issues(path))
    for issue in failures:
        print(issue)
    if not failures:
        print("Измеримые ограничения: OK")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
