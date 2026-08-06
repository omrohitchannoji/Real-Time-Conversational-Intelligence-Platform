import logging
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase, Driver
from config.neo4j_config import (
    NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE,
    NEO4J_MAX_CONNECTION_LIFETIME, NEO4J_MAX_CONNECTION_POOL_SIZE
)
from graph_db.graph_queries import (
    CREATE_USER_CONSTRAINT, CREATE_COMMENT_CONSTRAINT, CREATE_TOPIC_CONSTRAINT,
    CREATE_USER_PAGERANK_INDEX, UPSERT_USER, UPSERT_COMMENT_AND_POSTED,
    CREATE_COMMENT_HIERARCHY, CREATE_DIRECT_REPLY_INTERACTION,
    UPSERT_AGGREGATED_INTERACTION, UPSERT_USER_TOPIC, UPDATE_USER_COMMUNITY_METRICS,
    GET_TOP_INFLUENCERS_CYPHER, GET_USER_NEIGHBORHOOD_CYPHER, GET_COMMUNITY_SUMMARY_CYPHER
)

logger = logging.getLogger(__name__)


class Neo4jWriter:
    """
    Neo4j Graph Database Driver & Writer Manager.
    Handles connection pooling, schema initialization, batch Cypher ingestion,
    and property graph queries.
    """

    def __init__(self, uri: str = NEO4J_URI, user: str = NEO4J_USER, password: str = NEO4J_PASSWORD, database: str = NEO4J_DATABASE):
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self._driver: Optional[Driver] = None
        self._connected = False

    def connect(self) -> bool:
        """Establishes connection driver with Neo4j cluster/instance."""
        try:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=NEO4J_MAX_CONNECTION_LIFETIME,
                max_connection_pool_size=NEO4J_MAX_CONNECTION_POOL_SIZE
            )
            self._driver.verify_connectivity()
            self._connected = True
            logger.info(f"[NEO4J] Successfully connected to Neo4j at {self.uri}")
            self.init_schema()
            return True
        except Exception as e:
            self._connected = False
            logger.warning(f"[NEO4J WARN] Could not connect to Neo4j at {self.uri}: {e}")
            return False

    @property
    def is_connected(self) -> bool:
        return self._connected and self._driver is not None

    def close(self):
        """Closes the Neo4j driver connection pool."""
        if self._driver:
            self._driver.close()
            self._connected = False
            logger.info("[NEO4J] Closed Neo4j driver connection.")

    def init_schema(self):
        """Creates unique constraints and indexes on nodes."""
        if not self.is_connected:
            return
        
        constraints = [
            CREATE_USER_CONSTRAINT,
            CREATE_COMMENT_CONSTRAINT,
            CREATE_TOPIC_CONSTRAINT,
            CREATE_USER_PAGERANK_INDEX
        ]
        with self._driver.session(database=self.database) as session:
            for query in constraints:
                try:
                    session.run(query)
                except Exception as e:
                    logger.debug(f"[NEO4J SCHEMA] Constraint creation note: {e}")
        logger.info("[NEO4J] Schema constraints and indexes verified.")

    def write_interaction(
        self,
        author_a: str,
        author_b: str,
        comment_id: str,
        parent_id: str,
        timestamp: str,
        sentiment_score: float = 0.0,
        relationship_score: float = 50.0,
        topic: Optional[str] = None
    ) -> bool:
        """
        Writes a single direct reply interaction between author_a and author_b to Neo4j.
        """
        if not self.is_connected:
            return False

        query_params = {
            "author_a": author_a,
            "author_b": author_b,
            "comment_id": comment_id,
            "parent_id": parent_id,
            "timestamp": timestamp,
            "sentiment_score": float(sentiment_score),
            "relationship_score": float(relationship_score)
        }

        try:
            with self._driver.session(database=self.database) as session:
                # 1. Create direct reply interaction
                session.run(CREATE_DIRECT_REPLY_INTERACTION, **query_params)
                # 2. Upsert aggregated interaction edge
                session.run(UPSERT_AGGREGATED_INTERACTION, **query_params)
                # 3. Topic association if present
                if topic:
                    session.run(UPSERT_USER_TOPIC, username=author_a, topic_name=topic)
                    session.run(UPSERT_USER_TOPIC, username=author_b, topic_name=topic)
            return True
        except Exception as e:
            logger.error(f"[NEO4J ERROR] Failed to write interaction ({author_a} -> {author_b}): {e}")
            return False

    def batch_write_interactions(self, interactions: List[Dict[str, Any]]) -> int:
        """
        Batch ingests a list of interaction records into Neo4j graph.
        Returns count of successfully ingested records.
        """
        if not self.is_connected or not interactions:
            return 0

        success_count = 0
        with self._driver.session(database=self.database) as session:
            for record in interactions:
                try:
                    author_a = record.get("author_a")
                    author_b = record.get("author_b")
                    if not author_a or not author_b:
                        continue
                    
                    params = {
                        "author_a": author_a,
                        "author_b": author_b,
                        "comment_id": record.get("comment_id", ""),
                        "parent_id": record.get("parent_id", ""),
                        "timestamp": record.get("timestamp", ""),
                        "sentiment_score": float(record.get("sentiment_score", 0.0)),
                        "relationship_score": float(record.get("relationship_score", 50.0))
                    }
                    session.run(CREATE_DIRECT_REPLY_INTERACTION, **params)
                    session.run(UPSERT_AGGREGATED_INTERACTION, **params)
                    
                    topic = record.get("topic") or record.get("subreddit")
                    if topic:
                        session.run(UPSERT_USER_TOPIC, username=author_a, topic_name=topic)
                        session.run(UPSERT_USER_TOPIC, username=author_b, topic_name=topic)
                    
                    success_count += 1
                except Exception as e:
                    logger.error(f"[NEO4J BATCH ERROR] Record error: {e}")

        logger.info(f"[NEO4J] Successfully batch ingested {success_count}/{len(interactions)} interaction records.")
        return success_count

    def update_user_graph_metrics(self, user_metrics: List[Dict[str, Any]]) -> int:
        """
        Updates calculated PageRank, Centrality, and Community IDs on User nodes in Neo4j.
        """
        if not self.is_connected or not user_metrics:
            return 0

        updated_count = 0
        with self._driver.session(database=self.database) as session:
            for item in user_metrics:
                try:
                    session.run(
                        UPDATE_USER_COMMUNITY_METRICS,
                        username=item["username"],
                        community_id=item.get("community_id", -1),
                        pagerank=float(item.get("pagerank", 0.0)),
                        in_degree=int(item.get("in_degree", 0)),
                        out_degree=int(item.get("out_degree", 0)),
                        betweenness=float(item.get("betweenness", 0.0))
                    )
                    updated_count += 1
                except Exception as e:
                    logger.error(f"[NEO4J METRICS ERROR] Could not update user {item.get('username')}: {e}")

        logger.info(f"[NEO4J] Updated graph metrics for {updated_count} user nodes.")
        return updated_count

    def get_top_influencers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Queries Neo4j for top influencer users ordered by in-degree and PageRank."""
        if not self.is_connected:
            return []
        try:
            with self._driver.session(database=self.database) as session:
                result = session.run(GET_TOP_INFLUENCERS_CYPHER, limit=limit)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"[NEO4J QUERY ERROR] Failed to fetch top influencers: {e}")
            return []

    def get_community_summary(self) -> List[Dict[str, Any]]:
        """Queries community distribution summary from Neo4j."""
        if not self.is_connected:
            return []
        try:
            with self._driver.session(database=self.database) as session:
                result = session.run(GET_COMMUNITY_SUMMARY_CYPHER)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"[NEO4J QUERY ERROR] Failed to fetch community summary: {e}")
            return []
