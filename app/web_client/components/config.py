import streamlit as st


def get_test_config() -> dict:
    """Render the test configuration form based on test type"""
    st.header("⚙️ Test Configuration")
    test_type = st.radio("Test Type", ["Stress", "Performance"])

    if test_type == "Stress":
        return {"test_type": test_type, "config": {"target_url": st.text_input("Target URL", "https://example.com"),
            "requests": st.number_input("Total Requests", min_value=1, step=1, value=100),
            "concurrency": st.number_input("Concurrent Users", min_value=1, step=1, value=10),
            "headers": {"User-Agent": "PerformanceTester/1.0"}}}
    else:
        return {"test_type": test_type, "config": {"target_url": st.text_input("Target URL", "https://example.com"),
            "duration": st.number_input("Duration (seconds)", min_value=1, step=1, value=30),
            "concurrency": st.number_input("Concurrent Users", min_value=1, step=1, value=10),
            "headers": {"User-Agent": "PerformanceTester/1.0"}}}
