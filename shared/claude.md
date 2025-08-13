# Python Development Rules

## Core Principles

- Type hints required (PEP 484)
- No mutable default arguments
- Dependency injection over hard-coding
- Context managers for resource management
- Async for I/O operations
- Protocol-based interfaces over inheritance

## Module Organization

```python
"""Module docstring describing purpose and usage."""
from __future__ import annotations

# Standard library imports
import asyncio
import logging
from datetime import datetime
from typing import Any, Protocol, TypeVar

# Third-party imports
from pydantic import BaseSettings, Field

# Local imports
from .base import BaseProcessor
from .types import ProcessingResult

# Type definitions
T = TypeVar('T')

# Module-level configuration
logger = logging.getLogger(__name__)
```

## Class Design Patterns

### Dataclass Configuration

```python
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass(frozen=True)
class Config:
    """Immutable configuration using dataclass."""
    timeout: int = 30
    retries: int = 3
    debug: bool = False

    def __post_init__(self) -> None:
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
```

### Protocol-Based Interfaces

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Repository(Protocol):
    def get(self, id: str) -> Any: ...
    def save(self, entity: Any) -> str: ...
    def delete(self, id: str) -> bool: ...

class Service:
    def __init__(self, repository: Repository, config: Config) -> None:
        self._repo = repository
        self._config = config
```

## Error Handling

### Custom Exceptions with Context

```python
from datetime import datetime

