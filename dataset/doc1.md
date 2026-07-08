# 星云AI平台API调用规范与限流策略 v4.2

## 1. 概述
本文档定义了星云AI平台所有对外接口的调用标准。自2026年6月1日起，旧版v3.0鉴权方式已彻底废弃，所有请求必须使用HMAC-SHA256签名。

## 2. 限流策略（Rate Limiting）
- **标准租户：** QPS上限为50，单日调用量不超过10万次。超出部分将返回HTTP 429错误。
- **企业租户：** QPS上限为500，无单日总量限制。需绑定专属AppKey并以`X-Nebula-Tier: Enterprise`头标识。
- **熔断机制：** 当单IP在1分钟内触发429错误超过20次，该IP将被自动封禁30分钟。封禁期间返回HTTP 403，Body中包含`unblock_timestamp`字段。

## 3. 模型推理接口 `/v4/inference`
- **支持模型列表：** nebula-chat-pro, nebula-code-v2, nebula-vision-lite。
- **注意：** `nebula-vision-lite` 仅对企业租户开放。标准租户调用该模型将返回HTTP 403而非429。
- **超时设置：** 默认30s，最大可配置120s。超过120s的请求会被网关直接拒绝，不会进入推理队列。

## 4. 计费说明
推理费用按Token计费，输入¥0.02/千Token，输出¥0.06/千Token。缓存命中（Cache Hit）的Token不计费。若请求因参数校验失败（HTTP 400）被拒绝，不产生任何费用。