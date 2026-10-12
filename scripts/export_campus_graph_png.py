#!/usr/bin/env python3
"""
Export a campus graph as PNG diagram.

Usage:
  python scripts/export_campus_graph_png.py --campus <campus_id> --output <path.png>

Reuses existing graph_service to build the routable network, then
visualizes it with matplotlib/networkx for inclusion in reports.
"""

import argparse
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from digital_twin.config_loader import load_campus_config
from digital_twin.db import apply_migrations, get_connection
from digital_twin.graph_service import CampusGraphService

PROJECT_ROOT = Path(__file__).parent.parent

# Pixel positions (x, y) of buildings on docs/vitap_basemap.png (OpenStreetMap view of the campus).
# Used to fit lat/lon -> pixel so graph nodes land on the right buildings.
BASEMAP_ANCHORS = {
    "AB-1": (665, 155), "AB-2": (392, 162), "CB": (524, 325), "Food Street": (437, 405),
    "MH-1": (690, 352), "MH-2": (772, 430), "MH-3": (778, 585), "MH-6": (590, 610),
    "MH-7": (680, 530), "LH-1": (230, 612),
}


# Where these places really are on the basemap (pixel positions); overrides the config coordinates.
# Main Gate: top end of the straight boulevard north of CB. Overflow Parking: the two "P" bays beside it.
BASEMAP_NODE_PIXELS = {
    "Main Gate": [(528, 6)],
    "Overflow Parking": [(450, 43), (588, 43)],
    "Academic Block Main Lot": [(657, 298)],  # open area between the diagonal road and the Alternative Gate road
    "Library": [(560, 355)],  # inside the CB building
    "Sports & Recreation Lot": [(240, 430), (105, 480)],  # Sports Triangle 1 and Sports Triangle 2
    "Hostel Zone Parking": [(717, 452)],  # road beside Basketball Court 4
    "Sports Complex": [(376, 275)],  # building with the sports icons, west of the CB ring
    "Visitor Gate": [(803, 317)],  # east end of the straight road north of MH-1 / MH-5
    "Administrative & Visitor Lot": [(720, 245)],  # Cricket Ground, next to MH-1
}


# Road stretches (pixel segments) that routes to a place must not use, so they take the neighbouring road.
# Sports & Recreation Lot: do not go along the road past Food Street; use the road beside it instead.
BASEMAP_AVOID = {
    "Sports & Recreation Lot": [((430, 360), (280, 514))],
}

# Buildings drawn on the basemap figure only (not in the campus config / simulation): name -> pixel position.
BASEMAP_EXTRA_DESTINATIONS = {"LH-2": (320, 632), "MH-4": (695, 615)}

# Lots the extra buildings connect to, like LH-1 and MH-6 in the config (Hostel Zone + Overflow).
BASEMAP_EXTRA_LOTS = ["Hostel Zone Parking", "Overflow Parking"]

# Preferred label side per place so labels stay off the map's own text: (x dir, y dir, ha, va).
BASEMAP_LABEL_SIDE = {
    "Hostel Zone Parking": (-1.8, -1.2, "right", "top"),
    "Academic Block Main Lot": (1.8, 0, "left", "center"),
    "Administrative &\nVisitor Lot": (0, -1.6, "center", "top"),  # inside the Cricket Ground
}

# Places whose marker must sit exactly on a road of the basemap.
BASEMAP_ON_ROAD = ["Hostel Zone Parking"]

# Display names used on the basemap figure.
BASEMAP_RENAMES = {"Visitor Gate": "Alternative Gate", "Administrative & Visitor Lot": "Administrative &\nVisitor Lot"}


