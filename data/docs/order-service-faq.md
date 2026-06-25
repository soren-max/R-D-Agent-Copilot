# 订单服务 FAQ

## 订单接口报 500 的常见原因

订单接口报 500 通常表示 order-service 在创建或更新订单时遇到服务端失败。常见原因包括 payment-service 调用超时、支付预校验失败、订单状态不合法、异常处理逻辑未覆盖、配置不一致，或新支付流程引入额外失败路径。排查时应先看 trace_id 对应日志。

## order-service 和 payment-service 的关系

order-service 负责订单创建、状态流转和重试判断；payment-service 负责支付预校验、支付请求和支付状态返回。订单创建流程中，order-service 可能会调用 payment-service。所以下游支付服务慢或失败，可能表现为订单接口 500 或 timeout。

## payment.timeout 配置影响

payment.timeout 控制 order-service 等待 payment-service 响应的最长时间。配置过短时，下游慢请求可能被提前判定为失败；配置过长时，订单接口会长时间占用线程。排查时要结合 duration_ms 判断。

## retry_count 配置影响

retry_count 决定订单服务在下游失败时是否重试以及重试次数。重试可以缓解短暂抖动，也可能放大下游压力。若日志中出现 retry_count 已耗尽，说明请求在返回 500 前已经尝试恢复。

## enable_new_payment_flow 的风险

enable_new_payment_flow 用于控制是否启用新支付流程。开启后可能改变调用链路、错误码转换、fallback 行为和日志字段。若问题只在开启该开关的环境出现，应优先对比旧流程与新流程的异常处理差异，并确认回滚方案。
