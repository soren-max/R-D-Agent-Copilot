"""System API adapter interfaces and local adapter skeletons."""

from app.adapters.base import AdapterResult
from app.adapters.config_adapter import ConfigAdapter, LocalConfigAdapter
from app.adapters.git_adapter import GitAdapter, LocalGitAdapter
from app.adapters.log_adapter import LocalLogAdapter, LogAdapter

__all__ = [
    "AdapterResult",
    "ConfigAdapter",
    "GitAdapter",
    "LocalConfigAdapter",
    "LocalGitAdapter",
    "LocalLogAdapter",
    "LogAdapter",
]