def snap_to_road(img, xy):
    """Nearest point on the basemap's road network (white road pixels) to a pixel position."""
    import numpy as np
    from scipy import ndimage

    rgb = (img[..., :3] * 255).round().astype(int) if img.dtype != np.uint8 else img[..., :3].astype(int)
    road = ndimage.binary_opening((rgb == 255).all(axis=2), iterations=1)
    lab, n = ndimage.label(road, structure=np.ones((3, 3)))
    road = lab == (1 + int(np.argmax(ndimage.sum(road, lab, range(1, n + 1)))))
    dt = ndimage.distance_transform_edt(road)
    ys, xs = np.nonzero(road & (dt >= 2.5))  # inside the road, not on its edge
    i = int(np.argmin((xs - xy[0]) ** 2 + (ys - xy[1]) ** 2))
    return float(xs[i]), float(ys[i])


def route_roads_on_basemap(img, pos, road_ends, avoid=None):
    """Route each road along the white road pixels of the basemap (OpenStreetMap style).

    Returns {road index: [(x, y), ...]} in pixel coordinates. Nodes off the image
    or away from a road get a straight stub to the nearest road pixel.
    """
    import numpy as np
    from scipy import ndimage
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components, dijkstra

    rgb = (img[..., :3] * 255).round().astype(int) if img.dtype != np.uint8 else img[..., :3].astype(int)
    road = (rgb == 255).all(axis=2)
    road = ndimage.binary_opening(road, iterations=1)
    lab, n = ndimage.label(road, structure=np.ones((3, 3)))
    if n == 0:
        return {}
    sizes = ndimage.sum(road, lab, range(1, n + 1))
    road = lab == (1 + int(np.argmax(sizes)))  # main connected road network
    h, w = road.shape
    dt = ndimage.distance_transform_edt(road)
    idx = -np.ones(road.shape, dtype=int)
    ys, xs = np.nonzero(road)
    idx[ys, xs] = np.arange(len(ys))
    rows, cols, wts = [], [], []
    for dy, dx in [(0, 1), (1, 0), (1, 1), (1, -1)]:
        y2, x2 = ys + dy, xs + dx
        ok = (y2 >= 0) & (y2 < h) & (x2 >= 0) & (x2 < w)
        ok[ok] &= road[y2[ok], x2[ok]]
        a, b = idx[ys[ok], xs[ok]], idx[y2[ok], x2[ok]]
        step = np.hypot(dy, dx)
        cost = step * (1 + 12.0 / np.minimum(dt[ys[ok], xs[ok]], dt[y2[ok], x2[ok]]))  # prefer road centre lines
        rows += [a, b]
        cols += [b, a]
        wts += [cost, cost]
    all_r, all_c, all_w = np.concatenate(rows), np.concatenate(cols), np.concatenate(wts)
    graph = coo_matrix((all_w, (all_r, all_c)), shape=(len(ys), len(ys))).tocsr()

    def graph_avoiding(segments):
        """Same road graph, but pixels within 7px of the given segments cost 1000x more."""
        bad = np.zeros(len(ys), dtype=bool)
        for (x1, y1), (x2, y2) in segments:
            vx, vy = x2 - x1, y2 - y1
            t = np.clip(((xs - x1) * vx + (ys - y1) * vy) / (vx * vx + vy * vy), 0, 1)
            bad |= np.hypot(xs - (x1 + t * vx), ys - (y1 + t * vy)) <= 7
        w2 = np.where(bad[all_r] | bad[all_c], all_w * 1000.0, all_w)
        return coo_matrix((w2, (all_r, all_c)), shape=(len(ys), len(ys))).tocsr()

    def snap(x, y):
        d = (xs - x) ** 2 + (ys - y) ** 2
        i = int(np.argmin(d))
        return i, (float(xs[i]), float(ys[i]))

    routes = {}
    snaps = {}
    for k, (a, b) in enumerate(road_ends):
        for node in (a, b):
            if node not in snaps:
                snaps[node] = snap(*pos[node])
        ia, pa = snaps[a]
        ib, pb = snaps[b]
        segs = (avoid or {}).get(a, []) + (avoid or {}).get(b, [])
        _, pred = dijkstra(graph_avoiding(segs) if segs else graph, indices=ia, return_predecessors=True)
        path, cur = [], ib
        while cur != ia and cur >= 0:
            path.append((float(xs[cur]), float(ys[cur])))
            cur = pred[cur]
        path.append(pa)
        path.reverse()
        if len(path) > 9:  # light smoothing of the pixel staircase
            arr = np.array(path)
            sm = arr.copy()
            for i in range(len(arr)):
                lo, hi = max(0, i - 4), min(len(arr), i + 5)
                sm[i] = arr[lo:hi].mean(axis=0)
            sm[0], sm[-1] = arr[0], arr[-1]
            path = [tuple(p) for p in sm]
        routes[k] = [tuple(pos[a])] + path + [tuple(pos[b])]
    return routes


