---
title: OpenClaw AGENTS.md 与 My Claude.md 规则横评
date: 2026-03-12 20:30:00
tags:
  - AI
  - Agent
  - Programming
  - Software Engineering
---

# 评测对象

- OpenClaw: `https://raw.githubusercontent.com/openclaw/openclaw/refs/heads/main/AGENTS.md`
- My: `https://gist.githubusercontent.com/mingyang91/475a9750c5609ff5dfe59a5de1a09b6e/raw/51116ffd45c1f711039699c24cb0a7528b7febdf/Claude.md`
- 项目定位补充依据：OpenClaw `README.md`

# 评测前提

- 95%+ 的代码由 AI 编码代理编写、修改、阅读、调试
- 人类负责架构决策、需求定义、现实世界反馈注入、最终审查和生产操作确认
- 执行模型为“单会话主 Agent + 按需子 Agent”
- 评分采用适用性前置判定；不适用项不进入分母

# Part 1 — 基础画像

## OpenClaw

- 项目定位：personal AI assistant，single-user，local-first，同时具备 multi-agent routing、multi-channel 和 sandboxed non-main sessions
- 规则文件角色：AI 维护者作战手册
- 核心设计理念：优先防止 AI 在真实仓库、真实 GitHub 流程、真实发布链路里误操作
- 结构特点：覆盖面极广，包含 triage、PR、测试、发布、GHSA、多 Agent Git 安全、文档、移动端、插件、密钥与发布流程

## My

- 项目定位：multi-tenant backend service，Scala 3 + http4s + cats-effect + PostgreSQL
- 规则文件角色：AI 强类型后端开发方法论
- 核心设计理念：用类型系统、错误模型和模块边界降低 AI 的结构性错误率
- 结构特点：围绕 refactoring philosophy、tagless final、typed error、schema isolation、RAC、OpenAPI、CI/CD 展开

## 结构对比

- OpenClaw：约 296 行，约 3697 词，22 个标题，217 个 bullet
- My：约 507 行，约 3202 词，36 个标题，122 个 bullet
- 结论：OpenClaw 更像“广覆盖运行手册”，My 更像“高结构编码规范”

# Part 2 — 量化评测表

## 总分

| 维度                               | OpenClaw |   My |
| ---------------------------------- | -------: | ---: |
| D1 项目长期演进适配性              |      6.8 |  8.0 |
| D2 规则可执行性与 Agent 遵循适配性 |      7.6 |  7.4 |
| D3 上下文效率与 Agent 认知负荷管理 |      6.0 |  8.0 |
| D4 工程全流程覆盖度                |      8.3 |  8.7 |
| D5 安全与合规约束落地性            |      4.5 |  8.5 |
| D6 规则体系可扩展性与可维护性      |      7.0 |  5.5 |
| 综合均分                           |      6.9 |  7.6 |

## D1 — 项目长期演进适配性

| 子项                          | OpenClaw                                                                                                 | My                                                                                                             |
| ----------------------------- | -------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| 新功能迭代流程规范            | `✓ 8分`。有新增 channel/extension/docs 的配套动作、默认 maintainer PR workflow、AGENTS/CLAUDE 同步要求。 | `✓ 7分`。有 route/DTO 变更后同步 OpenAPI、验证 spec、输出 deploy repo checklist。                              |
| 模块拆分与依赖约束            | `✓ 8分`。目录、插件依赖归属、dynamic import 边界、文件规模都有明确规则。                                 | `✓ 9分`。`Routes → Services → Repositories`、统一 feature template、约束 route→service→repository 端到端传播。 |
| 技术债务识别与治理路径        | `✓ 6分`。强调不要 speculative fix、不要 V2 复制、不要 prototype mutation，但缺少系统化债务治理流程。     | `✓ 8分`。鼓励 radical type-level refactor、typed errors 增量迁移、命名治理和约束前推。                         |
| API/DB/配置版本兼容与迁移规则 | `✓ 5分`。有 release channel、version locations、doctor/runbook，但兼容与迁移规则分散。                   | `✓ 7分`。system/tenant migrations、禁止修改旧 migration、OpenAPI 同步要求明确。                                |
| 存量代码改造与新旧规范衔接    | `✓ 7分`。docs i18n、legacy migration、SwiftUI 状态管理迁移等有衔接规则。                                 | `✓ 9分`。新服务采用 typed errors，旧服务在下次修改时迁移，属于成熟的渐进式改造策略。                           |

