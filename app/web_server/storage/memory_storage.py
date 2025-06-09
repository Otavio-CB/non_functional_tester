from typing import Dict

from app.models.results import TestResult


class MemoryStorage:
    def __init__(self):
        self._storage: Dict[str, TestResult] = {}

    def save(self, test_id: str, result: TestResult):
        self._storage[test_id] = result

    def get(self, test_id: str) -> TestResult:
        return self._storage.get(test_id)

    def get_all(self) -> list[TestResult]:
        return list(self._storage.values())
