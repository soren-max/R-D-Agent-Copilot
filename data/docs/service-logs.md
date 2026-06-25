# 服务日志说明

服务日志是研发排障中最直接的证据来源。一次请求通常会在网关、业务服务和下游依赖中产生多条日志，trace_id 用来把这些日志串起来。排查时应先从用户报错时间点或接口路径定位日志，再使用 trace_id 查询同一次调用链路中的上下游记录。

日志级别通常分为 ERROR、WARN 和 INFO。ERROR 表示请求或任务出现明确失败，可能影响用户结果；WARN 表示存在异常迹象或降级行为，但不一定导致请求失败；INFO 用于记录正常流程中的关键状态，例如请求开始、调用下游、返回结果等。排障时不要只看 ERROR，WARN 和 INFO 往往能说明失败前发生了什么。

status=500 通常表示服务端处理失败，可能来自业务异常、未捕获异常、下游调用失败、配置错误或数据状态不符合预期。它不一定代表当前服务本身有 bug，也可能是 order-service 调用 payment-service 超时后，把失败转换成了 500 响应。

timeout 常见原因包括下游服务响应慢、网络抖动、线程池排队、连接池耗尽、配置的 timeout 过短、重试放大流量，或新功能开关引入额外调用链路。判断 timeout 时需要同时看 duration_ms、dependency、retry_count 和最终 status。

日志排查建议：先按 trace_id 聚合请求链路，再按时间顺序阅读；关注 service、endpoint、status、error、dependency、duration_ms 和 retry_count；如果同一 trace_id 中多个服务都有异常，应优先定位第一个异常点，而不是最后一个返回 500 的服务。
