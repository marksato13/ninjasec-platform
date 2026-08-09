import { buildQuery, downloadFile } from "./api/client";
import { getTopology, type TopologyResponse } from "./api/topology";

const TYPE_RANK: Record<string, number> = { firewall: 0, router: 1, cloud: 1, switch: 2, server: 3, ap: 3, camera: 4, endpoint: 4, other: 4 };
const LINK_COLOR: Record<string, string> = { ethernet: "#64748b", wifi: "#8b5cf6", wan: "#0ea5e9", vpn: "#f59e0b", mpls: "#ec4899", trunk: "#14b8a6", cloud_peering: "#6366f1" };
const CRITICALITY_COLOR: Record<string, string> = { low: "#10b981", medium: "#3b82f6", high: "#f59e0b", critical: "#dc2626" };

const NODE_W = 160;
const NODE_H = 46;

export type LayoutNode = { id: number; label: string; x: number; y: number; deviceType?: string | null; criticality?: string | null };
export type LayoutEdge = { source: number; target: number; label: string; color: string };
export type TopologyLayout = { nodes: LayoutNode[]; edges: LayoutEdge[]; width: number; height: number };

/** Mismo criterio de posicionamiento que `network-topology.tsx` (por sede, por rango de tipo de dispositivo), pero calculado aquí como texto/coordenadas planas para exportar sin depender de React Flow. */
export function computeTopologyLayout(topology: TopologyResponse): TopologyLayout {
  const nodes: LayoutNode[] = [];
  const clusters = topology.clusters.length ? topology.clusters : [{ label: "Sin sede", site_id: null, node_ids: topology.nodes.map((n) => n.id) }];
  let offsetX = 40;
  let maxY = 0;

  for (const cluster of clusters) {
    const devices = topology.nodes.filter((d) => cluster.node_ids.includes(d.id));
    const ranks = devices.map((d) => TYPE_RANK[d.device_type || "other"] ?? 4);
    const maxAtRank = Math.max(1, ...ranks.map((r) => ranks.filter((x) => x === r).length));
    const clusterWidth = Math.max(220, maxAtRank * (NODE_W + 30));
    const rankIndex = new Map<number, number>();

    devices
      .slice()
      .sort((a, b) => (TYPE_RANK[a.device_type || "other"] ?? 4) - (TYPE_RANK[b.device_type || "other"] ?? 4))
      .forEach((device) => {
        const rank = TYPE_RANK[device.device_type || "other"] ?? 4;
        const index = rankIndex.get(rank) || 0;
        rankIndex.set(rank, index + 1);
        const count = ranks.filter((x) => x === rank).length;
        const x = offsetX + (clusterWidth - count * (NODE_W + 20)) / 2 + index * (NODE_W + 20);
        const y = 50 + rank * 110;
        nodes.push({ id: device.id, label: device.label, x, y, deviceType: device.device_type, criticality: device.criticality });
        maxY = Math.max(maxY, y + NODE_H);
      });
    offsetX += clusterWidth + 60;
  }

  const edges: LayoutEdge[] = topology.edges.map((e) => ({
    source: e.source,
    target: e.target,
    label: e.bandwidth_mbps ? `${e.link_type} · ${e.bandwidth_mbps} Mbps` : e.link_type,
    color: LINK_COLOR[e.link_type] || "#64748b",
  }));

  return { nodes, edges, width: Math.max(400, offsetX), height: Math.max(300, maxY + 60) };
}

export function buildTopologySvg(topology: TopologyResponse): string {
  const layout = computeTopologyLayout(topology);
  const byId = new Map(layout.nodes.map((n) => [n.id, n]));
  const lines = layout.edges
    .map((e) => {
      const source = byId.get(e.source);
      const target = byId.get(e.target);
      if (!source || !target) return "";
      const x1 = source.x + NODE_W / 2, y1 = source.y + NODE_H / 2;
      const x2 = target.x + NODE_W / 2, y2 = target.y + NODE_H / 2;
      return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${e.color}" stroke-width="2" />`;
    })
    .join("\n");
  const boxes = layout.nodes
    .map((n) => {
      const color = CRITICALITY_COLOR[n.criticality || ""] || "#94a3b8";
      const escaped = n.label.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      return `<g><rect x="${n.x}" y="${n.y}" width="${NODE_W}" height="${NODE_H}" rx="8" fill="#ffffff" stroke="${color}" stroke-width="2" />` +
        `<text x="${n.x + NODE_W / 2}" y="${n.y + NODE_H / 2 + 4}" text-anchor="middle" font-size="12" font-family="sans-serif" fill="#0f172a">${escaped}</text></g>`;
    })
    .join("\n");
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${layout.width}" height="${layout.height}" viewBox="0 0 ${layout.width} ${layout.height}">` +
    `<rect width="100%" height="100%" fill="#f8fafc" />${lines}${boxes}</svg>`;
}

function downloadBlob(content: string, filename: string, mime: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export async function downloadTopologySvg(clientId: number, filename = "topologia.svg") {
  const topology = await getTopology(clientId);
  downloadBlob(buildTopologySvg(topology), filename, "image/svg+xml");
}

export async function downloadTopologyPng(clientId: number, filename = "topologia.png") {
  const topology = await getTopology(clientId);
  const layout = computeTopologyLayout(topology);
  const svg = buildTopologySvg(topology);
  const dataUrl = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;

  await new Promise<void>((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = layout.width;
      canvas.height = layout.height;
      const ctx = canvas.getContext("2d");
      if (!ctx) { reject(new Error("No se pudo crear el canvas")); return; }
      ctx.fillStyle = "#f8fafc";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0);
      const a = document.createElement("a");
      a.href = canvas.toDataURL("image/png");
      a.download = filename;
      a.click();
      resolve();
    };
    img.onerror = () => reject(new Error("No se pudo rasterizar el diagrama"));
    img.src = dataUrl;
  });
}

export function buildTopologyDrawioXml(topology: TopologyResponse): string {
  const layout = computeTopologyLayout(topology);
  const cellIdOf = (deviceId: number) => `node-${deviceId}`;
  const nodeCells = layout.nodes
    .map((n) => {
      const escaped = n.label.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
      return `<mxCell id="${cellIdOf(n.id)}" value="${escaped}" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#64748b;" vertex="1" parent="1">` +
        `<mxGeometry x="${n.x}" y="${n.y}" width="${NODE_W}" height="${NODE_H}" as="geometry" /></mxCell>`;
    })
    .join("\n");
  const edgeCells = layout.edges
    .map((e, i) => `<mxCell id="edge-${i}" style="endArrow=none;html=1;strokeColor=${e.color};" edge="1" parent="1" source="${cellIdOf(e.source)}" target="${cellIdOf(e.target)}"><mxGeometry relative="1" as="geometry" /></mxCell>`)
    .join("\n");
  return `<?xml version="1.0" encoding="UTF-8"?>` +
    `<mxGraphModel dx="800" dy="600" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="${layout.width}" pageHeight="${layout.height}" math="0" shadow="0">` +
    `<root><mxCell id="0" /><mxCell id="1" parent="0" />${nodeCells}${edgeCells}</root></mxGraphModel>`;
}

export async function downloadTopologyDrawio(clientId: number, filename = "topologia.drawio") {
  const topology = await getTopology(clientId);
  downloadBlob(buildTopologyDrawioXml(topology), filename, "application/xml");
}

export async function downloadTopologyPdf(clientId: number, filename = "topologia.pdf") {
  await downloadFile(`/devices/topology/export/pdf${buildQuery({ client_id: clientId })}`, filename);
}
