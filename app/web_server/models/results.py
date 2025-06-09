from datetime import datetime
from typing import Optional, List, Dict

from pydantic import BaseModel


class TestResult(BaseModel):
    """Model representing the complete results of a performance or stress test"""
    test_id: str
    test_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    min_response_time: float
    max_response_time: float
    percentile_90: float
    requests_per_second: float
    status: str = "running"
    errors: Optional[List[str]] = None
    resource_stats: Optional[List[Dict]] = None
    resource_metrics: Optional[Dict] = None
