import asyncio
import logging
import statistics
import time
from datetime import datetime
from typing import List, Dict

import httpx
import psutil

from app.web_server.models.config import TestConfig
from app.web_server.models.results import TestResult

logger = logging.getLogger(__name__)


class BaseTester:
    """Base class for performance testers that provides common testing functionality"""

    def __init__(self, config: TestConfig):
        self.config = config
        self.test_id = f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.results: List[Dict] = []
        self.resource_stats: List[Dict] = []
        self.monitoring = True
        self.start_time = None
        self.end_time = None
        self.test_result = TestResult(test_id=self.test_id, test_type=self.__class__.__name__,
                                      start_time=datetime.now(), total_requests=0, successful_requests=0,
                                      failed_requests=0, average_response_time=0, min_response_time=0,
                                      max_response_time=0, percentile_90=0, requests_per_second=0, status="running",
                                      resource_stats=[], resource_metrics={})

    async def _make_request(self, client: httpx.AsyncClient):
        """Make an individual HTTP request to the target URL and record the results"""
        try:
            start = time.time()
            response = await client.get(self.config.target_url)
            elapsed = time.time() - start

            self.results.append(
                {"status_code": response.status_code, "response_time": elapsed, "success": response.is_success})
            return True, elapsed
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            self.results.append({"status_code": None, "response_time": None, "success": False, "error": str(e)})
            return False, 0

    async def _monitor_resources(self, interval: float = 1.0):
        """Background task to monitor system resources during the test"""
        while self.monitoring:
            stats = {'timestamp': datetime.now().isoformat(), 'cpu_percent': psutil.cpu_percent(),
                     'memory_percent': psutil.virtual_memory().percent,
                     'memory_used': psutil.virtual_memory().used / (1024 * 1024),  # in MB
                     'network_sent': psutil.net_io_counters().bytes_sent,
                     'network_recv': psutil.net_io_counters().bytes_recv, }
            self.resource_stats.append(stats)

            if self.resource_stats:
                self.test_result.resource_metrics = {'max_cpu': max(s['cpu_percent'] for s in self.resource_stats),
                                                     'avg_cpu': statistics.mean(
                                                         s['cpu_percent'] for s in self.resource_stats),
                                                     'max_memory': max(s['memory_used'] for s in self.resource_stats),
                                                     'avg_memory': statistics.mean(
                                                         s['memory_used'] for s in self.resource_stats), }
                self.test_result.resource_stats = self.resource_stats

            await asyncio.sleep(interval)

    def _calculate_metrics(self):
        """Calculate performance metrics from collected test results"""
        response_times = [r["response_time"] for r in self.results if r["success"]]
        successful = len(response_times)
        failed = len(self.results) - successful

        if successful > 0:
            avg_time = statistics.mean(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            percentile_90 = statistics.quantiles(response_times, n=100)[-1] if len(response_times) > 1 else \
                response_times[0]
        else:
            avg_time = min_time = max_time = percentile_90 = 0

        test_duration = (self.end_time - self.start_time).total_seconds()
        rps = len(self.results) / test_duration if test_duration > 0 else 0

        self.test_result.total_requests = len(self.results)
        self.test_result.successful_requests = successful
        self.test_result.failed_requests = failed
        self.test_result.average_response_time = avg_time
        self.test_result.min_response_time = min_time
        self.test_result.max_response_time = max_time
        self.test_result.percentile_90 = percentile_90
        self.test_result.requests_per_second = rps
        self.test_result.end_time = self.end_time
        self.test_result.status = "completed"

        if failed > 0:
            errors = [r.get("error", "Unknown error") for r in self.results if not r["success"]]
            self.test_result.errors = list(set(errors))[:10]
