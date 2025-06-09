import time
from datetime import datetime

import asyncio
import httpx

from app.core.base_tester import BaseTester


class PerformanceTester(BaseTester):
    async def run(self):
        if not self.config.duration:
            raise ValueError("Duration is required for performance testing")

        self.start_time = datetime.now()
        end_time = self.start_time.timestamp() + self.config.duration

        async with httpx.AsyncClient() as client:
            while time.time() < end_time:
                tasks = [self._make_request(client) for _ in range(self.config.concurrency)]
                await asyncio.gather(*tasks)

        self.end_time = datetime.now()
        self._calculate_metrics()
        return self.test_result
