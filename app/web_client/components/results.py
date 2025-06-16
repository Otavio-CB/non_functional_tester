import pandas as pd
import plotly.express as px
import streamlit as st


def display_test_results(test_data: dict):
    """Display detailed test results"""
    tab1, tab2 = st.tabs(["📊 Performance Metrics", "📈 Resource Usage"])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            display_response_times(test_data)
            display_success_rate(test_data)

        with col2:
            display_throughput(test_data)

    with tab2:
        display_resource_usage(test_data)


def display_response_times(test_data: dict):
    """Display response times metrics"""
    st.subheader("⏱ Response Times (ms)")
    if all(k in test_data for k in
           ["min_response_time", "average_response_time", "max_response_time", "percentile_90"]):
        fig = px.bar(x=["Min", "Avg", "Max", "90th %"],
            y=[test_data["min_response_time"] * 1000, test_data["average_response_time"] * 1000,
               test_data["max_response_time"] * 1000, test_data["percentile_90"] * 1000],
            labels={"x": "Metric", "y": "Milliseconds"}, color_discrete_sequence=["#636EFA"])
        st.plotly_chart(fig, use_container_width=True)


def display_success_rate(test_data: dict):
    """Display success/failure rate"""
    st.subheader("✅ Success Rate")
    successful = test_data.get("successful_requests", 0)
    failed = test_data.get("failed_requests", 0)
    if successful + failed > 0:
        fig = px.pie(names=["Success", "Failed"], values=[successful, failed],
            color_discrete_sequence=["#00CC96", "#EF553B"])
        st.plotly_chart(fig, use_container_width=True)


def display_throughput(test_data: dict):
    """Display throughput metrics"""
    st.subheader("📈 Requests Per Second")
    if "requests_per_second" in test_data:
        duration = (pd.to_datetime(test_data["end_time"]) - pd.to_datetime(test_data["start_time"])).total_seconds()
        if duration > 0:
            total_requests = test_data.get("total_requests", 0)
            avg_rps = total_requests / duration
            fig = px.bar(x=["Measured", "Average"], y=[test_data["requests_per_second"], avg_rps],
                labels={"x": "Metric", "y": "Requests/Second"}, color_discrete_sequence=["#AB63FA", "#FFA15A"])
            st.plotly_chart(fig, use_container_width=True)


def display_resource_usage(test_data: dict):
    """Display resource usage metrics"""
    if test_data.get("resource_stats"):
        st.subheader("🖥️ Resource Usage Over Time")

        resource_df = pd.DataFrame(test_data["resource_stats"])
        resource_df['timestamp'] = pd.to_datetime(resource_df['timestamp'])

        fig_resources = px.line(resource_df, x='timestamp', y=['cpu_percent', 'memory_percent'],
            title='CPU and Memory Usage', labels={'value': 'Usage (%)', 'variable': 'Resource'},
            color_discrete_sequence=['#636EFA', '#EF553B'])
        st.plotly_chart(fig_resources, use_container_width=True)

        fig_network = px.line(resource_df, x='timestamp', y=['network_sent', 'network_recv'], title='Network Traffic',
            labels={'value': 'Bytes', 'variable': 'Direction'}, color_discrete_sequence=['#00CC96', '#AB63FA'])
        st.plotly_chart(fig_network, use_container_width=True)

        if test_data.get("resource_metrics"):
            st.subheader("📌 Resource Usage Summary")
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Max CPU Usage", f"{test_data['resource_metrics']['max_cpu']:.1f}%")
                st.metric("Avg CPU Usage", f"{test_data['resource_metrics']['avg_cpu']:.1f}%")

            with col2:
                st.metric("Max Memory Used", f"{test_data['resource_metrics']['max_memory']:.1f} MB")
                st.metric("Avg Memory Used", f"{test_data['resource_metrics']['avg_memory']:.1f} MB")