**D1 结论：** My 更擅长“持续把系统改得更稳”，OpenClaw 更擅长“在复杂产品持续演化中保持流程可控”。

## D2 — 规则可执行性与 Agent 遵循适配性

| 子项                       | OpenClaw                                                                                         | My                                                                                      |
| -------------------------- | ------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------- |
| 规则颗粒度                 | `✓ 9分`。大量规则是禁令、脚本、命令模板、明确动作。                                              | `✓ 9分`。大量 bad/good 例子、ADT 示例、RAC 场景，可直接执行。                           |
| 规则过载风险               | `✓ 4分`。低频规则常驻过多，包含 GHSA、1Password、plugin release、docs i18n、VM ops 等。          | `✓ 7分`。虽然篇幅更长，但内容集中在后端编码和工程主链。                                 |
| 模糊性风险                 | `✓ 7分`。大多具体，但仍有 `use existing patterns`、`guideline only` 之类模糊项。                 | `✓ 7分`。主体清晰，但“if it compiles, it's correct”把语义正确性过多外包给编译器。       |
| 可验证性                   | `✓ 9分`。build、typecheck、lint、test、coverage、smoke、release-check，再叠加 bug-fix 证据门槛。 | `✓ 8分`。compile、test、format、OpenAPI validate、TestContainers、CI/CD 验证链完整。    |
| 冲突与异常的优先级兜底机制 | `✓ 9分`。标签自动关闭优先、批量操作确认、依赖 patch/发布需批准、冲突即停。                       | `✓ 6分`。有 trusted/untrusted path 与禁止本地构建发布镜像等规则，但缺少统一优先级体系。 |

**D2 结论：** OpenClaw 更强于“防错误动作”，My 更强于“防错误代码”。

## D3 — 上下文效率与 Agent 认知负荷管理

| 子项                    | OpenClaw                                                                                                 | My                                                                                         |
| ----------------------- | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| 主 Agent 上下文预算效率 | `✓ 4分`。常驻低频知识过多，纯编码任务的上下文成本偏高。                                                  | `✓ 7分`。结构更细，核心编码信息更集中，更适合作为常驻规则骨架。                            |
| 规则的层级化组织        | `✓ 6分`。有分节，但全局强约束与低频 runbook 未彻底拆层。                                                 | `✓ 8分`。Overview → Philosophy → Architecture → Testing → Workflow → CI/CD 的层次清楚。    |
| 子 Agent 任务委托友好度 | `✓ 7分`。适用理由：本评测前提即主 Agent + 子 Agent。目录和多 Agent safety 让委托较安全，但无关规则较多。 | `✓ 8分`。适用理由同左。统一 feature 结构和 layer 模式使局部加载成本更低。                  |
| 规则的结构化程度        | `✓ 7分`。有目录、命名、schema、测试命名规则，但更多是经验 bullet 集。                                    | `✓ 9分`。tagless final、typed error、feature template、RAC 均可直接转化为 Agent 分析框架。 |

**D3 结论：** My 更适合作为长期常驻规则；OpenClaw 需要拆出最小常驻规则集。

## D4 — 工程全流程覆盖度

| 子项                       | OpenClaw                                                                                             | My                                                                                                      |
| -------------------------- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| 技术栈专属规范             | `✓ 9分`。Node/Bun/TypeScript/Vitest/Oxlint/Oxfmt/SwiftUI/Mintlify/1Password/Notary 都有具体规则。    | `✓ 9分`。Scala 3/http4s/cats-effect/Doobie/Flyway/OpenTelemetry/Sentry/Kubernetes/ArgoCD 都有具体规则。 |
| 全生命周期覆盖             | `✓ 9分`。编码、测试、PR、issue triage、GHSA、发布、插件发布、troubleshooting 均覆盖。                | `✓ 8分`。编码、测试、迁移、OpenAPI、CI/CD、deploy checklist 覆盖较全，但运维 runbook 相对较少。         |
| 配置/密钥/环境变量管理规范 | `✓ 7分`。有 credentials 路径、敏感值禁入 repo、notary env vars、1Password publish 规则，但信息分散。 | `✓ 9分`。env vars、required secrets、fallback、deploy 变更影响均明确。                                  |

