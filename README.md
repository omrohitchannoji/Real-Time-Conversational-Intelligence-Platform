# 🚀 Real-Time Conversational Context Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Apache Kafka](https://img.shields.io/badge/Apache_Kafka-3.5-231F20?style=for-the-badge&logo=apachekafka&logoColor=white)](https://kafka.apache.org/)
[![Apache Spark](https://img.shields.io/badge/Apache_Spark-3.5-E25A1C?style=for-the-badge&logo=apachespark&logoColor=white)](https://spark.apache.org/)
[![MongoDB Atlas](https://img.shields.io/badge/MongoDB_Atlas-Cloud-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com/cloud/atlas)
[![Neo4j](https://img.shields.io/badge/Neo4j-Graph_DB-008CC1?style=for-the-badge&logo=neo4j&logoColor=white)](https://neo4j.com/)
[![Groq LPU](https://img.shields.io/badge/Groq_LPU-Llama_3.3_70B-F05032?style=for-the-badge&logo=groq&logoColor=white)](https://groq.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)

A state-of-the-art, high-throughput **Real-Time Conversational Context Modeling and Network Intelligence Platform**. 

This enterprise-grade system ingests, validates, enriches, and visualizes high-velocity streaming conversation data from multi-channel sources (Reddit, WhatsApp, Twitter). It combines **Apache Kafka** and **PySpark Structured Streaming** with **Google EmbeddingGemma (768D)**, **Groq LPU Llama-3.3-70B**, **MongoDB Atlas Cloud**, and **Neo4j Graph Database** to deliver real-time sentiment, topic modeling, community cluster detection, and social relationship graph analytics.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Data_Ingestion [📡 Data Ingestion & Streaming Layer]
        A[Multi-Channel Raw Streams\nReddit / WhatsApp / Twitter] -->|Publish JSON Bytes| B[Apache Kafka 3.5 Broker\ntopic: conversational-context]
        B -->|Micro-Batch Stream| C[PySpark 3.5 Structured Streaming]
    end

    subgraph Validation_Enrichment [⚡ 8-Layer Validation & AI Enrichment Engine]
        C --> D{8-Layer Schema & Business Validator}
        D -->|Validation Failed| E[Dead Letter Queue DLQ\nMongoDB validation_errors]
        D -->|Validation Passed| F[Google EmbeddingGemma-300M\n768D Dense Context Vector]
        F --> G[Groq LPU Llama-3.3-70B\nZero-Shot Topic & Intent Classifier]
        G --> H[Cosine Similarity Matrix\nS ∈ 0, 1 Parent Alignment]
    end

    subgraph Dual_Database [☁️ Polyglot Cloud Datastore Engine]
        H -->|Clean Enriched JSON Docs| I[(🍃 MongoDB Atlas Cloud\nmessages & contexts)]
        H -->|Social Graph Topology| J[(🕸️ Neo4j Graph Database\nNodes: User, Topic | Edges: INTERACTED_WITH)]
    end

    subgraph Intelligence_UI [📊 Live Streamlit Intelligence Dashboard]
        I --> K[Executive KPI Overview & Analytics]
        I --> L[Live Stream Monitor & WhatsApp Chat UI]
        J --> M[2D Vis.js Physics Knowledge Graph]
        I --> N[Sentiment & Topic Treemaps]
    end
```

---

## ✨ Key Features & Capabilities

### 1. ⚡ High-Throughput Real-Time Streaming Pipeline
* **Apache Kafka & PySpark Structured Streaming**: Scalable micro-batching engine capable of processing tens of thousands of messages per minute.
* **Continuous Incremental Flushing**: Processed micro-batches write incrementally to MongoDB Atlas & Neo4j every 100 records to guarantee zero data loss.
* **Checkpoint & Fast-Skip Cache**: Automatically pre-indexes stored `comment_id`s at startup, skipping previously processed duplicate messages in `0.0001ms` without wasting LLM API tokens.

### 2. 🛡️ 8-Layer Validation Engine & Zero-Loss DLQ
* **Schema Validation**: Validates message payload types, timestamps, author IDs, and mandatory attributes.
* **Business Rule Filters**: Cleans profanity, standardizes HTML entities, normalizes timestamps (`YYYY-MM-DD HH:MM:SS`), and discards empty/deleted placeholders (`[deleted]`, `[removed]`).
* **Dead Letter Queue (DLQ)**: Malformed or failing payloads are safely isolated in the MongoDB Atlas `validation_errors` collection with full stack trace diagnostics for auditing.

### 3. 🧠 Dense Context Embeddings & Groq LPU Topic Classification
* **Google EmbeddingGemma (300M)**: Generates 768-dimensional dense semantic vector representations for conversational context modeling.
* **Groq LPU LLM (`llama-3.3-70b-versatile`)**: Performs zero-shot categorization extracting:
  * **2–4 Word Topic Category** (*e.g., "Career & Aviation Inquiries", "Legal & Inheritance Advice", "Travel & Indian Cities"*).
  * **3–4 Specific Context Keywords** (automatically filtered against custom stopword dictionaries).
  * **1-Sentence User Intent Summary**.
* **Semantic Parent Alignment**: Computes cosine similarity ($S \in [0, 1]$) between thread replies and parent messages to track topic drift.

### 4. 🕸️ Neo4j Graph Database & Network Centrality Metrics
* **Social Graph Topology**: Builds directed interaction networks `(User)-[:INTERACTED_WITH]->(User)` and bipartite topic connections `(User)-[:PARTICIPATED_IN]->(Topic)`.
* **Graph Centrality Engine**: Computes PageRank influence scores, in-degree/out-degree centrality, betweenness centrality, and Louvain modularity community detection.
* **Relationship Strength Scoring**: Assigns dynamic relationship weights ($S \in [0, 100]$) based on reply frequency, thread depth, and reciprocal communication ($A \leftrightarrow B$).

### 5. 📊 Premium Glassmorphism Streamlit Dashboard
* **Page 1: Overview Analytics**: Real-time KPI metrics, Subreddit channel distributions, Sentiment donut charts, and Groq LLM keyword frequency tables.
* **Page 2: Live Monitor & WhatsApp Chat UI**: Chat bubbles with dynamic channel/topic dropdown filtering, persistent state tracking, and in-stream regex search.
* **Page 3: Interactive 2D Knowledge Graph**: Powered by PyVis & Vis.js `ForceAtlas2Based` physics engine with 3 view modes (*Social Interactions*, *Community Clusters*, *User-Topic Bipartite*).
* **Page 4: Sentiment & Topic Intelligence**: Interactive Plotly treemaps, topic distribution breakdown, and DLQ error inspection.

---

## 🛠️ Technology Stack

| Layer | Technologies Used |
| :--- | :--- |
| **Language** | Python 3.11+ |
| **Streaming & Ingestion** | Apache Kafka 3.5, PySpark 3.5 (Structured Streaming), PySpark SQL |
| **NLP & LLM Intelligence** | Groq LPU API (`llama-3.3-70b-versatile`), HuggingFace Transformers (`google/embeddinggemma-300m`), PyTorch, NumPy |
| **Graph & Analytics** | NetworkX, Neo4j Python Driver, Cypher Query Language, PyVis |
| **Datastores** | MongoDB Atlas Cloud (PyMongo), Neo4j Graph DB |
| **Visualization & UI** | Streamlit, Plotly Express/GO, Custom CSS Glassmorphism, Vis.js |

---

## 📁 Repository Structure

```text
Real-Time-Conversational-Context-Modeling/
├── config/                         # Configuration settings
│   ├── kafka_config.py             # Kafka bootstrap & topic configurations
│   ├── mongodb_config.py           # MongoDB connection strings & schema keys
│   ├── neo4j_config.py             # Neo4j URI & auth settings
│   └── spark_config.py             # PySpark master & JVM memory tuning
├── kafka_pipeline/                 # Kafka streaming layer
│   ├── producer.py                 # High-throughput data stream producer
│   └── serializer.py               # JSON byte payload serializer
├── spark/                          # PySpark Structured Streaming engine
│   ├── spark_consumer.py           # Main streaming entry point & checkpointing
│   ├── kafka_reader.py             # Kafka stream reader & offset listener
│   ├── transformations.py          # PySpark SQL payload parsing
│   ├── consumer_validation.py      # Worker task for validation & AI enrichment
│   └── mongo_sink.py               # Parallel micro-batch sink to MongoDB & Neo4j
├── nlp/                            # Natural Language Processing & Vector Store
│   ├── embeddings.py               # EmbeddingGemma 768D vector engine
│   ├── topic_detection.py          # Groq LPU Llama-3.3-70B classifier
│   └── vector_store.py             # Cosine similarity calculation utilities
├── relationship/                   # Social Network Graph Engine
│   ├── graph_builder.py            # NetworkX directed interaction graph builder
│   ├── inference.py                # Reciprocity & co-participation inference
│   └── metrics.py                  # PageRank, degree centrality & community detection
├── neo4j/                          # Neo4j Graph Database integration
│   ├── graph_queries.py            # Reusable Cypher query constants
│   └── neo4j_writer.py             # Neo4j driver & batch write handlers
├── database/                       # Cloud Datastore Drivers
│   ├── mongo_connection.py         # MongoDB Atlas client with DNS resilience
│   ├── mongo_writer.py             # Idempotent bulk upsert handlers
│   └── validation_logs.py          # Dead Letter Queue (DLQ) writer
├── dashboard/                      # Live Streamlit Intelligence UI
│   ├── app.py                      # Main Streamlit application & navigation
│   └── analytics.py                # Aggregation queries, chart builders & PyVis graphs
├── clean_mongodb_stopwords.py      # Database batch stopword migration utility
├── test_graph_analytics.py         # End-to-end graph analytics verification test
├── .env                            # Environment variables (API keys & URIs)
└── requirements.txt                # Python dependencies manifest
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
* **Python**: `3.11` or higher
* **Java**: OpenJDK 11 or 17 (Required for PySpark)
* **Docker & Docker Compose** (Optional, for running local Kafka & Neo4j)

### 2. Environment Setup
Clone the repository and set up a Python virtual environment:
```bash
git clone https://github.com/omrohitchannoji/Real-Time-Conversational-Intelligence-Platform.git
cd Real-Time-Conversational-Intelligence-Platform

python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Environment Variables Configuration
Create a `.env` file in the project root directory with your credentials:
```env
# Groq LPU API Key
GROQ_API_KEY=your_groq_api_key_here

# MongoDB Atlas Cloud Connection
MONGODB_URI=mongodb+srv://<username>:<password>@cluster.mongodb.net/context-modeling

# Neo4j Graph Database Connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password

# Kafka Settings
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC=conversational-context
```

---

## 🎮 Running the Platform

### Option A: Launch the Streamlit Intelligence Dashboard
```bash
streamlit run dashboard/app.py
```
Open your browser at `http://localhost:8501`.

### Option B: Start the PySpark Streaming Pipeline
```bash
python -m spark.spark_consumer
```

### Option C: Run the Streaming Producer
```bash
python -m kafka_pipeline.producer
```

### Option D: Perform MongoDB Stopword Cleanup Migration
```bash
python clean_mongodb_stopwords.py
```

### Option E: Run End-to-End Graph Verification Tests
```bash
python test_graph_analytics.py
```

---

## 📄 License & Attribution

Distributed under the **MIT License**. See `LICENSE` for details. Built with ❤️ for Real-Time Conversational AI & Social Network Intelligence research.
