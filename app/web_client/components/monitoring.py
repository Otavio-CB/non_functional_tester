from typing import Dict

import pandas as pd
import plotly.express as px
import streamlit as st


def init_monitoring_placeholders():
    """Initialize placeholders for monitoring components"""
    if 'monitoring_placeholders' not in st.session_state:
        st.session_state.monitoring_placeholders = {'title': st.empty(), 'metrics': st.empty(),
            'cpu_mem_chart': st.empty(), 'network_chart': st.empty()}


def display_realtime_metrics(stats: Dict):
    """Display the real-time metrics"""
    last_stat = stats[-1]
    with st.session_state.monitoring_placeholders['metrics']:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("CPU Usage", f"{last_stat['cpu_percent']}%")
        col2.metric("Memory Used", f"{last_stat['memory_used']:.2f} MB")
        col3.metric("Memory %", f"{last_stat['memory_percent']}%")
        col4.metric("Network", f"↑{last_stat['network_sent'] / 1024:.1f} KB ↓{last_stat['network_recv'] / 1024:.1f} KB")


def display_realtime_charts(stats: Dict):
    """Display the real-time charts"""
    df = pd.DataFrame(stats)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    with st.session_state.monitoring_placeholders['cpu_mem_chart']:
        fig_resources = px.line(df, x='timestamp', y=['cpu_percent', 'memory_percent'],
            title='CPU and Memory Usage Over Time', labels={'value': 'Usage (%)', 'variable': 'Resource'},
            color_discrete_map={'cpu_percent': '#636EFA', 'memory_percent': '#EF553B'})
        st.plotly_chart(fig_resources, use_container_width=True)

    with st.session_state.monitoring_placeholders['network_chart']:
        fig_network = px.line(df, x='timestamp', y=['network_sent', 'network_recv'], title='Network Traffic Over Time',
            labels={'value': 'Bytes', 'variable': 'Direction'}, color_discrete_sequence=['#00CC96', '#AB63FA'])
        st.plotly_chart(fig_network, use_container_width=True)


def display_realtime_monitoring(test_id: str, api_client) -> bool:
    """Display real-time monitoring dashboard"""
    stats_data = api_client.fetch_resource_stats(test_id)
    if not stats_data:
        st.warning("Waiting for monitoring data...")
        return False

    stats = stats_data.get("resource_stats", [])
    if not stats:
        st.warning("No monitoring data available yet...")
        return False

    init_monitoring_placeholders()

    with st.session_state.monitoring_placeholders['title']:
        st.subheader("📊 Realtime Resource Monitoring")

    display_realtime_metrics(stats)
    display_realtime_charts(stats)

    return True
