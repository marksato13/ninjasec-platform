"""23-P4: exportación PDF de la topología (diagrama + inventario).

Reutiliza el motor ReportLab ya usado en `app/modules/reports/services/pdf_service.py`
(SimpleDocTemplate + flowables) agregando un `Drawing` (reportlab.graphics.shapes)
para el diagrama -- mismo criterio de posicionamiento por sede/rango de tipo de
dispositivo que el layout del frontend (`lib/topology-export.ts`), reimplementado
en Python porque el PDF se genera en el backend.
"""
from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.modules.devices.schemas import TopologyResponse

_MARGIN = 14 * mm
_NODE_W, _NODE_H = 90, 26
_TYPE_RANK = {"firewall": 0, "router": 1, "cloud": 1, "switch": 2, "server": 3, "ap": 3, "camera": 4, "endpoint": 4, "other": 4}
_LINK_COLOR = {
    "ethernet": colors.HexColor("#64748b"), "wifi": colors.HexColor("#8b5cf6"),
    "wan": colors.HexColor("#0ea5e9"), "vpn": colors.HexColor("#f59e0b"),
    "mpls": colors.HexColor("#ec4899"), "trunk": colors.HexColor("#14b8a6"),
    "cloud_peering": colors.HexColor("#6366f1"),
}
_CRITICALITY_COLOR = {
    "low": colors.HexColor("#10b981"), "medium": colors.HexColor("#3b82f6"),
    "high": colors.HexColor("#f59e0b"), "critical": colors.HexColor("#dc2626"),
}


def _layout(topology: TopologyResponse) -> tuple[dict[int, tuple[float, float]], float, float]:
    clusters = topology.clusters or [type("C", (), {"node_ids": [n.id for n in topology.nodes]})()]
    positions: dict[int, tuple[float, float]] = {}
    offset_x = 20.0
    max_y = 0.0
    for cluster in clusters:
        devices = [n for n in topology.nodes if n.id in cluster.node_ids]
        ranks = [_TYPE_RANK.get(d.device_type or "other", 4) for d in devices]
        max_at_rank = max([ranks.count(r) for r in set(ranks)] or [1])
        cluster_width = max(160.0, max_at_rank * (_NODE_W + 20))
        rank_index: dict[int, int] = {}
        for device in sorted(devices, key=lambda d: _TYPE_RANK.get(d.device_type or "other", 4)):
            rank = _TYPE_RANK.get(device.device_type or "other", 4)
            index = rank_index.get(rank, 0)
            rank_index[rank] = index + 1
            count = ranks.count(rank)
            x = offset_x + (cluster_width - count * (_NODE_W + 15)) / 2 + index * (_NODE_W + 15)
            y = 40 + rank * 75
            positions[device.id] = (x, y)
            max_y = max(max_y, y + _NODE_H)
        offset_x += cluster_width + 40
    return positions, max(300.0, offset_x), max(200.0, max_y + 40)


def _diagram(topology: TopologyResponse) -> Drawing:
    positions, width, height = _layout(topology)
    drawing = Drawing(width, height)
    drawing.add(Rect(0, 0, width, height, fillColor=colors.HexColor("#f8fafc"), strokeColor=None))

    for edge in topology.edges:
        if edge.source not in positions or edge.target not in positions:
            continue
        x1, y1 = positions[edge.source]
        x2, y2 = positions[edge.target]
        color = _LINK_COLOR.get(edge.link_type, colors.HexColor("#64748b"))
        drawing.add(Line(
            x1 + _NODE_W / 2, height - (y1 + _NODE_H / 2),
            x2 + _NODE_W / 2, height - (y2 + _NODE_H / 2),
            strokeColor=color, strokeWidth=1.5,
        ))

    for node in topology.nodes:
        if node.id not in positions:
            continue
        x, y = positions[node.id]
        border = _CRITICALITY_COLOR.get(node.criticality or "", colors.HexColor("#94a3b8"))
        drawing.add(Rect(x, height - y - _NODE_H, _NODE_W, _NODE_H, rx=4, ry=4, fillColor=colors.white, strokeColor=border, strokeWidth=1.5))
        label = node.label if len(node.label) <= 16 else node.label[:14] + "…"
        drawing.add(String(x + _NODE_W / 2, height - y - _NODE_H / 2 - 3, label, fontSize=7, fillColor=colors.HexColor("#0f172a"), textAnchor="middle"))

    return drawing


def generate_topology_pdf(topology: TopologyResponse) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=_MARGIN, rightMargin=_MARGIN, topMargin=_MARGIN, bottomMargin=_MARGIN,
        title=f"Topología — {topology.client_name or topology.client_id}",
        author="NinjaSec Platform",
    )
    base = getSampleStyleSheet()
    title_style = ParagraphStyle("topo_title", parent=base["Normal"], fontSize=16, fontName="Helvetica-Bold", textColor=colors.HexColor("#0f172a"))
    subtitle_style = ParagraphStyle("topo_subtitle", parent=base["Normal"], fontSize=9, textColor=colors.HexColor("#64748b"))
    section_style = ParagraphStyle("topo_section", parent=base["Normal"], fontSize=11, fontName="Helvetica-Bold", textColor=colors.HexColor("#0f172a"), spaceBefore=12, spaceAfter=6)

    story: list = [
        Paragraph(f"Topología de red — {topology.client_name or ''}", title_style),
        Paragraph(f"{len(topology.nodes)} dispositivos · {len(topology.edges)} conexiones", subtitle_style),
        Spacer(1, 12),
        Paragraph("Diagrama", section_style),
        _diagram(topology),
        Paragraph("Inventario", section_style),
    ]

    rows = [["Dispositivo", "Tipo", "Vendor / Modelo", "Estado", "Criticidad"]]
    for node in topology.nodes:
        rows.append([
            node.label,
            node.device_type or "—",
            " / ".join(filter(None, [node.vendor, node.model])) or "—",
            node.status,
            node.criticality or "—",
        ])
    table = Table(rows, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(table)

    doc.build(story)
    return buffer.getvalue()
