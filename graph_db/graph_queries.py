# Cypher Query Repository for Real-Time Conversational Graph Analytics

# -----------------------------------------------------------------------------
# 1. SCHEMA CONSTRAINTS & INDEXES
# -----------------------------------------------------------------------------
CREATE_USER_CONSTRAINT = """
CREATE CONSTRAINT user_username_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.username IS UNIQUE;
"""

CREATE_COMMENT_CONSTRAINT = """
CREATE CONSTRAINT comment_id_unique IF NOT EXISTS
FOR (c:Comment) REQUIRE c.comment_id IS UNIQUE;
"""

CREATE_TOPIC_CONSTRAINT = """
CREATE CONSTRAINT topic_name_unique IF NOT EXISTS
FOR (t:Topic) REQUIRE t.name IS UNIQUE;
"""

CREATE_USER_PAGERANK_INDEX = """
CREATE INDEX user_pagerank_idx IF NOT EXISTS
FOR (u:User) ON (u.pagerank);
"""

# -----------------------------------------------------------------------------
# 2. NODE & EDGE UPSERTS (BATCH / STREAM INGESTION)
# -----------------------------------------------------------------------------
UPSERT_USER = """
MERGE (u:User {username: $username})
ON CREATE SET u.created_at = timestamp(), u.message_count = 1
ON MATCH SET u.message_count = u.message_count + 1, u.last_active = $timestamp
RETURN u;
"""

UPSERT_COMMENT_AND_POSTED = """
MERGE (u:User {username: $author})
MERGE (c:Comment {comment_id: $comment_id})
ON CREATE SET 
    c.message = $message,
    c.created_utc = $created_utc,
    c.parent_id = $parent_id,
    c.source = $source
MERGE (u)-[:POSTED {created_utc: $created_utc}]->(c)
"""

CREATE_COMMENT_HIERARCHY = """
MATCH (child:Comment {comment_id: $comment_id})
MATCH (parent:Comment {comment_id: $parent_id})
MERGE (child)-[:REPLIES_TO_COMMENT]->(parent)
"""

CREATE_DIRECT_REPLY_INTERACTION = """
MERGE (u1:User {username: $author_a})
MERGE (u2:User {username: $author_b})
CREATE (u1)-[r:REPLIED_TO {
    comment_id: $comment_id,
    parent_id: $parent_id,
    timestamp: $timestamp,
    sentiment_score: $sentiment_score
}]->(u2)
"""

UPSERT_AGGREGATED_INTERACTION = """
MERGE (u1:User {username: $author_a})
MERGE (u2:User {username: $author_b})
MERGE (u1)-[r:INTERACTED_WITH]->(u2)
ON CREATE SET 
    r.weight = 1,
    r.relationship_score = $relationship_score,
    r.last_timestamp = $timestamp,
    r.first_timestamp = $timestamp
ON MATCH SET 
    r.weight = r.weight + 1,
    r.relationship_score = $relationship_score,
    r.last_timestamp = $timestamp
"""

UPSERT_USER_TOPIC = """
MERGE (u:User {username: $username})
MERGE (t:Topic {name: $topic_name})
MERGE (u)-[r:PARTICIPATED_IN]->(t)
ON CREATE SET r.message_count = 1
ON MATCH SET r.message_count = r.message_count + 1
"""

UPDATE_USER_COMMUNITY_METRICS = """
MATCH (u:User {username: $username})
SET u.community_id = $community_id,
    u.pagerank = $pagerank,
    u.in_degree = $in_degree,
    u.out_degree = $out_degree,
    u.betweenness = $betweenness
"""

# -----------------------------------------------------------------------------
# 3. GRAPH ANALYTICS & INSIGHT QUERY SUITE
# -----------------------------------------------------------------------------
GET_TOP_INFLUENCERS_CYPHER = """
MATCH (u:User)
OPTIONAL MATCH (u)<-[r:REPLIED_TO]-(other:User)
WITH u, count(DISTINCT other) AS in_degree, count(r) AS total_replies_received
RETURN u.username AS user, 
       coalesce(u.pagerank, 0.0) AS pagerank, 
       in_degree, 
       total_replies_received,
       coalesce(u.community_id, -1) AS community_id
ORDER BY in_degree DESC, pagerank DESC
LIMIT $limit
"""

GET_USER_NEIGHBORHOOD_CYPHER = """
MATCH (u:User {username: $username})-[r:INTERACTED_WITH]-(neighbor:User)
RETURN neighbor.username AS neighbor, 
       r.weight AS weight, 
       r.relationship_score AS relationship_score,
       r.last_timestamp AS last_timestamp
ORDER BY r.relationship_score DESC
"""

GET_COMMUNITY_SUMMARY_CYPHER = """
MATCH (u:User)
WHERE u.community_id IS NOT NULL
RETURN u.community_id AS community_id, 
       count(u) AS member_count, 
       collect(u.username)[0..5] AS top_members
ORDER BY member_count DESC
"""
