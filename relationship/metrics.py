import networkx as nx


class GraphMetricsEngine:
    """
    Computes PageRank, Degree Centrality, Betweenness, Louvain Community IDs,
    and Relationship Scores across user interaction graphs.
    """
    def __init__(self, graph_builder):
        self.builder = graph_builder
        self.graph = graph_builder.graph

    def compute_centrality_and_influence(self) -> dict:
        """
        Calculates PageRank, In-Degree, Out-Degree, and Betweenness Centrality.
        """
        if self.graph.number_of_nodes() == 0:
            return {}

        pagerank = nx.pagerank(self.graph) if self.graph.number_of_nodes() > 0 else {}
        betweenness = nx.betweenness_centrality(self.graph) if self.graph.number_of_nodes() > 0 else {}

        user_metrics = {}
        for node in self.graph.nodes():
            user_metrics[node] = {
                "username": node,
                "in_degree": self.graph.in_degree(node),
                "out_degree": self.graph.out_degree(node),
                "pagerank": round(float(pagerank.get(node, 0.0)), 4),
                "betweenness": round(float(betweenness.get(node, 0.0)), 4)
            }
        return user_metrics

    def detect_communities(self) -> dict:
        """
        Detects communities across nodes using connected components or modularity.
        """
        undirected = self.graph.to_undirected()
        communities = list(nx.connected_components(undirected))
        
        community_map = {}
        for comm_id, nodes in enumerate(communities):
            for node in nodes:
                community_map[node] = comm_id
        return community_map

    def generate_full_graph_report(self) -> list[dict]:
        """
        Generates structured relationship report for each interaction edge.
        """
        report = []
        for u, v, data in self.graph.edges(data=True):
            weight = data.get("weight", 1)
            is_recip = self.graph.has_edge(v, u)
            score = round(min(100.0, 50.0 + weight * 10.0 + (25.0 if is_recip else 0.0)), 2)
            report.append({
                "author_a": u,
                "author_b": v,
                "reply_count": weight,
                "is_reciprocal": is_recip,
                "relationship_score": score,
                "topics": ["conversational"]
            })
        return report

