import asyncio

from fastapi import FastAPI, BackgroundTasks

from app.web_server.core.performance_tester import PerformanceTester
from app.web_server.core.stress_tester import StressTester
from app.web_server.models.config import TestConfig
from app.web_server.storage.memory_storage import MemoryStorage

app = FastAPI()
storage = MemoryStorage()


async def _run_tester(tester):
    """Common function to run tests and monitor resources."""
    monitor_task = asyncio.create_task(tester.monitor_resources())
    result = await tester.run()
    tester.monitoring = False
    await monitor_task
    return result


def _setup_test(tester, background_tasks: BackgroundTasks):
    """Common setup for both test types."""
    test_id = tester.test_id
    storage.save(test_id, tester.test_result)

    async def run_and_save():
        result = await _run_tester(tester)
        storage.save(test_id, result)

    background_tasks.add_task(run_and_save)
    return tester.test_result


@app.post("/stress-test")
async def run_stress_test(config: TestConfig, background_tasks: BackgroundTasks):
    tester = StressTester(config)
    return _setup_test(tester, background_tasks)


@app.post("/performance-test")
async def run_performance_test(config: TestConfig, background_tasks: BackgroundTasks):
    tester = PerformanceTester(config)
    return _setup_test(tester, background_tasks)


@app.get("/test-results/{test_id}")
async def get_test_result(test_id: str):
    return storage.get(test_id) or {"error": "Test not found"}


@app.get("/test-results")
async def list_test_results():
    return storage.get_all()


@app.get("/resource-stats/{test_id}")
async def get_resource_stats(test_id: str):
    test_result = storage.get(test_id)
    if not test_result:
        return {"error": "Test not found"}

    return {"resource_stats": test_result.resource_stats if test_result.resource_stats else [],
            "resource_metrics": test_result.resource_metrics if test_result.resource_metrics else {}}
