from typing import Dict

from app.web_server.models.results import TestResult


class MemoryStorage:
    """In-memory storage for test results using a dictionary-based implementation"""
    def __init__(self):
        """Initialize the memory storage with an empty dictionary"""
        self._storage: Dict[str, TestResult] = {}

    def save(self, test_id: str, result: TestResult):
        """Store a test result in memory"""
        self._storage[test_id] = result

    def get(self, test_id: str) -> TestResult:
        """Retrieve a test result by its ID"""
        return self._storage.get(test_id)

    def get_all(self) -> list[TestResult]:
        """Get all stored test results"""
        return list(self._storage.values())
