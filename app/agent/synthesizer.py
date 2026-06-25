"""
结果合成器 — 基于工具返回结果生成中文回答。

职责：
- 根据 route + tool_results 合成最终回答
- 必须基于工具结果，不编造信息
- 输出中文
"""

from __future__ import annotations

from app.core.models import Plan, RouterResult, ToolCallRecord


class Synthesizer:
    """工具结果 → 中文回答。"""

    def synthesize(
        self,
        query: str,
        route_result: RouterResult,
        plan: Plan,
        tool_results: list[ToolCallRecord],
    ) -> str:
        if route_result.type == "simple_qa":
            return self._synthesize_simple_qa(query, tool_results)
        else:
            return self._synthesize_troubleshooting(query, tool_results)

    def _synthesize_simple_qa(
        self, query: str, tool_results: list[ToolCallRecord]
    ) -> str:
        rag_result = next((r for r in tool_results if r.tool == "rag_retriever"), None)
        if rag_result and rag_result.documents:
            top_doc = rag_result.documents[0]
            sources = "、".join(dict.fromkeys(doc["source"] for doc in rag_result.documents))
            return (
                f"简要解释：针对「{query}」，本地知识库中的相关说明是："
                f"{top_doc['content'][:220]}\n\n"
                f"相关知识来源：{sources}\n\n"
                "补充说明：以上内容来自本地 Markdown 知识库样例，当前未接入真实 LLM 或外部知识源。"
            )

        if rag_result and rag_result.error:
            return (
                f"简要解释：知识库中未检索到直接相关内容，暂时无法基于本地文档解释「{query}」。\n\n"
                f"相关知识来源：{rag_result.source or 'data/docs'}\n\n"
                "补充说明：当前回答不会编造知识库之外的具体事实。"
            )

        evidence = "；".join(r.result for r in tool_results if r.result) or "未获取到执行器结果。"
        return (
            f"初步判断：Router 将「{query}」判定为简单问答。\n\n"
            f"排查证据：{evidence}\n\n"
            "建议处理方式：Day1 未接入知识库或真实 LLM，当前不能编造工具之外的信息；"
            "建议在后续阶段接入受控知识源后再生成详细解释。"
        )

    def _synthesize_troubleshooting(
        self, query: str, tool_results: list[ToolCallRecord]
    ) -> str:
        if not tool_results:
            return "暂未获取到工具执行结果，无法进行分析。"

        # 收集各工具结果摘要
        log_result = ""
        config_result = ""
        git_result = ""
        rag_result = ""
        rag_sources = ""
        has_error = False
        has_failed_tool = any(record.status == "failed" for record in tool_results)

        for record in tool_results:
            if record.tool == "log_tool" and record.status == "success":
                log_result = record.result[:200]
                if "错误日志" in record.result or "ERROR" in record.result:
                    has_error = True
            elif record.tool == "config_tool" and record.status == "success":
                config_result = record.result[:200]
            elif record.tool == "git_tool" and record.status == "success":
                git_result = record.result[:200]
            elif record.tool == "rag_retriever" and record.status == "success" and record.documents:
                rag_result = "；".join(doc["content"][:120] for doc in record.documents[:2])
                rag_sources = "、".join(dict.fromkeys(doc["source"] for doc in record.documents))
            elif record.tool == "rag_retriever" and record.error:
                rag_result = "知识库中未检索到直接相关内容。"

        # 合成三段式回答
        paragraphs: list[str] = []

        # 1. 初步判断
        if has_error:
            paragraphs.append(
                f"初步判断「{query}」可能与系统异常、配置差异或最近代码变更有关。"
            )
        else:
            paragraphs.append(f"针对「{query}」，以下是排查结果：")

        if has_failed_tool:
            paragraphs.append("部分工具查询失败，以下判断基于已成功返回的数据。")

        # 2. 证据
        if log_result:
            paragraphs.append(f"工具证据：【日志分析】{log_result}")
        if config_result:
            paragraphs.append(f"工具证据：【配置分析】{config_result}")
        if git_result:
            paragraphs.append(f"工具证据：【代码变更】{git_result}")
        if rag_result:
            source_suffix = f" 来源：{rag_sources}" if rag_sources else ""
            paragraphs.append(f"知识库补充：{rag_result}{source_suffix}")

        # 3. 建议
        suggestions: list[str] = []
        if has_error:
            suggestions.append("建议优先查看对应服务的详细错误日志，定位异常堆栈。")
        if config_result and "不一致" in config_result:
            suggestions.append("建议核对各环境的配置差异，确保 prod 环境配置正确。")
        if git_result:
            suggestions.append("建议回查最近的代码提交，确认变更是否引入了问题。")
        if not suggestions:
            suggestions.append("建议进一步检查系统状态和监控指标。")

        paragraphs.append("【建议处理方式】" + " ".join(suggestions))

        return "\n\n".join(paragraphs)
