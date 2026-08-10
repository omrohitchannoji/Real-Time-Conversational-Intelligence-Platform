import networkx as nx


class UserInteractionGraphBuilder:
    """
    Builds directed user-to-user interaction graph from conversational records.
    Tracks replies, thread participation, and graph density using NetworkX.
    """
    def __init__(self):
        self.graph = nx.DiGraph()

    def build_from_records(self, records: list[dict]):
        """
        Populates directed graph edges (author_a -> author_b) based on parent-child comment links.
        """
        comment_to_author = {}
        for r in records:
            cid = str(r.get("comment_id", r.get("_id", "")))
            author = str(r.get("author", ""))
            if cid and author:
                comment_to_author[cid] = author
                if not self.graph.has_node(author):
                    self.graph.add_node(author, message_count=1)
                else:
                    self.graph.nodes[author]["message_count"] += 1

        for r in records:
            author = str(r.get("author", ""))
            parent_id = str(r.get("parent_id", ""))
            parent_author = str(r.get("parent_author", ""))

            # Resolve parent author from map if parent_author missing
            if not parent_author or parent_author in ["nan", "system", "None"]:
                parent_author = comment_to_author.get(parent_id, "")

            if author and parent_author and author != parent_author:
                if self.graph.has_edge(author, parent_author):
                    self.graph[author][parent_author]["weight"] += 1
                else:
                    self.graph.add_edge(author, parent_author, weight=1)

    def get_summary_stats(self) -> dict:
        """
        Returns graph nodes count, directed edges count, and density.
        """
        num_nodes = self.graph.number_of_nodes()
        num_edges = self.graph.number_of_edges()
        density = round(nx.density(self.graph), 4) if num_nodes > 1 else 0.0
        return {
            "num_nodes": num_nodes,
            "num_edges": num_edges,
            "density": density
        }