class ProcessingError(Exception):
    def __init__(self, message: str, code: str, context: dict[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.context = context or {}
        self.timestamp = datetime.utcnow()
```

### Result Type Pattern

```python
from dataclasses import dataclass
from typing import Generic, TypeVar, Callable

T = TypeVar('T')
E = TypeVar('E')

@dataclass(frozen=True)
class Result(Generic[T, E]):
    """Result monad for error handling without exceptions."""
    value: T | None = None
    error: E | None = None

    @property
    def is_ok(self) -> bool:
        return self.error is None

    def map(self, func: Callable[[T], T]) -> Result[T, E]:
        if self.is_ok:
            try:
                return Result(value=func(self.value))
            except Exception as e:
                return Result(error=e)
        return self

    def unwrap_or(self, default: T) -> T:
        return self.value if self.is_ok else default

# Usage
def divide(a: float, b: float) -> Result[float, str]:
    if b == 0:
        return Result(error="Division by zero")
    return Result(value=a / b)
```

### Retry Decorator

```python
from functools import wraps
import time
from typing import Callable, TypeVar, ParamSpec

P = ParamSpec('P')
R = TypeVar('R')

def retry_on_failure(max_attempts: int = 3, backoff_factor: float = 2.0):
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(backoff_factor ** attempt)
            raise last_exception
        return wrapper
    return decorator
```

## Async/Await Patterns

### Connection Pool

```python
import asyncio
from asyncio import Semaphore, Queue
from contextlib import asynccontextmanager
from typing import AsyncIterator

class AsyncConnectionPool:
    def __init__(self, max_connections: int = 10):
        self._semaphore = Semaphore(max_connections)
        self._connections: Queue = Queue()

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator:
        async with self._semaphore:
            conn = await self._get_or_create_connection()
            try:
                yield conn
            finally:
                await self._connections.put(conn)
```

### Concurrent Processing

```python
from asyncio import TaskGroup  # Python 3.11+

async def batch_process(
    items: list[T],
    processor: Callable[[T], Coroutine[Any, Any, R]],
    max_concurrent: int = 5
) -> list[R]:
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_with_limit(item: T) -> R:
        async with semaphore:
            return await processor(item)

    async with TaskGroup() as tg:
        tasks = [tg.create_task(process_with_limit(item)) for item in items]

    return [task.result() for task in tasks]
```

## Concurrency Patterns

### Thread Pool Processing

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial

def parallel_process(items: list[T], worker_func: Callable[[T], R], max_workers: int = 4) -> list[R]:
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_item = {executor.submit(worker_func, item): item for item in items}
        results = []
        for future in as_completed(future_to_item):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Failed processing {future_to_item[future]}: {e}")
                raise
        return results
```

### Queue-Based Processing

```python
import queue
import threading
from typing import Optional

class WorkerPool:
    def __init__(self, num_workers: int = 4):
        self.task_queue: queue.Queue = queue.Queue()
        self.result_queue: queue.Queue = queue.Queue()
        self.workers = []
        self._start_workers(num_workers)

    def _start_workers(self, num_workers: int):
        for _ in range(num_workers):
            worker = threading.Thread(target=self._worker_loop, daemon=True)
            worker.start()
            self.workers.append(worker)

    def _worker_loop(self):
        while True:
            task = self.task_queue.get()
            if task is None:
                break
            try:
                result = task()
                self.result_queue.put(result)
            except Exception as e:
                self.result_queue.put(e)
            finally:
                self.task_queue.task_done()
```

## API Development Patterns

### FastAPI with Pydantic

```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field, validator
from typing import Optional

class UserCreate(BaseModel):
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    name: str = Field(..., min_length=1, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)

    @validator('email')
    def validate_email(cls, v):
        if '@example.com' in v:
            raise ValueError('Example domains not allowed')
        return v.lower()

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime

app = FastAPI(title="User API", version="1.0.0")

@app.post("/users/", response_model=UserResponse, status_code=201)
async def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service)
) -> UserResponse:
    try:
        created_user = await service.create_user(user)
        return UserResponse(**created_user.dict())
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Failed to create user")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### Request/Response Middleware

```python
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import uuid

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = str(uuid.uuid4())

        # Add request ID to logs
        request.state.request_id = request_id

        response = await call_next(request)

        process_time = time.time() - start_time
        logger.info(
            f"Request {request_id} - {request.method} {request.url} "
            f"completed in {process_time:.3f}s with status {response.status_code}"
        )

        response.headers["X-Request-ID"] = request_id
        return response
```

## Testing Patterns

### Pytest Fixtures and Parametrization

```python
import pytest
from httpx import AsyncClient
from unittest.mock import Mock

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_repository():
    repo = Mock(spec=Repository)
    repo.get.return_value = {"id": "123", "name": "test"}
    return repo

@pytest.mark.parametrize("input_data,expected", [
    ({"value": 10}, 20),
    ({"value": 0}, 0),
])
async def test_process_values(client: AsyncClient, input_data, expected):
    response = await client.post("/process", json=input_data)
    assert response.status_code == 200
    assert response.json()["result"] == expected
```

## Configuration Management

```python
from pydantic import BaseSettings, Field, SecretStr
from functools import lru_cache

class Settings(BaseSettings):
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field(..., env="REDIS_URL")
    debug: bool = Field(False, env="DEBUG")
    api_key: SecretStr = Field(..., env="API_KEY")

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

## Documentation Standards

```python
def process_data(
    data: list[dict[str, Any]],
    *,
    batch_size: int = 100
) -> Iterator[ProcessingResult]:
    """Process data in batches.

    Args:
        data: Input data with 'id' and 'value' keys.
        batch_size: Items per batch for memory efficiency.

    Yields:
        ProcessingResult: Results for each processed item.

    Raises:
        ValidationError: If data format is invalid.
    """
```

## Python Quality Checklist

- [ ] Type hints on all functions and class attributes
- [ ] No mutable default arguments
- [ ] Context managers for resource management
- [ ] Proper exception hierarchy with custom exceptions
- [ ] Dependency injection instead of hard-coded dependencies
- [ ] Abstract base classes for interfaces
- [ ] Property decorators for computed attributes
- [ ] Dataclasses or Pydantic for data models
- [ ] Async/await for I/O operations
- [ ] Generator expressions for memory efficiency
- [ ] Comprehensive docstrings with examples
- [ ] 100% test coverage for business logic if using `<tdd>` mode
- [ ] Property-based tests for complex algorithms if using `<tdd>` mode
- [ ] Performance profiling for critical paths
- [ ] Configuration through environment variables
- [ ] Logging instead of print statements
- [ ] Virtual environments for dependency isolation
- [ ] Pre-commit hooks (black, isort, mypy, ruff)
- [ ] Security scanning with bandit
- [ ] Follows PEP 8 and PEP 484 standards
