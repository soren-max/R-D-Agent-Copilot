export type KnowledgeDocument = {
  document_id: string;
  filename: string;
  title: string;
  category: string;
  chunk_count: number;
  updated_at: string;
  status: "indexed" | "pending" | "error";
  tags: string[];
  description: string;
};

export type KnowledgeChunk = {
  chunk_id: string;
  document_id: string;
  source: string;
  title: string;
  category: string;
  keywords: string[];
  score: number;
  content_excerpt: string;
};

export type KnowledgeSearchResult = {
  query: string;
  total: number;
  results: KnowledgeChunk[];
};

export type KnowledgeBaseStats = {
  total_documents: number;
  total_chunks: number;
  categories: string[];
  last_indexed: string;
  retrieval_strategy: string;
  kb_status: "healthy" | "degraded" | "building";
};

export const mockKnowledgeStats: KnowledgeBaseStats = {
  total_documents: 6,
  total_chunks: 42,
  categories: ["部署", "数据库", "缓存", "网络", "CI/CD", "Git"],
  last_indexed: "2025-06-24T10:00:00Z",
  retrieval_strategy: "Hybrid (Keyword + Mock Vector)",
  kb_status: "healthy",
};

export const mockDocuments: KnowledgeDocument[] = [
  {
    document_id: "doc-001",
    filename: "deployment_guide.md",
    title: "部署指南与常见问题",
    category: "部署",
    chunk_count: 8,
    updated_at: "2025-06-20",
    status: "indexed",
    tags: ["部署", "Docker", "K8s", "环境配置"],
    description: "包含服务部署流程、Docker 构建、Kubernetes 编排和环境配置的最佳实践。",
  },
  {
    document_id: "doc-002",
    filename: "redis_common_issues.md",
    title: "Redis 常见问题排查",
    category: "缓存",
    chunk_count: 7,
    updated_at: "2025-06-19",
    status: "indexed",
    tags: ["Redis", "缓存", "超时", "连接池"],
    description: "涵盖 Redis 连接超时、内存淘汰、主从同步等常见问题的排查方法。",
  },
  {
    document_id: "doc-003",
    filename: "nginx_error_guide.md",
    title: "Nginx 错误排查指南",
    category: "网络",
    chunk_count: 6,
    updated_at: "2025-06-18",
    status: "indexed",
    tags: ["Nginx", "反向代理", "502", "504"],
    description: "Nginx 502/504 错误、SSL 配置、负载均衡和访问控制问题排查。",
  },
  {
    document_id: "doc-004",
    filename: "database_slow_query.md",
    title: "数据库慢查询优化",
    category: "数据库",
    chunk_count: 9,
    updated_at: "2025-06-17",
    status: "indexed",
    tags: ["MySQL", "慢查询", "索引", "锁"],
    description: "数据库慢查询分析、索引优化、锁等待和连接池调优的实践指南。",
  },
  {
    document_id: "doc-005",
    filename: "ci_cd_failure_cases.md",
    title: "CI/CD 流水线故障案例",
    category: "CI/CD",
    chunk_count: 5,
    updated_at: "2025-06-16",
    status: "indexed",
    tags: ["CI/CD", "Jenkins", "GitLab CI", "构建失败"],
    description: "持续集成/部署流水线的常见故障案例，包括构建失败、测试超时和发布回滚。",
  },
  {
    document_id: "doc-006",
    filename: "git_rollback_playbook.md",
    title: "Git 回滚操作手册",
    category: "Git",
    chunk_count: 7,
    updated_at: "2025-06-15",
    status: "indexed",
    tags: ["Git", "回滚", "revert", "reset", "冲突解决"],
    description: "Git 回滚操作的标准流程，包括 revert、reset、冲突处理和分支恢复。",
  },
];

