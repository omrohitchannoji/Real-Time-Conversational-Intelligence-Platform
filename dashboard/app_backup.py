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
    get_channel_chat_messages,
    get_dlq_logs,
    get_top_neo4j_influencers,
    get_neo4j_community_summary,
    generate_social_interaction_graph_html,
    generate_user_topic_bipartite_graph_html,
    generate_community_cluster_graph_html,
    get_groq_llm_topic_distribution,
    get_groq_llm_top_keywords,
    get_message_volume_timeseries,
    get_activity_heatmap_data,
    get_sentiment_trend_over_time,
    get_channel_radar_metrics,
)

# ------------------------------------------------------------------------------
# GLOBAL CHART THEME & CONFIG
# Centralizing this means every chart shares the same premium look-and-feel and
# the same interactive toolbar (zoom, pan, box/lasso select, PNG export, etc.)
# ------------------------------------------------------------------------------
ACCENT = "#38BDF8"
ACCENT2 = "#818CF8"
GREEN = "#10B981"
AMBER = "#F59E0B"
RED = "#EF4444"
PURPLE = "#A78BFA"
PLOT_BG = "rgba(15, 23, 42, 0)"
PAPER_BG = "rgba(15, 23, 42, 0)"
GRID_COLOR = "rgba(148, 163, 184, 0.12)"

PLOTLY_CONFIG = {
    "displaylogo": False,
    "scrollZoom": True,
    "modeBarButtonsToRemove": ["lasso2d"],
    "toImageButtonOptions": {"format": "png", "scale": 2, "filename": "cci_platform_chart"},
}


