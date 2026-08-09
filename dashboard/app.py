import sys
import os

# Auto-resolve project root directory in sys.path so 'from dashboard.analytics' works anywhere
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import time

from dashboard.analytics import (
    get_pipeline_kpis,
    get_channel_distribution,
    get_sentiment_distribution,
    get_top_keywords,
    search_messages,
    get_available_channels,
    get_channel_chat_messages,
    get_dlq_logs,
    get_top_neo4j_influencers,
    get_neo4j_community_summary,
    generate_social_interaction_graph_html,
    generate_user_topic_bipartite_graph_html,
    generate_community_cluster_graph_html
)

# Configure Streamlit Page


st.set_page_config(
    page_title="Conversational Context Intelligence Platform",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Ultra-Premium Glassmorphism CSS Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    .stApp {
        background: linear-gradient(135deg, #0B0F19 0%, #0F172A 50%, #030712 100%);
    }
    .main-title {
        font-size: 2.3rem;
        font-weight: 700;
        background: linear-gradient(90deg, #00E676 0%, #38BDF8 50%, #818CF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.1rem;
    }
    .sub-title {
        font-size: 0.95rem;
        color: #94A3B8;
        margin-bottom: 1.5rem;
    }
    .kpi-box {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(56, 189, 248, 0.2);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        backdrop-filter: blur(10px);
    }
    .kpi-title {
        font-size: 0.82rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #38BDF8;
    }
    .chat-bubble-received {
        background: rgba(30, 41, 59, 0.8);
        border-left: 4px solid #38BDF8;
        padding: 14px 18px;
        border-radius: 14px;
        margin-bottom: 12px;
        color: #F8FAFC;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    .chat-bubble-sent {
        background: rgba(6, 78, 59, 0.8);
        border-right: 4px solid #10B981;
        padding: 14px 18px;
        border-radius: 14px;
        margin-bottom: 12px;
        color: #ECFDF5;
        text-align: right;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    .chat-meta {
        font-size: 0.76rem;
        color: #94A3B8;
        margin-top: 6px;
    }
    /* =========================================================
       PREMIUM TOP NAVIGATION
       Keeps Streamlit radio functionality but presents it as
       clean application navigation rather than four buttons.
       ========================================================= */

    div[data-testid="stRadio"] input[type="radio"] {
        position: absolute !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }

    div[data-testid="stRadio"] {
        position: sticky;
        top: 0;
        z-index: 999;
        padding: 6px 0 16px 0;
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] {
        position: relative;
        display: flex;
        align-items: stretch;
        justify-content: center;
        gap: 6px;

        padding: 7px;
        margin: 0 0 22px 0;

        background: rgba(15, 23, 42, 0.52);
        border: 1px solid rgba(148, 163, 184, 0.12);
        border-radius: 18px;

        backdrop-filter: blur(22px);
        -webkit-backdrop-filter: blur(22px);

        box-shadow:
            0 12px 35px rgba(0, 0, 0, 0.28),
            inset 0 1px 0 rgba(255, 255, 255, 0.04);
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] > label {
        position: relative;
        flex: 1 1 0;

        display: flex;
        align-items: center;
        justify-content: center;

        min-height: 44px;
        padding: 9px 18px;
        margin: 0 !important;

        background: transparent !important;
        border: 1px solid transparent !important;
        border-radius: 12px;

        cursor: pointer;
        transition:
            color 0.2s ease,
            background 0.2s ease,
            transform 0.2s ease;
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] > label
    [data-testid="stMarkdownContainer"] p {
        margin: 0;
        color: #94A3B8;
        font-size: 0.91rem;
        font-weight: 500;
        letter-spacing: 0.15px;
        white-space: nowrap;
        transition: color 0.2s ease;
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
        background: rgba(255, 255, 255, 0.035) !important;
        transform: translateY(-1px);
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover
    [data-testid="stMarkdownContainer"] p {
        color: #E2E8F0;
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) {
        background: linear-gradient(
            180deg,
            rgba(56, 189, 248, 0.12),
            rgba(56, 189, 248, 0.045)
        ) !important;

        border: 1px solid rgba(56, 189, 248, 0.16) !important;

        box-shadow:
            inset 0 1px 0 rgba(255, 255, 255, 0.035),
            0 4px 18px rgba(56, 189, 248, 0.07);
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked)::after {
        content: "";
        position: absolute;
        left: 22%;
        right: 22%;
        bottom: -7px;
        height: 2px;
        border-radius: 999px;

        background: linear-gradient(
            90deg,
            transparent,
            #38BDF8,
            #818CF8,
            transparent
        );

        box-shadow: 0 0 12px rgba(56, 189, 248, 0.55);
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked)
    [data-testid="stMarkdownContainer"] p {
        color: #F8FAFC !important;
        font-weight: 650;
    }

    @media (max-width: 900px) {
        div[data-testid="stRadio"] > div[role="radiogroup"] {
            overflow-x: auto;
            justify-content: flex-start;
        }

        div[data-testid="stRadio"] > div[role="radiogroup"] > label {
            flex: 0 0 auto;
            padding: 9px 14px;
        }
    }

</style>
""", unsafe_allow_html=True)

# Application Header Deck
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    st.markdown('<div class="main-title">🚀 Real-Time Conversational Context & Intelligence Platform</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Distributed Event-Driven Ingestion Engine & Social Topology Analytics Dashboard</div>', unsafe_allow_html=True)
with header_col2:
    st.markdown("""
    <div style="text-align:right; margin-top:10px;">
        <span style="font-size:0.82rem; background:rgba(16,185,129,0.15); color:#10B981; border:1px solid rgba(16,185,129,0.3); padding:5px 12px; border-radius:20px; font-weight:600;">
            🟢 Core Engine: Streaming Live
        </span>
    </div>
    """, unsafe_allow_html=True)

# 🧭 SLEEK TOP NAVIGATION BAR
nav_options = [
    "📊  Overview",
    "💬  Live Monitor",
    "🕸️  Graph Intelligence",
    "🎯  Sentiment & Topics"
]

_nav_kpis = get_pipeline_kpis()
_nav_dlq_preview = get_dlq_logs(limit=30)

selected_tab = st.radio(
    "Navigation Menu",
    nav_options,
    horizontal=True,
    label_visibility="collapsed",
    key="top_navbar_selection"
)


# Keyboard shortcuts (press 1–4 to jump tabs) + hover tooltips describing each
# page. Runs inside a same-origin component iframe, so it reaches into the
# parent document to decorate the real nav pills — a guarded, idempotent
# listener attach avoids stacking duplicate handlers across reruns.
components.html("""
<script>
(function() {
    var tooltips = [
        "Executive KPIs, trending topics & keyword frequency  —  press 1",
        "Live WhatsApp-style monitor with keyword & topic filters  —  press 2",
        "Neo4j graph intelligence: influencers, communities & topology  —  press 3",
        "AI sentiment breakdown & cross-channel comparison  —  press 4"
    ];
    var labels = window.parent.document.querySelectorAll('div[data-testid="stRadio"] div[role="radiogroup"] label');
    labels.forEach(function(label, i) {
        if (tooltips[i]) { label.title = tooltips[i]; }
    });

    if (window.parent.__cciKeyNavAttached) return;
    window.parent.__cciKeyNavAttached = true;
    window.parent.document.addEventListener('keydown', function(e) {
        var tag = (e.target && e.target.tagName) || '';
        if (tag === 'INPUT' || tag === 'TEXTAREA') return;
        var keyMap = {'1': 0, '2': 1, '3': 2, '4': 3};
        if (!keyMap.hasOwnProperty(e.key)) return;
        var currentLabels = window.parent.document.querySelectorAll('div[data-testid="stRadio"] div[role="radiogroup"] label');
        var idx = keyMap[e.key];
        if (currentLabels.length > idx) { currentLabels[idx].click(); }
    });
})();
</script>
""", height=0)

# Sidebar System Health & DLQ Audit Logs
st.sidebar.title("⚡ Core Engine Status")
st.sidebar.markdown("""
- **Database:** 🟢 MongoDB Atlas Connected
- **Graph DB:** 🕸️ Neo4j Graph Synced
- **Stream Engine:** ⚡ Kafka + PySpark Active
- **NLP Model:** 🧠 Groq LLaMA-3.3-70B
""")
st.sidebar.divider()

# Sidebar Expander for Technical DLQ Error Audit Logs (reuses the preview
# fetched above for the nav badge, avoiding a duplicate MongoDB round-trip)
with st.sidebar.expander("🚨 Technical DLQ Error Audit Logs"):
    df_dlq = _nav_dlq_preview
    if df_dlq.empty:
        st.success("Zero DLQ Errors Recorded!")
    else:
        st.warning(f"Found {len(df_dlq)} rejected records.")
        st.dataframe(df_dlq[["reason", "timestamp", "pipeline_stage"]], height=200)
        csv_data = df_dlq.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Export DLQ CSV", csv_data, "dlq_errors.csv", "text/csv")

# ==============================================================================
# TAB 1: OVERVIEW & TRENDING (Mentor's Page 1)
# ==============================================================================
if selected_tab == "📊  Overview":

    st.header("📊 Pipeline KPI Overview & Trending Analytics")

    # Reuse the KPIs already fetched for the nav badge above (avoids a
    # duplicate MongoDB round-trip on every rerun)
    kpis = _nav_kpis

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">Total Clean Messages</div><div class="kpi-value">{kpis["total_messages"]:,}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">Active Subreddits</div><div class="kpi-value">{kpis["total_subreddits"]}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">Total User Authors</div><div class="kpi-value">{kpis["total_authors"]:,}</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">Pipeline Health</div><div class="kpi-value" style="color:#10B981;">HEALTHY</div></div>', unsafe_allow_html=True)

    st.divider()

    # Bottom Layout: Left Column = Groq LLM Topic Bar Chart, Right Column = Groq LLM Keywords Table
    chart_col, keywords_col = st.columns([3, 2])

    with chart_col:
        st.subheader("🧠 Human-Grade Groq LLM Detected Topics")
        from dashboard.analytics import get_groq_llm_topic_distribution, get_groq_llm_top_keywords
        df_topics = get_groq_llm_topic_distribution(limit=10)
        fig = px.bar(
            df_topics,
            x="Message Count",
            y="Topic Category",
            orientation="h",
            color="Message Count",
            color_continuous_scale="Purples",
            labels={"Message Count": "Enriched Documents", "Topic Category": "Groq LLM Detected Topic"},
            text="Message Count"
        )
        fig.update_layout(
            template="plotly_dark",
            height=420,
            xaxis_title="Messages Processed",
            yaxis_title="LLM Topic Category",
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig, width=500)

    with keywords_col:
        st.subheader("🏷️ Groq LLM Context Keywords")
        df_keywords = get_groq_llm_top_keywords(top_n=12)
        max_freq = int(df_keywords["Frequency"].max()) if not df_keywords.empty else 10
        st.dataframe(
            df_keywords,
            column_config={
                "Keyword": "Context Keyword",
                "Frequency": st.column_config.ProgressColumn("Frequency", format="%d", min_value=0, max_value=max(max_freq, 1))
            },
            width=400,
            height=420
        )


# ==============================================================================
# TAB 2: LIVE MONITOR & WHATSAPP CHAT UI (Page 2)
# ==============================================================================
elif selected_tab == "💬  Live Monitor":
    st.header("💬 Live Stream Channel Monitor & WhatsApp Chat UI")

    filter_col1, filter_col2, filter_col3 = st.columns([3, 3, 1])
    with filter_col1:
        search_filter = st.text_input(
            "🔍 Live Keyword Filter:",
            placeholder="Type keyword, author, or intent to filter...",
            key="chat_live_filter"
        )
    with filter_col2:
        channels_list = get_available_channels()
        selected_channel = st.selectbox(
            "🎯 Topic / Channel Filter:",
            channels_list,
            key="topic_filter_selector"
        )
    with filter_col3:
        st.write("")
        st.write("")
        auto_refresh = st.checkbox("🔄 Auto-Refresh", value=False, key="page2_auto_refresh")

    if search_filter and search_filter.strip():
        st.caption(f"🔎 **Filter Active:** Showing messages matching **'{search_filter}'** (clear search box to restore full feed)")

    st.divider()


    # Fetch Chat Messages with real-time keyword/topic search filter
    chat_messages = get_channel_chat_messages(selected_channel, limit=35, search_query=search_filter)

    if not chat_messages:
        st.info(f"No active messages currently stored for **{selected_channel}**.")
    else:
        st.subheader(f"💬 Live Stream: {selected_channel}")


        # Render WhatsApp-Style Chat UI
        for idx, msg in enumerate(chat_messages):
            author = msg.get("author", "Anonymous")
            text = msg.get("message", "")
            timestamp = msg.get("created_utc", "")
            comment_id = msg.get("comment_id", "")
            parent_id = msg.get("parent_id", "")

            # Extract Groq LLM Context Metadata
            ctx = msg.get("context_modeling", {})
            topic_name = ctx.get("detected_topic_name", "General Community Discussion")
            keywords_list = ", ".join(ctx.get("topic_keywords", ["General"]))
            intent_summary = ctx.get("summary_intent", "")

            # Left side (Received reply) vs Right side (Sent / Primary post)
            is_reply = bool(parent_id and parent_id != "t3_none" and str(parent_id).strip() != "")

            topic_badge = f'<div style="margin-top:6px; font-size:0.8rem; background:rgba(124,58,237,0.25); border:1px solid #A78BFA; border-radius:6px; padding:3px 8px; color:#E9D5FF;"><strong>🧠 LLM Topic:</strong> {topic_name} | <strong>🔑 Keywords:</strong> {keywords_list}</div>' if topic_name else ''
            intent_badge = f'<div style="font-size:0.78rem; color:#CBD5E1; margin-top:2px;"><em>"{intent_summary}"</em></div>' if intent_summary else ''

            if is_reply:
                # Left-aligned Received Chat Bubble
                st.markdown(f"""
                <div class="chat-bubble-received">
                    <strong>👤 {author}</strong> <span style="font-size:0.75rem; color:#38BDF8;">(Received Reply to #{parent_id})</span><br>
                    <span style="font-size: 1.05rem;">{text}</span>
                    {topic_badge}
                    {intent_badge}
                    <div class="chat-meta">🕒 {timestamp} | 🔑 Comment ID: {comment_id}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Right-aligned Sent Chat Bubble
                st.markdown(f"""
                <div class="chat-bubble-sent">
                    <strong>👤 {author}</strong> <span style="font-size:0.75rem; color:#10B981;">(Primary Thread Starter)</span><br>
                    <span style="font-size: 1.05rem;">{text}</span>
                    {topic_badge}
                    {intent_badge}
                    <div class="chat-meta">🕒 {timestamp} | 🔑 Comment ID: {comment_id}</div>
                </div>
                """, unsafe_allow_html=True)

    if auto_refresh:
        time.sleep(3)
        st.rerun()


# ==============================================================================
# TAB 3: NEO4J GRAPH INTELLIGENCE & INTERACTIVE TOPOLOGY (Page 3)
# ==============================================================================
elif selected_tab == "🕸️  Graph Intelligence":
    st.header("🕸️ Neo4j Real-Time Graph Analytics & Influencer Centrality")
    st.markdown("Explore social graph topologies, parent-child reply dynamics, and user-topic knowledge bipartite structures.")

    g_col1, g_col2 = st.columns([1, 1])
    with g_col1:
        st.markdown("#### 🌟 Top Influencers (PageRank & In-Degree)")
        df_influencers = get_top_neo4j_influencers(limit=10)
        st.dataframe(df_influencers, width=500)
    with g_col2:
        st.markdown("#### 👥 Community Detection Summary (Louvain)")
        df_comm = get_neo4j_community_summary()
        st.dataframe(df_comm, width=500)

    st.markdown("---")
    st.subheader("🌐 Interactive 2D Physics Knowledge Graph Visualizer Suite")
    st.caption("Drag nodes, scroll to zoom, and hover over users and topics to inspect real-time conversational connections.")

    graph_ctrl_col1, graph_ctrl_col2 = st.columns([2, 1])
    with graph_ctrl_col1:
        node_limit = st.slider("🔧 Graph density (max relationships rendered)", min_value=10, max_value=100, value=35, step=5)
    with graph_ctrl_col2:
        st.caption("Fewer nodes = faster physics settling. More nodes = richer topology.")

    graph_tab1, graph_tab2, graph_tab3 = st.tabs([
        "💬 COMMENTED_ON / REPLIED_TO (User Reply Graph)",
        "🤝 INTERACTED_WITH (Social Influence & Louvain Communities)",
        "🏷️ PARTICIPATED_IN (User-to-Topic Knowledge Bipartite Graph)"
    ])

    with graph_tab1:
        st.markdown("**`[:COMMENTED_ON]` / `[:REPLIED_TO]` Dynamics** *(🟠 Orange = Influencer, 🔵 Blue = Contributor — node size scales with reply count)*")
        html_social = generate_social_interaction_graph_html(limit=node_limit)
        components.html(html_social, height=520, scrolling=False)

    with graph_tab2:
        st.markdown("**`[:INTERACTED_WITH]` Louvain Community Clusters** *(Color-coded sub-communities & mutual conversation bridges)*")
        html_comm = generate_community_cluster_graph_html(limit=node_limit)
        components.html(html_comm, height=520, scrolling=False)

    with graph_tab3:
        st.markdown("**`[:PARTICIPATED_IN]` User-to-Topic Bipartite Graph** *(🟣 Purple Hexagons = Groq LLM Topics | 🟢 Green Dots = Users)*")
        html_bipartite = generate_user_topic_bipartite_graph_html(limit=node_limit)
        components.html(html_bipartite, height=520, scrolling=False)


# ==============================================================================
# TAB 4: AI SENTIMENT & TOPIC DISENTANGLEMENT (Page 4)
# ==============================================================================
elif selected_tab == "🎯  Sentiment & Topics":

    st.header("🎯 AI Sentiment Distribution & Topic Disentanglement")
    st.markdown("Analyze tone, sentiment breakdown, and cross-channel conversational trends across all monitored channels.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("🟢 Conversational Sentiment Breakdown")
        df_sent = get_sentiment_distribution()
        fig_donut = px.pie(
            df_sent,
            values="Count",
            names="Sentiment",
            hole=0.5,
            color="Sentiment",
            color_discrete_map={
                "🟢 Positive": "#10B981",
                "⚪ Neutral": "#94A3B8",
                "🔴 Negative": "#EF4444"
            }
        )
        fig_donut.update_layout(
            template="plotly_dark",
            height=380,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_donut, width=400)

    with col2:
        st.subheader("🌐 Channel Multi-Compare Intelligence")
        df_channels = get_channel_distribution()
        fig_treemap = px.treemap(
            df_channels,
            path=["channel"],
            values="count",
            color="count",
            color_continuous_scale="Blues"
        )
        fig_treemap.update_layout(
            template="plotly_dark",
            height=380,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_treemap, width=400)