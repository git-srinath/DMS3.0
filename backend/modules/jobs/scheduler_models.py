from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

# Support both FastAPI (package import) and legacy Flask (relative import) contexts
try:
    from backend.modules.jobs.pkgdwprc_python import JobRequestType
except ImportError:  # When running Flask app.py directly inside backend
    from modules.jobs.pkgdwprc_python import JobRequestType  # type: ignore


@dataclass
class SchedulerConfig:
    poll_interval_seconds: int = 15
    schedule_refresh_seconds: int = 60
    max_workers: int = 4
    timezone: str = "UTC"


@dataclass
class QueueRequest:
    request_id: str
    mapref: str
    request_type: JobRequestType
    payload: Dict[str, Any]

    def get_param(self, key: str, default: Optional[Any] = None) -> Any:
        return self.payload.get(key, default)