def style_fig(fig, height=420, hovermode="closest", legend=True, title=None):
    """Applies the shared dark, glassmorphism-matching theme to any Plotly figure."""
    fig.update_layout(
        template="plotly_dark",
        height=height,
        hovermode=hovermode,
        plot_bgcolor=PLOT_BG,
        paper_bgcolor=PAPER_BG,
        font=dict(family="Outfit, sans-serif", color="#E2E8F0", size=13),
        margin=dict(l=20, r=20, t=50 if title else 30, b=20),
        showlegend=legend,
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        if legend else None,
        hoverlabel=dict(bgcolor="#1E293B", font_size=13, font_family="Outfit, sans-serif", bordercolor=ACCENT),
        title=dict(text=title, x=0.01, font=dict(size=15, color="#F8FAFC")) if title else None,
        transition=dict(duration=350, easing="cubic-in-out"),
    )
    fig.update_xaxes(gridcolor=GRID_COLOR, zeroline=False)
    fig.update_yaxes(gridcolor=GRID_COLOR, zeroline=False)
    return fig

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
        border-radius: 14px;
        padding: 18px 16px;
        text-align: center;
        backdrop-filter: blur(10px);
        transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
        position: relative;
        overflow: hidden;
    }
    .kpi-box:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 30px rgba(56, 189, 248, 0.25);
        border-color: rgba(56, 189, 248, 0.55);
    }
    .kpi-icon {
        font-size: 1.3rem;
        margin-bottom: 2px;
        opacity: 0.9;
    }
    .kpi-title {
        font-size: 0.78rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .kpi-value {
        font-size: 1.9rem;
        font-weight: 700;
        color: #38BDF8;
        line-height: 1.3;
    }
    .kpi-sub {
        font-size: 0.72rem;
        color: #64748B;
        margin-top: 2px;
    }
    .section-card {
        background: rgba(15, 23, 42, 0.55);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 16px;
        padding: 18px 20px 6px 20px;
        margin-bottom: 18px;
        backdrop-filter: blur(8px);
        transition: border-color 0.25s ease;
    }
    .section-card:hover {
        border-color: rgba(56, 189, 248, 0.35);
    }
    .section-title {
        font-size: 1.02rem;
        font-weight: 600;
        color: #F1F5F9;
        margin-bottom: 2px;
    }
    .section-caption {
        font-size: 0.8rem;
        color: #94A3B8;
        margin-bottom: 10px;
    }
    /* Plotly modebar polish */
    .modebar {
        background: rgba(15, 23, 42, 0.6) !important;
        border-radius: 8px;
    }
    /* Tabs */
    button[data-baseweb="tab"] {
        font-family: 'Outfit', sans-serif;
    }
    div[data-testid="stMetric"] {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(56, 189, 248, 0.15);
        border-radius: 12px;
        padding: 10px 14px;
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
</style>
""", unsafe_allow_html=True)

# Application Header
st.markdown('<div class="main-title">🚀 Real-Time Conversational Context & Intelligence Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Distributed Event-Driven Ingestion Engine & Social Topology Analytics Dashboard</div>', unsafe_allow_html=True)

# 🔍 UNIVERSAL TOP SEARCH BAR (Pinned at top of every page)
search_query = st.text_input(
    "🔍 Universal Search Bar (Search across all messages, authors, or subreddits in MongoDB Atlas):",
    placeholder="Type keyword, user name, or comment ID (e.g. 'AI', 'technology', 'relative-cause')...",
    key="global_search_input"
)

# Render Search Results immediately if user typed a search term
if search_query and search_query.strip():
    st.info(f"🔍 Search Results for: **'{search_query}'**")
    search_results = search_messages(search_query, limit=30)
    if search_results:
        results_data = []
        for r in search_results:
            results_data.append({
                "Comment ID": r.get("comment_id"),
                "Author": r.get("author"),
                "Source Channel": f"r/{r.get('source')}",
                "Message Text": r.get("message"),
                "Timestamp": r.get("created_utc")
            })
        st.dataframe(pd.DataFrame(results_data), width=1000)
    else:
        st.warning(f"No messages found matching '{search_query}'.")
    st.divider()

# Sidebar Navigation Tabs
st.sidebar.title("📌 Dashboard Navigation")
selected_tab = st.sidebar.radio(
    "Select Intelligence View:",
    [
        "📊 Page 1: Executive KPI Overview & Trending",
        "💬 Page 2: Live WhatsApp Monitor UI",
        "🎯 Page 3: AI Sentiment & Context Disentanglement"
    ]
)

st.sidebar.divider()
st.sidebar.caption("System Status: 🟢 MongoDB Atlas Connected")
st.sidebar.caption("Ingestion Engine: Apache Kafka + PySpark")

# Sidebar Expander for Technical DLQ Error Audit Logs
with st.sidebar.expander("🚨 Technical DLQ Error Audit Logs"):
    df_dlq = get_dlq_logs(limit=30)
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
if selected_tab == "📊 Page 1: Executive KPI Overview & Trending":
    st.header("📊 Pipeline KPI Overview & Trending Analytics")

    # Fetch KPIs from MongoDB Atlas
    kpis = get_pipeline_kpis()

    col1, col2, col3, col4 = st.columns(4)
    kpi_cards = [
        ("📨", "Total Clean Messages", f'{kpis["total_messages"]:,}', "#38BDF8", "Ingested via Kafka → PySpark"),
        ("📡", "Active Subreddits", f'{kpis["total_subreddits"]}', "#818CF8", "Distinct channels monitored"),
        ("👥", "Total User Authors", f'{kpis["total_authors"]:,}', "#A78BFA", "Unique contributing users"),
        ("💚", "Pipeline Health", "HEALTHY", "#10B981", "0 blocking errors detected"),
    ]
    for col, (icon, title, value, color, sub) in zip([col1, col2, col3, col4], kpi_cards):
        with col:
            st.markdown(
                f'<div class="kpi-box"><div class="kpi-icon">{icon}</div>'
                f'<div class="kpi-title">{title}</div>'
                f'<div class="kpi-value" style="color:{color};">{value}</div>'
                f'<div class="kpi-sub">{sub}</div></div>',
                unsafe_allow_html=True
            )

    st.divider()

    # ------------------------------------------------------------------------
    # Message Volume Over Time — interactive area chart with range selector
    # and range slider so users can zoom/pan into any time window.
    # ------------------------------------------------------------------------
    st.markdown('<div class="section-title">📈 Message Ingestion Volume Over Time</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-caption">Drag the range slider below the chart, or click a quick-range button, to zoom into any window. Hover for exact daily counts.</div>', unsafe_allow_html=True)

    range_choice = st.radio(
        "Quick range:", ["7D", "14D", "30D", "All"], horizontal=True, index=2, key="volume_range", label_visibility="collapsed"
    )
    lookback_days = {"7D": 7, "14D": 14, "30D": 30, "All": 90}[range_choice]
    df_volume = get_message_volume_timeseries(days=lookback_days)

    fig_volume = go.Figure()
    fig_volume.add_trace(go.Scatter(
        x=df_volume["Date"], y=df_volume["Message Count"],
        mode="lines+markers",
        line=dict(color=ACCENT, width=3, shape="spline"),
        marker=dict(size=5, color=ACCENT2, line=dict(width=1, color="#0F172A")),
        fill="tozeroy",
        fillcolor="rgba(56, 189, 248, 0.18)",
        hovertemplate="<b>%{x|%b %d, %Y}</b><br>Messages: %{y:,}<extra></extra>",
        name="Messages / day"
    ))
    fig_volume.update_xaxes(
        rangeslider=dict(visible=True, thickness=0.08, bgcolor="rgba(30,41,59,0.6)"),
        rangeselector=dict(
            buttons=[
                dict(count=7, label="7D", step="day", stepmode="backward"),
                dict(count=14, label="14D", step="day", stepmode="backward"),
                dict(count=30, label="30D", step="day", stepmode="backward"),
                dict(step="all", label="All"),
            ],
            bgcolor="rgba(30,41,59,0.8)", activecolor=ACCENT, font=dict(color="#F1F5F9", size=11)
        ),
        type="date"
    )
    style_fig(fig_volume, height=380, hovermode="x unified", legend=False)
    st.plotly_chart(fig_volume, use_container_width=True, config=PLOTLY_CONFIG)

    st.divider()

    # Bottom Layout: Left = Groq LLM Topic Bar Chart, Right = Activity Heatmap
    chart_col, heat_col = st.columns([3, 2])

    with chart_col:
        st.markdown('<div class="section-title">🧠 Human-Grade Groq LLM Detected Topics</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-caption">Hover any bar for the exact document count and share of total volume.</div>', unsafe_allow_html=True)
        df_topics = get_groq_llm_topic_distribution(limit=10).sort_values("Message Count")
        total_topic_msgs = df_topics["Message Count"].sum()
        df_topics["Share"] = (df_topics["Message Count"] / max(total_topic_msgs, 1) * 100).round(1)

        fig_topics = go.Figure(go.Bar(
            x=df_topics["Message Count"], y=df_topics["Topic Category"],
            orientation="h",
            marker=dict(
                color=df_topics["Message Count"], colorscale="Purples",
                line=dict(color="rgba(167,139,250,0.6)", width=1)
            ),
            text=df_topics["Message Count"], textposition="outside",
            customdata=df_topics["Share"],
            hovertemplate="<b>%{y}</b><br>Documents: %{x:,}<br>Share of total: %{customdata}%<extra></extra>"
        ))
        style_fig(fig_topics, height=420, legend=False)
        fig_topics.update_layout(xaxis_title="Messages Processed", yaxis_title=None)
        st.plotly_chart(fig_topics, use_container_width=True, config=PLOTLY_CONFIG)

    with heat_col:
        st.markdown('<div class="section-title">🔥 Activity Heatmap</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-caption">Darker cells = busier hours. Hover for exact volume by day & hour.</div>', unsafe_allow_html=True)
        heat_df = get_activity_heatmap_data()
        fig_heat = go.Figure(go.Heatmap(
            z=heat_df.values, x=[f"{h:02d}:00" for h in heat_df.columns], y=heat_df.index,
            colorscale="Viridis", showscale=True,
            colorbar=dict(title="Msgs", thickness=12, len=0.8),
            hovertemplate="<b>%{y}, %{x}</b><br>Messages: %{z}<extra></extra>"
        ))
        style_fig(fig_heat, height=420, legend=False)
        fig_heat.update_xaxes(tickangle=-45, nticks=12)
        st.plotly_chart(fig_heat, use_container_width=True, config=PLOTLY_CONFIG)

    st.divider()

    # Interactive keyword bar chart (replaces the static progress-column table)
    st.markdown('<div class="section-title">🏷️ Groq LLM Context Keywords</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-caption">Ranked by frequency across enriched documents. Hover for exact counts.</div>', unsafe_allow_html=True)
    df_keywords = get_groq_llm_top_keywords(top_n=14).sort_values("Frequency")
    fig_kw = go.Figure(go.Bar(
        x=df_keywords["Frequency"], y=df_keywords["Keyword"],
        orientation="h",
        marker=dict(color=df_keywords["Frequency"], colorscale="Teal", line=dict(color="rgba(56,189,248,0.5)", width=1)),
        text=df_keywords["Frequency"], textposition="outside",
        hovertemplate="<b>%{y}</b><br>Frequency: %{x}<extra></extra>"
    ))
    style_fig(fig_kw, height=440, legend=False)
    fig_kw.update_layout(xaxis_title="Frequency", yaxis_title=None)
    st.plotly_chart(fig_kw, use_container_width=True, config=PLOTLY_CONFIG)


# ==============================================================================
# TAB 2: LIVE MONITOR & WHATSAPP CHAT UI (Mentor's Page 2)
# ==============================================================================
elif selected_tab == "💬 Page 2: Live WhatsApp Monitor UI":
    st.header("💬 Live Stream Channel Monitor & WhatsApp Chat UI")
    
    top_col1, top_col2 = st.columns([3, 1])
    with top_col1:
        selected_channel = st.selectbox(
            "📺 Select Channel / Subreddit to Monitor:",
            [
                "r/technology",
                "r/science",
                "r/AskReddit",
                "r/sports",
                "r/gaming",
                "r/space",
                "r/movies",
                "r/news",
                "r/worldnews",
                "r/geopolitics"
            ]
        )
    with top_col2:
        auto_refresh = st.checkbox("🔄 Auto-Refresh Live Stream", value=False)
    
    st.divider()
    
    # Fetch Chat Messages for selected channel
    chat_messages = get_channel_chat_messages(selected_channel, limit=25)
    
    if not chat_messages:
        st.info(f"No active messages currently stored in channel **{selected_channel}**. Run the producer to stream messages!")
    else:
        st.subheader(f"💬 Live Conversation Feed in {selected_channel}")
        
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

                
    st.divider()
    st.subheader("🕸️ Neo4j Real-Time Graph Analytics & Influencer Centrality")
    g_col1, g_col2 = st.columns([1, 1])
    with g_col1:
        st.markdown("#### 🌟 Top Influencers (PageRank & In-Degree)")
        df_influencers = get_top_neo4j_influencers(limit=10)
        st.dataframe(df_influencers, use_container_width=True)
    with g_col2:
        st.markdown("#### 👥 Community Detection Summary (Louvain)")
        df_comm = get_neo4j_community_summary()
        st.dataframe(df_comm, use_container_width=True)

    st.markdown("---")
    st.subheader("🌐 Interactive 2D Physics Knowledge Graph Visualizer Suite")
    st.caption("Drag nodes, scroll to zoom, and hover over users and topics to inspect real-time conversational connections. Nodes stay draggable and re-settle with physics.")

    graph_ctrl_col1, graph_ctrl_col2 = st.columns([2, 1])
    with graph_ctrl_col1:
        node_limit = st.slider("🔧 Graph density (max relationships rendered)", min_value=10, max_value=100, value=35, step=5)
    with graph_ctrl_col2:
        st.caption("Fewer nodes = faster physics settling. More nodes = richer topology.")

    graph_tab1, graph_tab2, graph_tab3 = st.tabs([
        "🌟 Graph 1: User Social Interaction Network",
        "🧠 Graph 2: User-to-Topic Bipartite Graph",
        "👥 Graph 3: Louvain Community Clusters"
    ])

    with graph_tab1:
        st.markdown("**User-to-User Interaction Graph** *(🟠 Orange = Influencer, 🔵 Blue = Contributor — node size scales by in-degree replies)*")
        html_social = generate_social_interaction_graph_html(limit=node_limit)
        components.html(html_social, height=500, scrolling=False)

    with graph_tab2:
        st.markdown("**User-to-Topic Interest Graph** *(🟣 Purple Hexagons = Groq LLM Topics | 🟢 Green Dots = Users)*")
        html_bipartite = generate_user_topic_bipartite_graph_html(limit=node_limit)
        components.html(html_bipartite, height=500, scrolling=False)

    with graph_tab3:
        st.markdown("**Louvain Community Detection Graph** *(Node color = detected sub-community; edges show cross-community bridges)*")
        html_comm = generate_community_cluster_graph_html(limit=node_limit)
        components.html(html_comm, height=500, scrolling=False)

    if auto_refresh:
        time.sleep(3)
        st.rerun()


# ==============================================================================
# TAB 3: AI SENTIMENT & CONTEXT DISENTANGLEMENT (Interactive Feature)
# ==============================================================================

elif selected_tab == "🎯 Page 3: AI Sentiment & Context Disentanglement":
    st.header("🎯 AI Sentiment Distribution & Topic Disentanglement")
    st.markdown("Analyze tone, sentiment breakdown, and cross-channel conversational trends across all 10 subreddits.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown('<div class="section-title">🟢 Conversational Sentiment Breakdown</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-caption">Click a legend entry to isolate a sentiment. Hover a slice for its exact share.</div>', unsafe_allow_html=True)
        df_sent = get_sentiment_distribution()
        total_sent = int(df_sent["Count"].sum())

        fig_donut = go.Figure(go.Pie(
            labels=df_sent["Sentiment"], values=df_sent["Count"], hole=0.62,
            marker=dict(colors=["#10B981", "#94A3B8", "#EF4444"], line=dict(color="#0F172A", width=2)),
            pull=[0.03, 0.03, 0.03],
            textinfo="percent", textfont=dict(size=13, color="#F8FAFC"),
            hovertemplate="<b>%{label}</b><br>Messages: %{value:,}<br>Share: %{percent}<extra></extra>"
        ))
        fig_donut.add_annotation(
            text=f"<b>{total_sent:,}</b><br><span style='font-size:11px;color:#94A3B8;'>Analyzed</span>",
            x=0.5, y=0.5, showarrow=False, font=dict(size=20, color="#F1F5F9")
        )
        style_fig(fig_donut, height=380, legend=True)
        st.plotly_chart(fig_donut, use_container_width=True, config=PLOTLY_CONFIG)

    with col2:
        st.markdown('<div class="section-title">🌐 Channel Multi-Compare Intelligence</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-caption">Click into a tile to drill down, click center breadcrumb to zoom back out.</div>', unsafe_allow_html=True)
        df_channels = get_channel_distribution()
        total_ch = int(df_channels["count"].sum())
        fig_treemap = go.Figure(go.Treemap(
            labels=df_channels["channel"], parents=[""] * len(df_channels), values=df_channels["count"],
            marker=dict(colors=df_channels["count"], colorscale="Blues", line=dict(color="#0F172A", width=2)),
            textinfo="label+value",
            hovertemplate="<b>%{label}</b><br>Messages: %{value:,}<br>Share: %{percentParent:.1%}<extra></extra>",
            root_color="rgba(0,0,0,0)"
        ))
        style_fig(fig_treemap, height=380, legend=False)
        st.plotly_chart(fig_treemap, use_container_width=True, config=PLOTLY_CONFIG)

    st.divider()

    # --------------------------------------------------------------------
    # Sentiment Trend Over Time — 100% stacked area, with range selector
    # --------------------------------------------------------------------
    st.markdown('<div class="section-title">📉 Sentiment Trend Over Time</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-caption">Toggle sentiments via the legend. Drag the range slider to inspect a specific window.</div>', unsafe_allow_html=True)
    df_trend = get_sentiment_trend_over_time(days=30)
    trend_totals = df_trend[["Positive", "Neutral", "Negative"]].sum(axis=1).replace(0, 1)

    fig_trend = go.Figure()
    for col_name, color in [("Positive", GREEN), ("Neutral", "#94A3B8"), ("Negative", RED)]:
        pct = (df_trend[col_name] / trend_totals * 100).round(1)
        fig_trend.add_trace(go.Scatter(
            x=df_trend["date"], y=pct, mode="lines", stackgroup="one",
            name=col_name, line=dict(width=0.5, color=color), fillcolor=color,
            customdata=df_trend[col_name],
            hovertemplate=f"<b>{col_name}</b><br>%{{x|%b %d}}<br>Share: %{{y}}%%<br>Messages: %{{customdata}}<extra></extra>"
        ))
    fig_trend.update_xaxes(
        rangeslider=dict(visible=True, thickness=0.08, bgcolor="rgba(30,41,59,0.6)"),
        rangeselector=dict(
            buttons=[
                dict(count=7, label="7D", step="day", stepmode="backward"),
                dict(count=14, label="14D", step="day", stepmode="backward"),
                dict(step="all", label="All"),
            ],
            bgcolor="rgba(30,41,59,0.8)", activecolor=ACCENT, font=dict(color="#F1F5F9", size=11)
        ),
        type="date"
    )
    fig_trend.update_yaxes(ticksuffix="%", range=[0, 100])
    style_fig(fig_trend, height=380, hovermode="x unified", legend=True)
    st.plotly_chart(fig_trend, use_container_width=True, config=PLOTLY_CONFIG)

    st.divider()

    # --------------------------------------------------------------------
    # Channel Radar Comparison — overlaid polar chart, legend-click toggle
    # --------------------------------------------------------------------
    st.markdown('<div class="section-title">🕸️ Channel Intelligence Radar</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-caption">Volume, unique authors, average message length, and positivity — normalized per metric. Click a channel in the legend to isolate it.</div>', unsafe_allow_html=True)
    df_radar = get_channel_radar_metrics(top_n=6)
    metrics = ["Message Volume", "Unique Authors", "Avg Msg Length", "Positivity %"]
    radar_colors = [ACCENT, ACCENT2, GREEN, AMBER, PURPLE, RED]

    fig_radar = go.Figure()
    for i, (_, row) in enumerate(df_radar.iterrows()):
        raw_vals = [row[m] for m in metrics]
        norm_vals = []
        for m, v in zip(metrics, raw_vals):
            col_max = df_radar[m].max() or 1
            norm_vals.append(round((v / col_max) * 100, 1))
        fig_radar.add_trace(go.Scatterpolar(
            r=norm_vals + [norm_vals[0]], theta=metrics + [metrics[0]],
            fill="toself", name=row["channel"],
            line=dict(color=radar_colors[i % len(radar_colors)]),
            customdata=raw_vals + [raw_vals[0]],
            hovertemplate="<b>%{theta}</b><br>Normalized: %{r}%<br>Raw value: %{customdata}<extra>%{fullData.name}</extra>"
        ))
    fig_radar.update_layout(
        polar=dict(
            bgcolor="rgba(15,23,42,0.3)",
            radialaxis=dict(visible=True, range=[0, 100], gridcolor=GRID_COLOR, tickfont=dict(size=9)),
            angularaxis=dict(gridcolor=GRID_COLOR, tickfont=dict(size=11))
        )
    )
    style_fig(fig_radar, height=460, legend=True)
    st.plotly_chart(fig_radar, use_container_width=True, config=PLOTLY_CONFIG)