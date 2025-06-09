import time
from datetime import datetime

import pandas as pd
import streamlit as st

from app.web_client.api.client import APIClient
from app.web_client.components.config import get_test_config
from app.web_client.components.monitoring import display_realtime_monitoring
from app.web_client.components.results import display_test_results

POLLING_INTERVAL = 1
st.set_page_config(layout="wide")


def main():
    api_client = APIClient()

    with st.sidebar:
        config_data = get_test_config()
        if st.button("🚀 Run Test"):
            with st.spinner(f"Starting {config_data['test_type']} test..."):
                result = api_client.run_test(config_data['test_type'], config_data['config'])
                if "test_id" in result:
                    st.session_state.active_test_id = result["test_id"]
                    st.session_state.test_start_time = datetime.now()
                    st.success(f"Test {result['test_id']} started!")
                else:
                    st.error(result.get("error", "Unknown error"))

    st.title("📊 Performance Test Dashboard")

    if st.session_state.get("active_test_id"):
        handle_active_test(api_client)

    display_historical_results(api_client)


def handle_active_test(api_client):
    """Handle display and state for active tests"""
    test_data = next(
        (t for t in api_client.fetch_test_results() if t.get("test_id") == st.session_state.active_test_id), None)

    if test_data and test_data.get("status") == "completed":
        cleanup_completed_test()
        st.rerun()
    else:
        if display_realtime_monitoring(st.session_state.active_test_id, api_client):
            time.sleep(POLLING_INTERVAL)
            st.rerun()


def cleanup_completed_test():
    """Cleanup session state after test completion"""
    st.session_state.active_test_id = None
    if 'monitoring_placeholders' in st.session_state:
        del st.session_state.monitoring_placeholders


def display_historical_results(api_client):
    """Display historical test results"""
    tests = api_client.fetch_test_results()
    if not tests:
        st.info("No test results available. Run a test to see data.")
        return

    df = prepare_results_dataframe(tests)
    st.dataframe(df, use_container_width=True)

    selected_test_id = st.selectbox("Select test for details", df["Test ID"], index=0)
    test_data = next(t for t in tests if t.get("test_id") == selected_test_id)
    display_test_results(test_data)


def prepare_results_dataframe(tests):
    """Prepare dataframe with test results summary"""
    df_data = []
    for test in tests:
        duration = (pd.to_datetime(test.get("end_time")) - pd.to_datetime(
            test.get("start_time"))).total_seconds() if test.get("end_time") else 0
        total_requests = test.get("total_requests", 0)
        success_rate = test.get("successful_requests", 0) / total_requests if total_requests > 0 else 0

        df_data.append(
            {"Test ID": test.get("test_id"), "Type": test.get("test_type"), "Status": test.get("status", "unknown"),
                "Start Time": test.get("start_time"), "Duration": f"{duration:.1f}s", "Requests": total_requests,
                "Success Rate": f"{success_rate:.1%}",

                "RPS": f"{test.get('requests_per_second', 0):.1f}"})
    return pd.DataFrame(df_data)


if __name__ == "__main__":
    main()
