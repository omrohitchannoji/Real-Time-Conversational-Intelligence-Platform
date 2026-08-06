import sys
import os

# Auto-resolve project root so `from dashboard.analytics import ...` works anywhere
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import plotly.express as px
import pandas as pd

from dashboard.style import inject_style, kpi_box
from dashboard.sidebar import render_sidebar_status
from dashboard.analytics import (
    get_pipeline_kpis,
    get_dataset_overview_stats,
    get_channel_distribution,
    get_top_keywords,
    search_messages,
    get_dataset_preview,
)

st.set_page_config(
    page_title="Conversational Context Intelligence Platform",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_style()

st.markdown('<div class="main-title">🚀 Real-Time Conversational Context & Intelligence Platform</div>',
            unsafe_allow_html=True)
st.markdown('<div class="sub-title">Distributed Event-Driven Ingestion Engine & Social Topology Analytics Dashboard</div>',
            unsafe_allow_html=True)

# ------------------------------------------------------------
# UNIVERSAL SEARCH
# ------------------------------------------------------------
search_query = st.text_input(
    "🔍 Universal Search (messages, authors, or subreddits in MongoDB Atlas):",
    placeholder="Type a keyword, username, or comment ID...",
    key="global_search_input",
)

if search_query and search_query.strip():
    st.info(f"🔍 Search Results for: **'{search_query}'**")
    search_results = search_messages(search_query, limit=30)
    if search_results:
        results_data = [{
            "Comment ID": r.get("comment_id"),
            "Author": r.get("author"),
            "Source Channel": f"r/{r.get('source')}",
            "Message Text": r.get("message"),
            "Timestamp": r.get("created_utc"),
        } for r in search_results]
        st.dataframe(pd.DataFrame(results_data), width="stretch")
    else:
        st.warning(f"No messages found matching '{search_query}'.")
    st.divider()

# ------------------------------------------------------------
# KPI OVERVIEW (merged from both old dashboard versions)
# ------------------------------------------------------------
st.subheader("📊 System Overview")

kpis = get_pipeline_kpis()
overview = get_dataset_overview_stats()

c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    kpi_box("Total Messages", f'{kpis["total_messages"]:,}')
with c2:
    kpi_box("Threads", f'{overview["total_threads"]:,}' if overview["total_threads"] else "N/A")
with c3:
    kpi_box("Total Authors", f'{kpis["total_authors"]:,}')
with c4:
    kpi_box("Active Subreddits", kpis["total_subreddits"])
with c5:
    kpi_box("Avg. Message Score", overview["avg_score"])
with c6:
    kpi_box("Pipeline Health", "HEALTHY", value_color="#10B981")

st.caption(f"Latest data year: **{overview['latest_year']}**  |  "
           f"DLQ errors so far: **{kpis['dlq_errors']}** (see the DLQ Audit page for details)")

st.divider()

# ------------------------------------------------------------
# TRENDING CHANNELS + TOP KEYWORDS
# ------------------------------------------------------------
chart_col, keywords_col = st.columns([3, 2])

with chart_col:
    st.subheader("🔥 Trending Channels (Message Volume by Subreddit)")
    df_channel = get_channel_distribution()
    fig = px.bar(
        df_channel, x="count", y="channel", orientation="h", color="count",
        color_continuous_scale="Viridis",
        labels={"count": "Total Messages", "channel": "Subreddit Channel"},
        text="count",
    )
    fig.update_layout(template="plotly_dark", height=420,
                       margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig, width="stretch")

with keywords_col:
    st.subheader("🏷️ Top Extracted Keywords")
    df_keywords = get_top_keywords(top_n=12)
    max_freq = int(df_keywords["Frequency"].max()) if not df_keywords.empty else 10
    st.dataframe(
        df_keywords,
        column_config={
            "Keyword": "Extracted Keyword",
            "Frequency": st.column_config.ProgressColumn(
                "Frequency", format="%d", min_value=0, max_value=max(max_freq, 1)),
        },
        width="stretch", height=420,
    )

st.divider()

# ------------------------------------------------------------
# RAW DATA PREVIEW (bounded sample - see utils/load_data.py note)
# ------------------------------------------------------------
st.subheader("🔎 Dataset Preview (sample of 200 rows)")
st.dataframe(get_dataset_preview(limit=200), width="stretch")

render_sidebar_status()
