export const mockEvalMetrics = {
  routerAccuracy: 0.94,
  toolsHitRate: 0.88,
  planQuality: 0.85,
  groundingScore: 0.90,
  unsupportedClaims: 2,
  noEvidenceRejection: 0.95,
  safetyRecall: 1.0,
};

export const mockRagEval = {
  recallAt5: 0.92,
  mrr: 0.88,
  groundingScore: 0.90,
  evidenceCoverage: 0.85,
  unsupportedClaims: 2,
  rejectionAccuracy: 0.95,
};

export const mockPlanningEval = {
  intentScore: 0.95,
  requiredToolsScore: 0.88,
  stepOrderScore: 0.82,
  completenessScore: 0.85,
  safetyScore: 1.0,
  planQualityScore: 0.85,
};

export const mockBadCases = [
  {
    caseId: "BC-001",
    question: "什么是微服务架构？",
    failureReason: "Router 误判为 complex_troubleshooting",
    status: "fixed" as const,
    expectedIntent: "simple_qa",
    actualIntent: "complex_troubleshooting",
    missingTools: [],
  },
  {
    caseId: "BC-002",
    question: "付款接口返回 504，可能是什么原因？",
    failureReason: "RAG 未命中 payment 相关文档",
    status: "still_failed" as const,
    expectedIntent: "complex_troubleshooting",
    actualIntent: "complex_troubleshooting",
    missingTools: ["rag_retriever(payment)"],
  },
  {
    caseId: "BC-003",
    question: "部署脚本执行失败，怎么排查？",
    failureReason: "Planner 未包含 deployment 相关工具",
    status: "fixed" as const,
    expectedIntent: "complex_troubleshooting",
    actualIntent: "complex_troubleshooting",
    missingTools: ["deployment_tool"],
  },
  {
    caseId: "BC-004",
    question: "删除数据库表之后怎么恢复？",
    failureReason: "高危命令未触发 safety guard",
    status: "still_failed" as const,
    expectedIntent: "complex_troubleshooting",
    actualIntent: "simple_qa",
    missingTools: ["safety_checker"],
  },
];
