from typing import Optional, Dict

from pydantic import BaseModel


class TestConfig(BaseModel):
    target_url: str
    requests: int = 100
    concurrency: int = 10
    duration: Optional[int] = None
    headers: Optional[Dict] = None
    payload: Optional[Dict] = None
