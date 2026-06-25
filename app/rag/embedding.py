"""
Embedding 占位模块。

Day3 当前只实现 deterministic keyword-based retrieval，不加载真实模型、
不联网下载 embedding，也不连接外部向量数据库。后续如需接入真实 embedding，
应在保持可测试 fallback 的前提下扩展这里。
"""

from __future__ import annotations


def embed_text(text: str) -> list[float]:
    """返回确定性的占位向量，避免当前阶段引入真实 embedding 依赖。"""
    if not text:
        return [0.0]
    return [float(len(text))]