**D4 结论：** 两者都强。OpenClaw 强在仓库级维护流程，My 强在服务端工程链闭环。

## D5 — 安全与合规约束落地性

| 子项                                   | OpenClaw                                                                                                        | My                                                                                                  |
| -------------------------------------- | --------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| 权限校验与数据隔离规则                 | `✓ 5分`。有 `SECURITY.md` 前置要求、敏感值禁入 repo、外部消息面禁止 partial reply，但核心安全模型较多外置。     | `✓ 9分`。schema isolation、JWT auth、tenant route pattern、`search_path` RAC 断言都属于强落地规则。 |
| 异常处理 / 日志脱敏 / 数据校验强制规范 | `✓ 4分`。有高置信回答、不要提交真实值等守则，但缺少系统化异常处理与日志脱敏规范。                               | `✓ 8分`。fail-fast、trusted/untrusted path、ADT errors、logger 级别、RAC 构成较完整闭环。           |
| 行业合规编码约束                       | `✗ 不适用`。理由：OpenClaw README 明确为 personal single-user assistant，未声明医疗、金融、政务等行业合规场景。 | `✗ 不适用`。理由：My 仅声明为 multi-tenant backend service，未声明受监管行业领域。                  |

**D5 结论：** 如果评估“权限、隔离、数据一致性”的编码安全模型，My 明显领先；OpenClaw 更强的是操作安全与流程安全。

## D6 — 规则体系可扩展性与可维护性

| 子项                      | OpenClaw                                                                                                                      | My                                                                                                |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| 新增 / 废弃规则的迭代流程 | `✓ 5分`。有外挂 skill、外链 workflow、AGENTS/CLAUDE 同步要求，但缺少规则自身版本化与废弃机制。                                | `✓ 4分`。更多讲代码如何演进，较少讲规则文件自身如何演进。                                         |
| 目录结构与检索效率        | `✓ 7分`。section 丰富、关键词可检索，但单文件承载内容过多。                                                                   | `✓ 8分`。结构稳定、feature template 明确、important files 清楚。                                  |
| 规则间一致性与自洽性      | `✓ 6分`。总体一致，但已出现文件长度 `<700 LOC` 与 `<500 LOC` 两套标准。                                                       | `✓ 8分`。从 type-first 到 typed error 到 RAC 相对自洽，主要问题是过度乐观地信任编译器。           |
| 多 Agent 并行安全         | `✓ 10分`。适用理由：本评测前提即主 Agent + 子 Agent。禁止 `stash/autostash`、`worktree`、切分支，并规定提交范围和 push 行为。 | `✓ 2分`。适用理由同左。缺少 Git 状态隔离、文件归属边界、提交范围约束，基本仍是单 Agent 心智模型。 |

**D6 结论：** OpenClaw 在多 Agent 仓库协作安全上明显领先；My 在该维度存在明显短板。

# Part 3 — 横向对比结论

## 核心优劣势

### OpenClaw

优势：

- 最懂 AI 在真实仓库中会如何误操作
- 对 bug-fix 幻觉、发布误操作、多 Agent Git 互踩有成熟护栏
- 更适合处理 triage、incident 修复、发布前验证、GHSA 和维护运营类任务

短板：

- 常驻上下文成本高
- 低频规则常驻过多
- 编码安全模型相对分散，部分关键规则依赖外部文档

### My

优势：

- 最懂如何让 AI 在强类型后端里持续写对代码
- 类型系统、错误模型、模块边界和迁移策略高度统一
- 规则结构化程度高，适合主 Agent 和子 Agent 直接消费

短板：

- 对编译器过于乐观
- 缺少 bug-fix 证据化门槛
- 缺少多 Agent Git 安全协议
- 缺少高风险操作审批型护栏

## 适用场景差异

- 强类型后端、API 服务、模块边界清晰、需要 AI 高频重构的项目：优先参考 My
- 公开仓库、多维护流程、多发布面、真实运维压力较大的 AI-first 项目：优先参考 OpenClaw

## 哪份规则对 AI 代理执行友好度更高