def export_campus_graph_png(campus_id: str, config_path: str, output_path: str, basemap: str = None):
    """Load campus config, build graph, export as PNG."""
    db_path = PROJECT_ROOT / "documentation" / "database" / "digital_twin.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = get_connection(db_path)
    apply_migrations(conn)

    # Load config into DB
    loaded_id = load_campus_config(config_path, conn)
    assert loaded_id == campus_id, f"Campus ID mismatch: {loaded_id} vs {campus_id}"

    # Build graph
    graph_svc = CampusGraphService()
    graph = graph_svc.build_graph(campus_id, conn)

    # Layout based on real geographical coordinates (longitude = x, latitude = y)
    pos = {}
    for node, data in graph.nodes(data=True):
        if data.get("longitude") is not None and data.get("latitude") is not None:
            pos[node] = (data["longitude"], data["latitude"])
        else:
            pos[node] = (0, 0)

    # Query human-readable names for all nodes
    labels = {}
    for row in conn.execute("SELECT gate_id, name FROM gates WHERE campus_id=?", (campus_id,)):
        labels[row["gate_id"]] = row["name"]
    for row in conn.execute("SELECT parking_lot_id, name FROM parking_lots WHERE campus_id=?", (campus_id,)):
        labels[row["parking_lot_id"]] = row["name"]
    for row in conn.execute("SELECT destination_id, name FROM destinations WHERE campus_id=?", (campus_id,)):
        labels[row["destination_id"]] = row["name"]

    # Fallback to node_id if name missing
    for node in graph.nodes():
        if node not in labels:
            labels[node] = node

    # Query road geometries from DB (one polyline per road)
    road_geometries = []
    for row in conn.execute("SELECT geometry FROM roads WHERE campus_id=?", (campus_id,)):
        try:
            geom = yaml.safe_load(row["geometry"])
            if isinstance(geom, list):
                coords = [(pt["lng"], pt["lat"]) for pt in geom if "lng" in pt and "lat" in pt]
                if len(coords) >= 2:
                    road_geometries.append(coords)
        except Exception:
            pass

    img = None
    extra_px = {}
    if basemap:
        import numpy as np
        import matplotlib.image as mpimg

        img = mpimg.imread(basemap)
        names = {v: k for k, v in labels.items()}
        anchors = [(n, names[n]) for n in BASEMAP_ANCHORS if n in names]
        src = np.array([[pos[nid][0], pos[nid][1], 1.0] for _, nid in anchors])
        dst = np.array([BASEMAP_ANCHORS[n] for n, _ in anchors], dtype=float)
        coef, *_ = np.linalg.lstsq(src, dst, rcond=None)  # affine lon/lat -> pixel
        to_px = lambda x, y: tuple(np.array([x, y, 1.0]) @ coef)
        err = np.hypot(*(src @ coef - dst).T)
        print(f"Basemap fit: {len(anchors)} anchors, mean error {err.mean():.1f}px, max {err.max():.1f}px")
        pos = {n: to_px(*xy) for n, xy in pos.items()}
        extra_px = {}
        for name, pts in BASEMAP_NODE_PIXELS.items():
            if name in names:
                nid = names[name]
                pos[nid] = (sum(x for x, _ in pts) / len(pts), sum(y for _, y in pts) / len(pts))
                extra_px[nid] = pts
        for name in BASEMAP_ON_ROAD:
            if name in names:
                pos[names[name]] = snap_to_road(img, pos[names[name]])
        for name, xy in BASEMAP_EXTRA_DESTINATIONS.items():
            nid = f"extra:{name}"
            graph.add_node(nid, type="destination")
            pos[nid] = xy
            labels[nid] = name
        for old, new in BASEMAP_RENAMES.items():
            if old in names:
                labels[names[old]] = new
        road_ends = [(r["start_node_id"], r["end_node_id"]) for r in conn.execute(
            "SELECT start_node_id, end_node_id FROM roads WHERE campus_id=?", (campus_id,))]
        road_ends = [(a, b) for a, b in road_ends if a in pos and b in pos]
        for name in BASEMAP_EXTRA_DESTINATIONS:
            for lot in BASEMAP_EXTRA_LOTS:
                if lot in names:
                    road_ends.append((names[lot], f"extra:{name}"))
        avoid = {names[n]: segs for n, segs in BASEMAP_AVOID.items() if n in names}
        road_geometries = list(route_roads_on_basemap(img, pos, road_ends, avoid).values())

    # Equal-scale map: 1 degree of longitude is shorter than 1 degree of latitude
    lat0 = sum(y for _, y in pos.values()) / len(pos)
    aspect = 1.0 if img is not None else 1.0 / math.cos(math.radians(lat0))

    styles = {  # node type -> (colour, marker, size, label font size, bold)
        "gate": ("#d62728", "s", 150, 9, True),
        "parking_lot": ("#1f77b4", "P", 190, 9, True),
        "destination": ("#2ca02c", "o", 55, 7, False),
    }

    fig, ax = plt.subplots(figsize=(13, 10))
    ax.set_facecolor("#f4f1ea")
    if img is not None:
        ax.set_facecolor("#fbf7d9")
        ax.imshow(img, extent=(0, img.shape[1], img.shape[0], 0), zorder=0)
    ax.set_aspect(aspect)

    # Roads: drawn once from real geometry, no duplicate straight edges
    for coords in road_geometries:
        xs, ys = zip(*coords)
        ax.plot(xs, ys, color="white", linewidth=5, solid_capstyle="round", zorder=1)
        ax.plot(xs, ys, color="#9aa0a6", linewidth=2, solid_capstyle="round", zorder=2)

    for ntype, (color, marker, size, _, _) in styles.items():
        pts = [pos[n] for n in graph.nodes()
               if graph.nodes[n].get("type") == ntype and len(extra_px.get(n, [0])) < 2]
        if pts:
            xs, ys = zip(*pts)
            ax.scatter(xs, ys, c=color, marker=marker, s=size, edgecolors="white",
                       linewidths=1.2, zorder=3 + (ntype != "destination"))
    for nid, pts in extra_px.items():  # places drawn at several spots (e.g. two parking bays)
        if len(pts) > 1:
            color, marker, size, _, _ = styles[graph.nodes[nid].get("type")]
            for bx, by in pts:  # link each bay to the point where the lot's roads attach
                ax.plot([pos[nid][0], bx], [pos[nid][1], by], color="#9aa0a6", linewidth=2, linestyle=(0, (3, 2)), zorder=2)
            ax.scatter(*zip(*pts), c=color, marker=marker, s=size, edgecolors="white", linewidths=1.2, zorder=4)

    # Labels: try 8 offsets per node, keep the first that does not overlap earlier labels
    xs_all = [x for x, _ in pos.values()]
    ys_all = [y for _, y in pos.values()]
    dx = (max(xs_all) - min(xs_all)) or 1e-3
    dy = (max(ys_all) - min(ys_all)) or 1e-3
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    placed = []
    from matplotlib.transforms import Bbox

    for n, (px, py) in pos.items():  # markers are obstacles too, so labels never cover them
        for mx, my in (extra_px.get(n) or [(px, py)]):
            cx, cy = ax.transData.transform((mx, my))
            placed.append(Bbox([[cx - 9, cy - 9], [cx + 9, cy + 9]]))
    offsets = [(1, 1, "left", "bottom"), (-1, 1, "right", "bottom"), (1, -1, "left", "top"),
               (-1, -1, "right", "top"), (0, 1.6, "center", "bottom"), (0, -1.6, "center", "top"),
               (1.8, 0, "left", "center"), (-1.8, 0, "right", "center")]
    order = sorted(
        pos,
        key=lambda n: (img is not None and labels.get(n) in BASEMAP_LABEL_SIDE,  # places with a fixed side go first
                       styles.get(graph.nodes[n].get("type"), styles["destination"])[4]),
        reverse=True,
    )
    for node in order:
        x, y = extra_px[node][-1] if node in extra_px else pos[node]  # label the last bay of multi-bay places
        _, _, _, fs, bold = styles.get(graph.nodes[node].get("type"), styles["destination"])
        best = None
        side = BASEMAP_LABEL_SIDE.get(labels.get(node)) if img is not None else None
        for ox, oy, ha, va in ([side] if side else []) + offsets:
            t = ax.annotate(labels.get(node, node), (x, y), xytext=(ox * 7, oy * 7), textcoords="offset points",
                            fontsize=fs, fontweight="bold" if bold else "normal", ha=ha, va=va, zorder=6,
                            bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.85))
            box = t.get_window_extent(renderer)
            if not any(box.overlaps(o) for o in placed):
                best = box
                break
            t.remove()
        if best is None:  # crowded: fall back to the first offset
            ox, oy, ha, va = offsets[0]
            t = ax.annotate(labels.get(node, node), (x, y), xytext=(ox * 7, oy * 7), textcoords="offset points",
                            fontsize=fs, ha=ha, va=va, zorder=6,
                            bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.85))
            best = t.get_window_extent(renderer)
        placed.append(best)

    pad_x, pad_y = dx * 0.12, dy * 0.12
    ax.set_xlim(min(xs_all) - pad_x, max(xs_all) + pad_x)
    ax.set_ylim(min(ys_all) - pad_y, max(ys_all) + pad_y)
    if img is not None:
        h, w = img.shape[:2]
        ax.set_xlim(min(0, min(xs_all) - 30), max(w, max(xs_all) + 30))
        ax.set_ylim(max(h, max(ys_all) + 30), min(0, min(ys_all) - 30))
    if img is None:
        ax.set_xlabel("Longitude (E)")
        ax.set_ylabel("Latitude (N)")
        ax.grid(True, color="white", linewidth=0.8, alpha=0.7)
        ax.ticklabel_format(useOffset=False, style="plain")
    else:
        ax.set_xticks([])
        ax.set_yticks([])
    ax.tick_params(labelsize=8)
    for sp in ax.spines.values():
        sp.set_color("#c8c4ba")
    ax.set_title("VIT-AP Campus Map: Gates, Parking Lots and Destinations", fontsize=15, fontweight="bold")

    from matplotlib.lines import Line2D

    legend_elements = [
        Line2D([0], [0], marker="s", color="w", markerfacecolor="#d62728", markersize=10, label="Gates"),
        Line2D([0], [0], marker="P", color="w", markerfacecolor="#1f77b4", markersize=11, label="Parking lots"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#2ca02c", markersize=7, label="Destinations"),
        Line2D([0], [0], color="#9aa0a6", linewidth=2, label="Roads"),
    ]
    ax.legend(handles=legend_elements, loc="upper left", framealpha=0.95)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"OK: Campus graph exported: {output_path}")
    plt.close(fig)

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Export campus graph as PNG diagram"
    )
    parser.add_argument(
        "--campus", required=True, help="Campus ID (e.g., vitap, toy_small)"
    )
    parser.add_argument(
        "--config", required=True, help="Path to campus YAML config file"
    )
    parser.add_argument(
        "--output", required=True, help="Output PNG file path"
    )

    parser.add_argument(
        "--basemap", default=None, help="Optional map image to draw the graph on (e.g. docs/vitap_basemap.png)"
    )

    args = parser.parse_args()
    export_campus_graph_png(args.campus, args.config, args.output, args.basemap)
