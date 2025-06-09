import asyncio
from datetime import datetime

import httpx

from app.core.base_tester import BaseTester


class StressTester(BaseTester):
    async def run(self):
        self.start_time = datetime.now()

        async with httpx.AsyncClient() as client:
            tasks = []
            for _ in range(self.config.requests):
                tasks.append(self._make_request(client))
                if len(tasks) >= self.config.concurrency:
                    await asyncio.gather(*tasks)
                    tasks = []

            if tasks:
                await asyncio.gather(*tasks)

        self.end_time = datetime.now()
        self._calculate_metrics()
        return self.test_result
