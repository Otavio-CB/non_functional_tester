from typing import Dict, List, Optional

import requests


class APIClient:
    """Client for interacting with a performance testing API"""
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the APIClient with the base URL of the API"""
        self.base_url = base_url

    def fetch_test_results(self) -> List[Dict]:
        """Fetch all available test results from the API"""
        try:
            response = requests.get(f"{self.base_url}/test-results", timeout=5)
            if response.status_code == 200:
                return response.json()
            return []
        except requests.exceptions.RequestException:
            return []

    def fetch_resource_stats(self, test_id: str) -> Optional[Dict]:
        """Fetch resource statistics for a specific test"""
        try:
            response = requests.get(f"{self.base_url}/resource-stats/{test_id}", timeout=5)
            if response.status_code == 200:
                return response.json()
            return None
        except requests.exceptions.RequestException:
            return None

    def run_test(self, test_type: str, config: Dict) -> Dict:
        """Execute a new performance test"""
        endpoint = f"{self.base_url}/{test_type.lower()}-test"
        try:
            response = requests.post(endpoint, json=config, timeout=30)
            if response.status_code == 200:
                return response.json()
            return {"error": f"Backend error: {response.text}"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Connection failed: {str(e)}"}
