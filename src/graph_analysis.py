
import os
import pandas as pd
import networkx as nx

from src.storage import get_connection
from config import REPORTS_DIR


def load_relationship_edges():
    connection = get_connection()

    try:
        query = """
            SELECT
                edge_id,
                source_entity_type,
                source_entity_id,
                target_entity_type,
                target_entity_id,
                relationship_type,
                weight
            FROM relationship_edges
        """

        dataframe = pd.read_sql(query, connection)

        print("\nRELATIONSHIP DATA LOADED")
        print("Total edges:", len(dataframe))

        return dataframe

    finally:
        connection.close()


def build_relationship_graph(dataframe):
    graph = nx.Graph()

    for _, row in dataframe.iterrows():
        source = (
            f"{row['source_entity_type']}:"
            f"{row['source_entity_id']}"
        )

        target = (
            f"{row['target_entity_type']}:"
            f"{row['target_entity_id']}"
        )

        graph.add_node(source, entity_type=row["source_entity_type"])
        graph.add_node(target, entity_type=row["target_entity_type"])

        graph.add_edge(
            source,
            target,
            edge_id=row["edge_id"],
            relationship_type=row["relationship_type"],
            weight=float(row["weight"]) if pd.notna(row["weight"]) else 1.0
        )

    print("\nGRAPH CREATED SUCCESSFULLY")
    print("Total nodes:", graph.number_of_nodes())
    print("Total edges:", graph.number_of_edges())

    return graph


def analyze_graph(graph):
    print("\nRELATIONSHIP GRAPH ANALYSIS")
    print("=" * 55)

    print("Number of nodes:", graph.number_of_nodes())
    print("Number of edges:", graph.number_of_edges())

    components = list(nx.connected_components(graph))

    print("Connected components:", len(components))

    degree_centrality = nx.degree_centrality(graph)

    sorted_nodes = sorted(
        degree_centrality.items(),
        key=lambda item: item[1],
        reverse=True
    )

    print("\nTOP 10 CONNECTED ENTITIES")
    print("-" * 55)

    for node, score in sorted_nodes[:10]:
        print(f"{node} | Degree centrality: {score:.6f}")

    return degree_centrality, components


def export_graph_results(graph, degree_centrality, components):
    os.makedirs(REPORTS_DIR, exist_ok=True)

    node_records = []

    for node, score in degree_centrality.items():
        node_records.append({
            "entity": node,
            "degree": graph.degree(node),
            "degree_centrality": score,
            "connected_component": next(
                index
                for index, component in enumerate(components, start=1)
                if node in component
            )
        })

    nodes_df = pd.DataFrame(node_records)

    nodes_path = os.path.join(
        REPORTS_DIR,
        "graph_node_analysis.csv"
    )

    nodes_df.to_csv(nodes_path, index=False)

    edge_records = []

    for source, target, attributes in graph.edges(data=True):
        edge_records.append({
            "source": source,
            "target": target,
            "edge_id": attributes.get("edge_id"),
            "relationship_type": attributes.get("relationship_type"),
            "weight": attributes.get("weight")
        })

    edges_df = pd.DataFrame(edge_records)

    edges_path = os.path.join(
        REPORTS_DIR,
        "graph_edge_analysis.csv"
    )

    edges_df.to_csv(edges_path, index=False)

    print("\nGRAPH REPORTS EXPORTED")
    print("Node report:", nodes_path)
    print("Edge report:", edges_path)


def main():
    dataframe = load_relationship_edges()

    if dataframe.empty:
        print("No relationship edges found.")
        return

    graph = build_relationship_graph(dataframe)

    degree_centrality, components = analyze_graph(graph)

    export_graph_results(
        graph,
        degree_centrality,
        components
    )

    print("\nGRAPH ANALYSIS COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    main()