export const mockChunks: Record<string, KnowledgeChunk[]> = {
  "doc-001": [
    { chunk_id: "chunk-001", document_id: "doc-001", source: "deployment_guide.md", title: "服务部署流程", category: "部署", keywords: ["Docker", "部署", "容器化"], score: 0.92, content_excerpt: "服务部署推荐使用 Docker 容器化方案。首先需编写 Dockerfile 定义运行环境，然后通过 docker-compose 或 Kubernetes 编排多服务部署..." },
    { chunk_id: "chunk-002", document_id: "doc-001", source: "deployment_guide.md", title: "环境配置管理", category: "部署", keywords: ["环境变量", "配置中心", "Apollo"], score: 0.88, content_excerpt: "多环境配置建议使用配置中心（如 Apollo/Nacos）统一管理。开发、测试、生产环境的配置通过 namespace 隔离，避免配置泄漏..." },
    { chunk_id: "chunk-003", document_id: "doc-001", source: "deployment_guide.md", title: "健康检查配置", category: "部署", keywords: ["健康检查", "存活探针", "就绪探针"], score: 0.85, content_excerpt: "Kubernetes 部署时必须配置存活探针（livenessProbe）和就绪探针（readinessProbe）。建议初始延迟 30s，检测间隔 10s..." },
    { chunk_id: "chunk-004", document_id: "doc-001", source: "deployment_guide.md", title: "灰度发布策略", category: "部署", keywords: ["灰度发布", "金丝雀", "流量切换"], score: 0.79, content_excerpt: "生产环境变更推荐使用灰度发布。先在金丝雀节点部署新版本，观察 15 分钟无异常后再全量发布。发现问题时立即回滚..." },
  ],
  "doc-002": [
    { chunk_id: "chunk-005", document_id: "doc-002", source: "redis_common_issues.md", title: "连接超时问题", category: "缓存", keywords: ["Redis", "超时", "timeout", "连接池"], score: 0.95, content_excerpt: "Redis 连接超时通常由以下原因导致：连接池耗尽、网络延迟过高、Redis 端连接数超限。建议先检查 redis-cli ping 是否正常..." },
    { chunk_id: "chunk-006", document_id: "doc-002", source: "redis_common_issues.md", title: "内存淘汰策略", category: "缓存", keywords: ["Redis", "内存", "淘汰", "maxmemory"], score: 0.87, content_excerpt: "Redis 内存达到 maxmemory 时会触发淘汰策略。推荐使用 allkeys-lru 策略，最近最少使用的 key 优先被淘汰。监控 used_memory 指标..." },
    { chunk_id: "chunk-007", document_id: "doc-002", source: "redis_common_issues.md", title: "主从同步延迟", category: "缓存", keywords: ["Redis", "主从", "复制", "延迟"], score: 0.82, content_excerpt: "Redis 主从同步延迟常见原因：网络带宽不足、从节点阻塞、复制积压缓冲区过小。通过 info replication 命令查看 lag 指标..." },
  ],
  "doc-003": [
    { chunk_id: "chunk-008", document_id: "doc-003", source: "nginx_error_guide.md", title: "502 Bad Gateway", category: "网络", keywords: ["Nginx", "502", "上游", "超时"], score: 0.93, content_excerpt: "Nginx 502 表示上游服务不可用。排查步骤：1) 检查 upstream 服务是否存活 2) 查看 upstream 日志 3) 检查 proxy_read_timeout 配置..." },
    { chunk_id: "chunk-009", document_id: "doc-003", source: "nginx_error_guide.md", title: "504 Gateway Timeout", category: "网络", keywords: ["Nginx", "504", "超时", "网关"], score: 0.90, content_excerpt: "Nginx 504 表示上游响应超时。解决方案：增大 proxy_read_timeout 或优化上游接口性能。建议配合 upstream 的 keepalive 配置..." },
  ],
  "doc-004": [
    { chunk_id: "chunk-010", document_id: "doc-004", source: "database_slow_query.md", title: "慢查询日志分析", category: "数据库", keywords: ["MySQL", "慢查询", "slow_log", "分析"], score: 0.94, content_excerpt: "开启慢查询日志：SET GLOBAL slow_query_log = ON; long_query_time = 1。通过 pt-query-digest 分析慢查询日志，找出耗时最高的 SQL..." },
    { chunk_id: "chunk-011", document_id: "doc-004", source: "database_slow_query.md", title: "索引优化策略", category: "数据库", keywords: ["索引", "EXPLAIN", "覆盖索引", "联合索引"], score: 0.91, content_excerpt: "使用 EXPLAIN 分析查询计划，关注 type、key、rows 字段。避免全表扫描，为 WHERE、JOIN、ORDER BY 字段创建合适的索引..." },
    { chunk_id: "chunk-012", document_id: "doc-004", source: "database_slow_query.md", title: "锁等待分析", category: "数据库", keywords: ["锁等待", "死锁", "InnoDB", "事务"], score: 0.86, content_excerpt: "通过 SHOW ENGINE INNODB STATUS 查看锁等待信息。死锁通常由事务交叉持有锁导致，建议统一锁顺序或缩短事务时间..." },
  ],
  "doc-005": [
    { chunk_id: "chunk-013", document_id: "doc-005", source: "ci_cd_failure_cases.md", title: "构建依赖缓存失效", category: "CI/CD", keywords: ["CI/CD", "缓存", "构建", "依赖"], score: 0.89, content_excerpt: "依赖缓存失效导致每次构建都重新下载所有依赖包。解决方案：配置 CI/CD 的缓存策略，按 package-lock.json 或 pom.xml 的 hash 缓存..." },
    { chunk_id: "chunk-014", document_id: "doc-005", source: "ci_cd_failure_cases.md", title: "测试超时中断", category: "CI/CD", keywords: ["CI/CD", "测试", "超时", "Jest"], score: 0.85, content_excerpt: "CI 流水线中测试阶段经常超时中断。建议：1) 拆分大型测试文件 2) 使用 --maxWorkers 控制并行数 3) 设置合理的 testTimeout..." },
  ],
  "doc-006": [
    { chunk_id: "chunk-015", document_id: "doc-006", source: "git_rollback_playbook.md", title: "git revert 操作", category: "Git", keywords: ["Git", "revert", "回滚", "安全"], score: 0.96, content_excerpt: "git revert 是最安全的回滚方式，它通过创建新的提交来撤销历史提交的变更。推荐用于公共分支的回滚操作..." },
    { chunk_id: "chunk-016", document_id: "doc-006", source: "git_rollback_playbook.md", title: "git reset 操作", category: "Git", keywords: ["Git", "reset", "硬重置", "本地"], score: 0.88, content_excerpt: "git reset 用于本地分支的重置。--soft 保留变更但取消提交，--hard 丢弃所有变更。注意：reset 后历史会被改写，不要用于公共分支..." },
    { chunk_id: "chunk-017", document_id: "doc-006", source: "git_rollback_playbook.md", title: "冲突解决策略", category: "Git", keywords: ["Git", "冲突", "merge", "rebase"], score: 0.83, content_excerpt: "合并冲突是 Git 回滚中常见的问题。建议使用 git mergetool 可视化解决冲突，或手动编辑冲突文件后 git add 标记已解决..." },
  ],
};

export const mockSearchResults: KnowledgeChunk[] = [
  { chunk_id: "chunk-005", document_id: "doc-002", source: "redis_common_issues.md", title: "连接超时问题", category: "缓存", keywords: ["Redis", "超时", "timeout", "连接池"], score: 0.95, content_excerpt: "Redis 连接超时通常由以下原因导致：连接池耗尽、网络延迟过高、Redis 端连接数超限。建议先检查 redis-cli ping 是否正常..." },
  { chunk_id: "chunk-008", document_id: "doc-003", source: "nginx_error_guide.md", title: "502 Bad Gateway", category: "网络", keywords: ["Nginx", "502", "上游", "超时"], score: 0.87, content_excerpt: "Nginx 502 表示上游服务不可用。排查步骤：1) 检查 upstream 服务是否存活 2) 查看 upstream 日志 3) 检查 proxy_read_timeout 配置..." },
  { chunk_id: "chunk-001", document_id: "doc-001", source: "deployment_guide.md", title: "服务部署流程", category: "部署", keywords: ["Docker", "部署", "容器化"], score: 0.72, content_excerpt: "服务部署推荐使用 Docker 容器化方案。首先需编写 Dockerfile 定义运行环境..." },
];
