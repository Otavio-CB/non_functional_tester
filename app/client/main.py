from time import sleep
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

BACKEND_URL = "http://localhost:8000"
POLLING_INTERVAL = 2
st.set_page_config(layout="wide")


def fetch_test_results():
    try:
        response = requests.get(f"{BACKEND_URL}/test-results", timeout=5)
        return response.json() if response.status_code == 200 else []
    except requests.exceptions.RequestException as e:
        st.error(f"Backend connection failed: {str(e)}")
        return []


def run_test(test_type, config):
    endpoint = f"{BACKEND_URL}/{test_type.lower()}-test"
    try:
        response = requests.post(endpoint, json=config, timeout=30)
        return response.json() if response.status_code == 200 else {"error": response.text}
    except requests.exceptions.RequestException as e:
        return {"error": f"Connection failed: {str(e)}"}


# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Test Configuration")
    test_type = st.radio("Test Type", ["Stress", "Performance"])

    if test_type == "Stress":
        config = {
            "target_url": st.text_input("Target URL", "https://example.com"),
            "requests": st.number_input("Total Requests", 10, 1000, 100),
            "concurrency": st.number_input("Concurrent Users", 1, 100, 10),
            "headers": {"User-Agent": "PerformanceTester/1.0"}
        }
    else:
        config = {
            "target_url": st.text_input("Target URL", "https://example.com"),
            "duration": st.number_input("Duration (seconds)", 10, 3600, 30),
            "concurrency": st.number_input("Concurrent Users", 1, 100, 10),
            "headers": {"User-Agent": "PerformanceTester/1.0"}
        }

    if st.button("🚀 Run Test"):
        with st.spinner(f"Starting {test_type} test..."):
            result = run_test(test_type, config)
            if "test_id" in result:
                st.session_state.last_test_id = result["test_id"]
                st.success(f"Test {result['test_id']} started!")
                st.session_state.polling = True
            else:
                st.error(result.get("error", "Unknown error"))

# Main Dashboard
st.title("📊 Performance Test Dashboard")

# Initialize polling
if "polling" not in st.session_state:
    st.session_state.polling = False

# Polling mechanism
if st.session_state.polling:
    with st.spinner("Waiting for test completion..."):
        while st.session_state.polling:
            tests = fetch_test_results()
            if tests and st.session_state.last_test_id in [t.get("test_id") for t in tests]:
                test_data = next((t for t in tests if t.get("test_id") == st.session_state.last_test_id), None)
                if test_data and test_data.get("status") == "completed":
                    st.session_state.polling = False
                    st.rerun()
            sleep(POLLING_INTERVAL)

# Display test results
tests = fetch_test_results()
if tests:
    # Prepare data for table
    df_data = []
    for test in tests:
        duration = (pd.to_datetime(test.get("end_time")) - pd.to_datetime(test.get("start_time"))).total_seconds()
        success_rate = test.get("successful_requests", 0) / test.get("total_requests", 1)  # Avoid division by zero
        df_data.append({
            "Test ID": test.get("test_id"),
            "Type": test.get("test_type"),
            "Status": test.get("status", "unknown"),
            "Start Time": test.get("start_time"),
            "Duration": f"{duration:.1f}s",
            "Requests": test.get("total_requests", 0),
            "Success Rate": f"{success_rate:.1%}",
            "RPS": f"{test.get('requests_per_second', 0):.1f}"
        })

    st.dataframe(pd.DataFrame(df_data), use_container_width=True)

    # Detailed view
    selected_test_id = st.selectbox(
        "Select test for details",
        [t["Test ID"] for t in df_data],
        index=0
    )

    test_data = next((t for t in tests if t.get("test_id") == selected_test_id), None)

    if test_data:
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
                fig.update_layout(yaxis_title="Time (ms)")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Response time data not available")

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
            else:
                st.warning("No request data available")

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
                else:
                    st.warning("Duration data invalid")
            else:
                st.warning("Throughput data not available")

            # Resource Usage
            st.subheader("🖥️ Resource Usage")
            if "resource_metrics" in test_data:
                # Create resource metrics dataframe
                resource_df = pd.DataFrame({
                    "Metric": ["CPU (%)", "Memory (MB)"],
                    "Max": [
                        test_data["resource_metrics"]["max_cpu"],
                        test_data["resource_metrics"]["max_memory"] / 1024
                    ],
                    "Average": [
                        test_data["resource_metrics"]["avg_cpu"],
                        test_data["resource_metrics"]["avg_memory"] / 1024
                    ]
                })

                # CPU Usage
                st.markdown("**CPU Usage**")
                fig_cpu = px.bar(
                    resource_df[resource_df["Metric"] == "CPU (%)"],
                    x="Metric",
                    y=["Max", "Average"],
                    barmode="group",
                    labels={"value": "Usage (%)"},
                    color_discrete_sequence=["#19D3F3", "#FF6692"]
                )
                st.plotly_chart(fig_cpu, use_container_width=True)

                # Memory Usage
                st.markdown("**Memory Usage**")
                fig_mem = px.bar(
                    resource_df[resource_df["Metric"] == "Memory (MB)"],
                    x="Metric",
                    y=["Max", "Average"],
                    barmode="group",
                    labels={"value": "Usage (MB)"},
                    color_discrete_sequence=["#B6E880", "#FF97FF"]
                )
                st.plotly_chart(fig_mem, use_container_width=True)
            else:
                st.warning("Resource metrics not available")

        # Raw JSON view
        with st.expander("📄 Raw Test Data"):
            st.json(test_data)
    else:
        st.error("Selected test data could not be loaded")
else:
    st.info("No test results available. Run a test to see data.")