import sys
import os

# Auto-resolve project root directory in sys.path so 'from dashboard.analytics' works anywhere
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
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
    get_dlq_logs
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
    with col1:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">Total Clean Messages</div><div class="kpi-value">{kpis["total_messages"]:,}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">Active Subreddits</div><div class="kpi-value">{kpis["total_subreddits"]}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">Total User Authors</div><div class="kpi-value">{kpis["total_authors"]:,}</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">Pipeline Health</div><div class="kpi-value" style="color:#10B981;">HEALTHY</div></div>', unsafe_allow_html=True)
    
    st.divider()
    
    # Bottom Layout: Left Column = Subreddit Bar Chart, Right Column = Keywords Table
    chart_col, keywords_col = st.columns([3, 2])
    
    with chart_col:
        st.subheader("🔥 Trending Channels (Message Volume by Subreddit)")
        df_channel = get_channel_distribution()
        fig = px.bar(
            df_channel,
            x="count",
            y="channel",
            orientation="h",
            color="count",
            color_continuous_scale="Viridis",
            labels={"count": "Total Messages", "channel": "Subreddit Channel"},
            text="count"
        )
        fig.update_layout(
            template="plotly_dark",
            height=420,
            xaxis_title="Message Count",
            yaxis_title="Subreddit Channel",
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig, width=500)
        
    with keywords_col:
        st.subheader("🏷️ Top Extracted Keywords")
        df_keywords = get_top_keywords(top_n=12)
        max_freq = int(df_keywords["Frequency"].max()) if not df_keywords.empty else 10
        st.dataframe(
            df_keywords,
            column_config={
                "Keyword": "Extracted Keyword",
                "Frequency": st.column_config.ProgressColumn("Frequency", format="%d", min_value=0, max_value=max(max_freq, 1))
            },
            width=400,
            height=420
        )

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
            
            # Left side (Received reply) vs Right side (Sent / Primary post)
            is_reply = bool(parent_id and parent_id != "t3_none" and str(parent_id).strip() != "")
            
            if is_reply:
                # Left-aligned Received Chat Bubble
                st.markdown(f"""
                <div class="chat-bubble-received">
                    <strong>👤 {author}</strong> <span style="font-size:0.75rem; color:#38BDF8;">(Received Reply to #{parent_id})</span><br>
                    <span style="font-size: 1.05rem;">{text}</span>
                    <div class="chat-meta">🕒 {timestamp} | 🔑 Comment ID: {comment_id}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Right-aligned Sent Chat Bubble
                st.markdown(f"""
                <div class="chat-bubble-sent">
                    <strong>👤 {author}</strong> <span style="font-size:0.75rem; color:#10B981;">(Primary Thread Starter)</span><br>
                    <span style="font-size: 1.05rem;">{text}</span>
                    <div class="chat-meta">🕒 {timestamp} | 🔑 Comment ID: {comment_id}</div>
                </div>
                """, unsafe_allow_html=True)
                
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