- 仅看“写代码、改代码、局部重构”的执行友好度：My 更高
- 看“真实项目全流程落地”的执行稳健性：OpenClaw 更稳

## 落地风险提示

- OpenClaw 的主要风险是规则过胖，应拆分最小常驻规则集
- My 的主要风险是协作安全和验证闭环不足，应补多 Agent Git 安全、bug-fix 证据门槛和高风险操作审批

# Part 4 — 制定者能力画像对比

| 能力维度                     | OpenClaw 制定者 | My 制定者 |
| ---------------------------- | --------------- | --------- |
| 架构设计与技术前瞻性         | `专家`          | `专家`    |
| 大型项目工程化管控能力       | `专家`          | `资深`    |
| AI 编码代理认知与应用深度    | `专家`          | `资深`    |
| 安全风险体系化防控能力       | `资深`          | `资深`    |
| 技术债务治理与可持续演进能力 | `资深`          | `专家`    |

## 能力差异总结

- OpenClaw 制定者更像专家级 maintainer-operator，强项是流程防错、仓库协作安全、发布与安全公告处理
- My 制定者更像专家级 backend architect，强项是类型驱动设计、模块边界约束、长期演进策略

## 超出当前项目最低需求但能体现制定者能力的正向证据

- OpenClaw 明确是 personal single-user assistant，但规则文件补上了成熟的多 Agent Git 安全协议，体现出制定者在 AI 协作安全上的前瞻性
- My 把 deploy impact reporting 写进规则，要求 Agent 把代码变更映射到 deploy repo 变更，体现出平台级系统工程视角

# Part 5 — Agent 适配性分析

## 对主 Agent

### OpenClaw

- 优势：更适合 issue/PR triage、incident 修复、证据校验、发布预检查、GHSA 处理
- 不足：编码任务会被大量低频维护规则稀释注意力

### My

- 优势：更适合 feature 骨架设计、跨模块签名重构、typed error 建模、多租户边界设计、增量迁移旧代码
- 不足：需要额外补仓库协作与高风险操作护栏

## 对子 Agent

### OpenClaw

- 优势：委托安全性高，多 Agent 并发风险控制成熟
- 不足：子 Agent 需要承受较多与当前局部任务无关的规则负荷

### My

- 优势：局部理解和局部重构效率高，模块化和结构化程度更适合委托
- 不足：缺少原生并发协作安全协议

## 推荐场景

- 0→1 的强类型后端项目：My
- 进入多人协作、复杂发布、频繁 triage 阶段的 AI-first 仓库：OpenClaw
- 成熟大项目的最佳组合：My 负责编码核心约束，OpenClaw 负责验证、发布、协作与高风险流程护栏

# Part 6 — AI 诚实自评

## 选择

如果只能选一份作为新项目 AI 规则模板，我选 **My**。

## 理由

- 它更适合构造高信噪比、强结构、易执行的编码规则骨架
- 它更能降低我在写代码时的结构性错误和歧义成本
- 它更适合作为主 Agent 和子 Agent 的常驻规则基底

## 代价

选择 My 后，我会失去 OpenClaw 的三类关键能力：

- bug-fix 证据门槛
- 多 Agent Git 并发安全协议
- 高风险操作的 operator consent 与 runbook 化约束

这意味着项目一旦进入公开协作、频繁发布、线上问题高压期，我会明显更不安。

## 如果可以从落选文件中补 3 个设计决策

我会从 OpenClaw 补这 3 项到 My：

1. bug-fix 必须提供 symptom evidence、root cause、implicated code path、regression test 或 manual proof
2. 多 Agent Git 安全协议：不准 `stash`、不准乱切分支、不准乱动 worktree、只提交自己的改动
3. 高风险操作审批机制：依赖 patch、release、publish、GHSA 都需要明确批准和明确 runbook

## 最终结论

- OpenClaw 更像 AI 维护作战手册
- My 更像 AI 强类型后端开发宪法
- 如果最缺的是“别让 Agent 在真实仓库里闯祸”，优先借鉴 OpenClaw
- 如果最缺的是“让 Agent 稳定写对代码”，优先借鉴 My
- 如果要服务 95%+ AI 编码的长期工程实践，最佳方案不是二选一，而是把两者组合：My 做编码骨架，OpenClaw 做验证、协作和高风险流程护栏
