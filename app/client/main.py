from time import sleep
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from datetime import datetime

BACKEND_URL = "http://localhost:8000"
POLLING_INTERVAL = 1  # seconds
st.set_page_config(layout="wide")


def fetch_test_results():
    try:
        response = requests.get(f"{BACKEND_URL}/test-results", timeout=5)
        if response.status_code == 200:
            return response.json()
        st.error(f"Backend returned status {response.status_code}")
        return []
    except requests.exceptions.RequestException as e:
        st.error(f"Backend connection failed: {str(e)}")
        return []


def fetch_resource_stats(test_id: str):
    try:
        response = requests.get(f"{BACKEND_URL}/resource-stats/{test_id}", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching resource stats: {str(e)}")
        return None


def run_test(test_type, config):
    endpoint = f"{BACKEND_URL}/{test_type.lower()}-test"
    try:
        response = requests.post(endpoint, json=config, timeout=30)
        if response.status_code == 200:
            return response.json()
        return {"error": f"Backend error: {response.text}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Connection failed: {str(e)}"}


def display_realtime_monitoring(test_id: str, placeholder=None):
    """Display real-time monitoring charts and metrics"""
    stats_data = fetch_resource_stats(test_id)
    if not stats_data:
        if placeholder:
            placeholder.warning("Waiting for monitoring data...")
        return False

    stats = stats_data.get("resource_stats", [])
    if not stats:
        if placeholder:
            placeholder.warning("No monitoring data available yet...")
        return False

    # Create a container for the metrics if no placeholder provided
    container = placeholder or st.container()

    with container:
        st.subheader("📊 Realtime Resource Monitoring")

        # Display current metrics
        last_stat = stats[-1]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("CPU Usage", f"{last_stat['cpu_percent']}%")
        col2.metric("Memory Used", f"{last_stat['memory_used']:.2f} MB")
        col3.metric("Memory %", f"{last_stat['memory_percent']}%")
        col4.metric("Network",
                    f"↑{last_stat['network_sent'] / 1024:.1f} KB ↓{last_stat['network_recv'] / 1024:.1f} KB")

        # Convert to DataFrame for plotting
        df = pd.DataFrame(stats)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # CPU and Memory Chart
        fig_resources = px.line(
            df, x='timestamp', y=['cpu_percent', 'memory_percent'],
            title='CPU and Memory Usage Over Time',
            labels={'value': 'Usage (%)', 'variable': 'Resource'},
            color_discrete_map={'cpu_percent': '#636EFA', 'memory_percent': '#EF553B'}
        )
        st.plotly_chart(fig_resources, use_container_width=True)

        # Network Chart
        fig_network = px.line(
            df, x='timestamp', y=['network_sent', 'network_recv'],
            title='Network Traffic Over Time',
            labels={'value': 'Bytes', 'variable': 'Direction'},
            color_discrete_sequence=['#00CC96', '#AB63FA']
        )
        st.plotly_chart(fig_network, use_container_width=True)

    return True


# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Test Configuration")
    test_type = st.radio("Test Type", ["Stress", "Performance"])

    if test_type == "Stress":
        config = {
            "target_url": st.text_input("Target URL", "https://example.com"),
            "requests": st.number_input("Total Requests"),
            "concurrency": st.number_input("Concurrent Users"),
            "headers": {"User-Agent": "PerformanceTester/1.0"}
        }
    else:
        config = {
            "target_url": st.text_input("Target URL", "https://example.com"),
            "duration": st.number_input("Duration (seconds)", 10, 3600, 30),
            "concurrency": st.number_input("Concurrent Users", 1, 500, 10),
            "headers": {"User-Agent": "PerformanceTester/1.0"}
        }

    if st.button("🚀 Run Test"):
        with st.spinner(f"Starting {test_type} test..."):
            result = run_test(test_type, config)
            if "test_id" in result:
                st.session_state.active_test_id = result["test_id"]
                st.session_state.test_start_time = datetime.now()
                st.success(f"Test {result['test_id']} started!")
            else:
                st.error(result.get("error", "Unknown error"))

# Main Dashboard
st.title("📊 Performance Test Dashboard")

# Initialize session state for active test
if "active_test_id" not in st.session_state:
    st.session_state.active_test_id = None

# Real-time monitoring section
if st.session_state.get("active_test_id"):
    # Create a dedicated container for real-time monitoring
    monitoring_placeholder = st.empty()

    # Check if test is still running
    test_data = next((t for t in fetch_test_results()
                      if t.get("test_id") == st.session_state.active_test_id), None)

    if test_data and test_data.get("status") == "completed":
        st.session_state.active_test_id = None
        st.rerun()
    else:
        # Display real-time monitoring
        if display_realtime_monitoring(st.session_state.active_test_id, monitoring_placeholder):
            # Auto-refresh the monitoring data
            sleep(POLLING_INTERVAL)
            st.rerun()

# Display historical test results
tests = fetch_test_results()
if tests:
    # Prepare data for the results table
    df_data = []
    for test in tests:
        duration = (pd.to_datetime(test.get("end_time")) - pd.to_datetime(
            test.get("start_time"))).total_seconds() if test.get("end_time") else 0
        total_requests = test.get("total_requests", 0)
        success_rate = test.get("successful_requests", 0) / total_requests if total_requests > 0 else 0

        df_data.append({
            "Test ID": test.get("test_id"),
            "Type": test.get("test_type"),
            "Status": test.get("status", "unknown"),
            "Start Time": test.get("start_time"),
            "Duration": f"{duration:.1f}s",
            "Requests": total_requests,
            "Success Rate": f"{success_rate:.1%}",
            "RPS": f"{test.get('requests_per_second', 0):.1f}"
        })

    st.dataframe(pd.DataFrame(df_data), use_container_width=True)

    # Test details section
    selected_test_id = st.selectbox(
        "Select test for details",
        [t["Test ID"] for t in df_data],
        index=0
    )

    test_data = next((t for t in tests if t.get("test_id") == selected_test_id), None)

    if test_data:
        # Create tabs for different views
        tab1, tab2 = st.tabs(["📊 Performance Metrics", "📈 Resource Usage"])

        with tab1:
            col1, col2 = st.columns(2)

            with col1:
                # Response Times
                st.subheader("⏱ Response Times (ms)")
                if all(k in test_data for k in
                       ["min_response_time", "average_response_time", "max_response_time", "percentile_90"]):
                    fig = px.bar(
                        x=["Min", "Avg", "Max", "90th %"],
                        y=[
                            test_data["min_response_time"] * 1000,
                            test_data["average_response_time"] * 1000,
                            test_data["max_response_time"] * 1000,
                            test_data["percentile_90"] * 1000
                        ],
                        labels={"x": "Metric", "y": "Milliseconds"},
                        color_discrete_sequence=["#636EFA"]
                    )
                    st.plotly_chart(fig, use_container_width=True)

                # Success/Failure Rate
                st.subheader("✅ Success Rate")
                successful = test_data.get("successful_requests", 0)
                failed = test_data.get("failed_requests", 0)
                if successful + failed > 0:
                    fig = px.pie(
                        names=["Success", "Failed"],
                        values=[successful, failed],
                        color_discrete_sequence=["#00CC96", "#EF553B"]
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Throughput
                st.subheader("📈 Requests Per Second")
                if "requests_per_second" in test_data:
                    duration = (pd.to_datetime(test_data["end_time"]) - pd.to_datetime(
                        test_data["start_time"])).total_seconds()
                    if duration > 0:
                        total_requests = test_data.get("total_requests", 0)
                        avg_rps = total_requests / duration
                        fig = px.bar(
                            x=["Measured", "Average"],
                            y=[test_data["requests_per_second"], avg_rps],
                            labels={"x": "Metric", "y": "Requests/Second"},
                            color_discrete_sequence=["#AB63FA", "#FFA15A"]
                        )
                        st.plotly_chart(fig, use_container_width=True)

        with tab2:
            # Resource Usage Analysis
            if test_data.get("resource_stats"):
                st.subheader("🖥️ Resource Usage Over Time")

                # Convert resource stats to DataFrame
                resource_df = pd.DataFrame(test_data["resource_stats"])
                resource_df['timestamp'] = pd.to_datetime(resource_df['timestamp'])

                # CPU and Memory Usage
                fig_resources = px.line(
                    resource_df,
                    x='timestamp',
                    y=['cpu_percent', 'memory_percent'],
                    title='CPU and Memory Usage',
                    labels={'value': 'Usage (%)', 'variable': 'Resource'},
                    color_discrete_sequence=['#636EFA', '#EF553B']
                )
                st.plotly_chart(fig_resources, use_container_width=True)

                # Network Usage
                fig_network = px.line(
                    resource_df,
                    x='timestamp',
                    y=['network_sent', 'network_recv'],
                    title='Network Traffic',
                    labels={'value': 'Bytes', 'variable': 'Direction'},
                    color_discrete_sequence=['#00CC96', '#AB63FA']
                )
                st.plotly_chart(fig_network, use_container_width=True)

                # Summary Metrics
                if test_data.get("resource_metrics"):
                    st.subheader("📌 Resource Usage Summary")
                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric("Max CPU Usage", f"{test_data['resource_metrics']['max_cpu']:.1f}%")
                        st.metric("Avg CPU Usage", f"{test_data['resource_metrics']['avg_cpu']:.1f}%")

                    with col2:
                        st.metric("Max Memory Used", f"{test_data['resource_metrics']['max_memory']:.1f} MB")
                        st.metric("Avg Memory Used", f"{test_data['resource_metrics']['avg_memory']:.1f} MB")

        # Raw JSON view
        with st.expander("📄 Raw Test Data"):
            st.json(test_data)
else:
    st.info("No test results available. Run a test to see data.")