"""Local mock platform API routes.

These endpoints simulate enterprise log, config-center, and Git platform
integrations while staying fully deterministic and local.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from app.mock.services import compare_mock_configs, search_mock_commits, search_mock_logs

router = APIRouter(prefix="/mock", tags=["mock"])


@router.get("/logs")
def mock_logs(
    query: str = Query(default="", description="检索关键词或用户问题"),
    context: str = Query(default="", description="执行上下文"),
) -> dict[str, Any]:
    return search_mock_logs(query=query, context=context)


@router.get("/configs")
def mock_configs(
    query: str = Query(default="", description="配置排查问题"),
    context: str = Query(default="", description="执行上下文"),
) -> dict[str, Any]:
    return compare_mock_configs(query=query, context=context)


@router.get("/git/commits")
def mock_git_commits(
    query: str = Query(default="", description="提交检索问题"),
    context: str = Query(default="", description="执行上下文"),
) -> dict[str, Any]:
    return search_mock_commits(query=query, context=context)
