#!/usr/bin/env python3
"""
Export a campus graph as PNG diagram.

Usage:
  python scripts/export_campus_graph_png.py --campus <campus_id> --output <path.png>

Reuses existing graph_service to build the routable network, then
visualizes it with matplotlib/networkx for inclusion in reports.
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx

sys.path.insert(0, str(Path(__file__).parent.parent))

from digital_twin.config_loader import load_campus_config
from digital_twin.db import apply_migrations, get_connection
from digital_twin.graph_service import CampusGraphService

PROJECT_ROOT = Path(__file__).parent.parent


def export_campus_graph_png(campus_id: str, config_path: str, output_path: str):
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

    # Layout
    pos = nx.spring_layout(graph, seed=42, k=2, iterations=50)

    # Colors by node type
    node_colors = []
    for node in graph.nodes():
        node_type = graph.nodes[node].get("type", "unknown")
        if node_type == "gate":
            node_colors.append("red")
        elif node_type == "parking_lot":
            node_colors.append("blue")
        elif node_type == "destination":
            node_colors.append("green")
        else:
            node_colors.append("gray")

    # Draw
    fig, ax = plt.subplots(figsize=(12, 10))
    nx.draw_networkx_nodes(
        graph, pos, node_color=node_colors, node_size=800, ax=ax, alpha=0.9
    )
    nx.draw_networkx_edges(graph, pos, edge_color="gray", width=1, ax=ax, alpha=0.5)
    nx.draw_networkx_labels(graph, pos, font_size=8, ax=ax)

    ax.set_title(f"Campus Graph: {campus_id}", fontsize=16, fontweight="bold")
    ax.axis("off")

    # Legend
    from matplotlib.patches import Patch

    legend_elements = [
        Patch(facecolor="red", label="Gates (entry/exit)"),
        Patch(facecolor="blue", label="Parking Lots"),
        Patch(facecolor="green", label="Destinations (buildings)"),
    ]
    ax.legend(handles=legend_elements, loc="upper left")

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
        "--campus", required=True, help="Campus ID (e.g., vitap, sample, synthetic_large)"
    )
    parser.add_argument(
        "--config", required=True, help="Path to campus YAML config file"
    )
    parser.add_argument(
        "--output", required=True, help="Output PNG file path"
    )

    args = parser.parse_args()
    export_campus_graph_png(args.campus, args.config, args.output)
