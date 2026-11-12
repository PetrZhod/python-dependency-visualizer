"""Изображение графа SVG из того же графа, что используется для D2."""

from xml.sax.saxutils import escape

from svg_layout import BOX_HEIGHT, graph_layout

SVG_START = '<svg xmlns="http://www.w3.org/2000/svg"'
ARROW = ('<defs><marker id="arrow" markerWidth="10" markerHeight="7" '
         'refX="9" refY="3.5" orient="auto" markerUnits="userSpaceOnUse">'
         '<path d="M0,0 L10,3.5 L0,7 Z" fill="#526173"/>'
         '</marker></defs>')


def edge_path(source, target, box_width, outer):
    """Построить кривую обычного ребра, обратной связи или петли."""
    x, y = source
    tx, ty = target
    if source == target:
        right = x + box_width
        middle = y + BOX_HEIGHT / 2
        return (f"M{right},{middle - 8} "
                f"C{right + 75},{middle - 65} "
                f"{right + 75},{middle + 65} {right},{middle + 8}")
    if ty > y:
        sx = x + box_width / 2
        ex = tx + box_width / 2
        start = y + BOX_HEIGHT
        middle = (start + ty) / 2
        return f"M{sx},{start} C{sx},{middle} {ex},{middle} {ex},{ty}"
    start = y + BOX_HEIGHT / 2
    end = ty + BOX_HEIGHT / 2
    return (f"M{x + box_width},{start} C{outer},{start} "
            f"{outer},{end} {tx + box_width},{end}")


def node_svg(name, position, box_width, root):
    """Изобразить пакет с XML-экранированной подписью."""
    x, y = position
    color = "#dbeafe" if name == root else "#f1f5f9"
    label = escape(name)
    return (f'<g class="node"><title>{label}</title>'
            f'<rect x="{x}" y="{y}" width="{box_width}" '
            f'height="{BOX_HEIGHT}" rx="8" fill="{color}" '
            'stroke="#526173"/>'
            f'<text x="{x + box_width / 2}" y="{y + 28}" '
            'text-anchor="middle" font-family="monospace" '
            f'font-size="14">{label}</text></g>')


def to_svg(graph, root):
    """Сформировать самостоятельный SVG со всеми вершинами и рёбрами."""
    positions, box_width, size = graph_layout(graph, root)
    width, height = size
    lines = [f'{SVG_START} width="{width}" height="{height}" '
             f'viewBox="0 0 {width} {height}">',
             '<title>Граф зависимостей</title>', ARROW]
    if not graph:
        lines.append('<text x="20" y="60">Корень исключён фильтром</text>')
    for name in sorted(graph):
        for target in sorted(set(graph[name])):
            path = edge_path(positions[name], positions[target],
                             box_width, width - 15)
            lines.append(f'<path class="edge" d="{path}" fill="none" '
                         'stroke="#526173" stroke-width="1.7" '
                         'marker-end="url(#arrow)"/>')
    for name in sorted(graph):
        lines.append(node_svg(name, positions[name], box_width, root))
    lines.append('</svg>')
    return "\n".join(lines) + "\n"
