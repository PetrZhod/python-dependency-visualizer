"""Сохранение D2 и SVG с открытием изображения в браузере."""

import webbrowser
from pathlib import Path

from d2_format import to_d2
from svg_format import to_svg

OUTPUT_DIRECTORY = Path("output")


def publish_graph(graph, root):
    """Сохранить представления графа и открыть SVG стандартным браузером."""
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    d2_path = OUTPUT_DIRECTORY / f"{root}.d2"
    svg_path = OUTPUT_DIRECTORY / f"{root}.svg"
    d2_path.write_text(to_d2(graph), encoding="utf-8")
    svg_path.write_text(to_svg(graph, root), encoding="utf-8")
    print(f"D2: {d2_path.resolve()}")
    print(f"Изображение: {svg_path.resolve()}")
    if not webbrowser.open(svg_path.resolve().as_uri(), new=2):
        raise ValueError("Браузер не открылся. "
                         "Откройте сохранённый SVG вручную")
    return d2_path, svg_path
