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

- OpenClaw：`https://raw.githubusercontent.com/openclaw/openclaw/refs/heads/main/AGENTS.md`
- My（下文即 Linewise）：`https://gist.githubusercontent.com/mingyang91/475a9750c5609ff5dfe59a5de1a09b6e/raw/51116ffd45c1f711039699c24cb0a7528b7febdf/Claude.md`
- 项目定位补充依据：OpenClaw `README.md`；Linewise 的项目定位以规则文件自身及仓库结构说明为准

# 评测方法与判定图例

- 本文默认两个项目都是 **AI-native 项目**：代码的编写、修改、阅读、调试主要由 AI 编码代理完成，人类负责需求、反馈注入、最终审查与高风险动作确认。
- 本文不预设“渐进式 AI-native”或“原生式 AI-native”哪条路径更优，只评估：规则文件是否能支撑 agent **长期、高质量、一致地**自主执行。
- 评测时先做两层前置判定：
  - `✗ 不适用`：该子项不属于项目合理需求范围，不计入分母。
  - `✗ 未委托`：该子项对项目可能有意义，但规则文件没有把该职责委托给 agent，不计入分母。
  - `✓ 已委托`：该子项既适用又已交给 agent，才进入 1-10 分打分。
- 图例：`✓ 已委托｜8/10` 表示“该项适用且已委托给 agent，评分 8 分”；`✗ 不适用` 与 `✗ 未委托` 后均附一句理由。
- 对目标架构的尊重：
  - OpenClaw 按 **多 agent 并行 / 大量外部贡献者 agent** 的目标架构评估。
  - My 按 **高能力主 agent 深入单仓库长期演进** 的目标架构评估。

# Part 1 — 基础画像

## OpenClaw

- **项目定位**：开源自主 AI 代理平台，覆盖 CLI、桌面端、移动端、插件、消息通道、GH 维护与发布链路。
- **规则文件角色**：面向 maintainer 与外部贡献者 agent 的仓库级执行手册。
- **核心设计理念**：优先防止 agent 在真实 GitHub、真实 Git、真实发布链路中“高置信度做错事”。
- **结构特征**：覆盖 triage、PR truthfulness、build/test、coding style、release channel、GHSA、安全提示、1Password 发布、插件发布 fast path、多 agent Git 安全等。
- **一句话总结**：它更像一套面向复杂开源仓库的 **AI 维护操作系统**。

## My

- **项目定位**：多租户 Scala 3 / http4s 后端 API，强调 tagless-final、cats-effect、Doobie、PostgreSQL schema isolation、Vertex AI、Quartz 与多租户安全边界。
- **规则文件角色**：面向高能力主 agent 的强类型后端开发与演进规范。
- **核心设计理念**：通过类型系统、分层边界、typed error、编译器与工具链，把 agent 的错误从运行时前移到编译期与签名层。
- **结构特征**：围绕 refactoring philosophy、tagless final、flat `for`、typed error、schema isolation、RAC、OpenAPI、Metals、deploy impact reporting 展开。
- **一句话总结**：它更像一套面向成熟后端存量代码的 **AI 结构化演进宪法**。

## 基础对比结论

- OpenClaw 的强项是 **广覆盖、强 runbook、强并发协作安全、强外部流程防错**。
- My 的强项是 **深架构约束、强类型驱动、强渐进式重构、强后端正确性约束**。
- 如果把两者硬放在同一赛道比“谁更全”，结论会失真；更准确的说法是：**两者分别在不同 AI-native 工程阶段和执行架构上做到非常成熟。**

# Part 2 — 量化评测表

## 维度总览

> 注：下表分数仅基于“适用且已委托”的子项平均；参考均分仅用于帮助阅读，不代表脱离场景的绝对胜负。

| 维度                               | OpenClaw |   My | 结论摘要      |
| ---------------------------------- | -------: | ---: | ------------- |
| D1 项目长期演进适配性              |      7.6 |  9.4 | My 显著更强   |
| D2 规则可执行性与 Agent 遵循适配性 |      8.7 |  8.1 | OpenClaw 略强 |
| D3 上下文效率与 Agent 认知负荷管理 |      8.7 |  7.7 | OpenClaw 更强 |
| D4 已委托领域的工程深度与可持续性  |      8.0 |  8.8 | My 更强       |
| D5 安全与合规约束落地性            |      5.0 |  9.0 | My 显著更强   |
| D6 规则体系可扩展性与可维护性      |      8.5 |  6.7 | OpenClaw 更强 |
| 参考均分                           |      7.8 |  8.3 | My 小幅领先   |

## D1 — 项目长期演进适配性

### 新功能迭代流程规范

- **OpenClaw**：`✓ 已委托｜9/10`
  - 证据：要求“新增 channels/extensions/apps/docs 时同步更新 `.github/labeler.yml` 和 GitHub labels”，并提供 maintainer PR workflow、`/landpr`、PR template、issue template 等完整流程。
  - 评价：新功能从“代码 → 标签 → PR → 落地”的路径很清楚。
- **My**：`✓ 已委托｜8/10`
  - 证据：要求 route/DTO 变更后同步 `src/main/resources/openapi/documentation.yaml`、运行 `swagger-cli validate`，并在 deploy 受影响时输出 deploy repo checklist。
  - 评价：对 API 后端主路径很完整，但覆盖面更聚焦于后端研发主链路。

### 模块拆分与依赖约束

- **OpenClaw**：`✓ 已委托｜8/10`
  - 证据：明确 `src/`、`extensions/*`、plugin deps 归属、`workspace:*` 禁用、dynamic import 边界、共享 channel 逻辑需覆盖全部 built-in + extension channels。
  - 评价：模块边界清楚，但更多是产品级模块组织，不像强类型架构那样深入签名层。
- **My**：`✓ 已委托｜10/10`
  - 证据：明确 `Routes → Services → Repositories → Database`，要求 invariants 端到端沿 route → service → repository 传播；tagless-final、method-level `using`、feature template 都写得很细。
  - 评价：这是典型“让 agent 几乎无法把层次写乱”的规则设计。

### 技术债务识别与治理路径

- **OpenClaw**：`✓ 已委托｜6/10`
  - 证据：强调不要 speculative bug-fix、不要 `V2` 复制、不要 prototype mutation、要先读依赖源码再下结论。
  - 评价：有技术债防扩散意识，但缺少系统化“触及时如何治理”的迁移路径。
- **My**：`✓ 已委托｜10/10`
  - 证据：明确“prefer radical type-level refactors over conservative patches”；新服务用 typed errors，旧服务“when next modified” 时迁移；要求主动标记误导性命名与 code smell 并沉淀。
  - 评价：这是成熟 AI-native 项目的“渐进式治理手册”写法。

### API / DB / 配置的版本兼容与迁移规则

- **OpenClaw**：`✓ 已委托｜8/10`
  - 证据：release channels、version locations、beta 命名、changelog、GHSA patch/publish、release check 都有明确规则。
  - 评价：偏产品/发布面；对 DB 兼容与 schema 迁移不是主战场。
- **My**：`✓ 已委托｜9/10`
  - 证据：system/tenant migrations 分离、绝不修改旧 migration、environment variables / secrets 明细、OpenAPI 同步要求、deploy repo checklist。
  - 评价：后端 API/DB/config 的演进路径更清晰。

### 存量代码改造与新旧规范衔接

- **OpenClaw**：`✓ 已委托｜7/10`
  - 证据：有 docs i18n 流程、SwiftUI `Observation` 迁移、legacy config / service warning 处理、rebrand/doctor 路径。
  - 评价：有衔接，但不是整份规则的主心骨。
- **My**：`✓ 已委托｜10/10`
  - 证据：整份文件的核心就是“触及旧代码时，把约束上移到类型系统和签名”；同时允许 existing `Either[String, T]` 在下次修改时增量迁移。
  - 评价：这项是 My 的最强长板之一。

### D1 小结

- OpenClaw 擅长的是“让复杂产品持续演化时别失控”。
- My 擅长的是“让成熟后端持续演化时越改越稳”。

## D2 — 规则可执行性与 Agent 遵循适配性

### 规则颗粒度

- **OpenClaw**：`✓ 已委托｜10/10`
  - 证据：大量明确 guardrails，如不要用 `gh issue/pr comment -b "..."`、不要给 `#24643` 加反引号、bug-fix PR 必须满足 4 项 merge gate。
  - 评价：对陌生 agent 非常友好，几乎不留“靠经验补位”的空白。
- **My**：`✓ 已委托｜9/10`
  - 证据：大量 bad/good 代码示例、trusted vs untrusted 路径表、typed errors 规则、Metals 工具切换规范、RAC 该加/不该加的清单。
  - 评价：颗粒度很高，但比 OpenClaw 更偏“原则 + 示例”，不是完全 runbook 化。

### 场景完备性

- **OpenClaw**：`✓ 已委托｜9/10`
  - 证据：覆盖 triage、PR、release、GHSA、移动端、桌面端、macOS 日志、版本号、1Password、插件发布、多 agent 协作等边界场景。
- **My**：`✓ 已委托｜9/10`
  - 证据：覆盖 NoOp 行为、typed errors、trusted/untrusted error path、schema isolation、OpenAPI、deploy handoff、RAC、Metals 使用时机等。

### 跨会话决策一致性

- **OpenClaw**：`✓ 已委托｜9/10`
  - 证据：大量规则给出唯一动作或唯一命令，像“先 `/reviewpr` 再 `/landpr`”“不要 stash / worktree / switch branch”。
- **My**：`✓ 已委托｜8/10`
  - 证据：主原则明确，但像“主动 flag 命名问题”“写入 memory 文件”“当工具返回 5+ operators 再切换命令”的判断仍保留一定裁量空间。

### 规则内部一致性

- **OpenClaw**：`✓ 已委托｜8/10`
  - 证据：整体采用“默认 workflow + maintainer override”解决冲突；主要瑕疵是个别文件长度建议存在 `<700 LOC` 与 `<500 LOC` 两种口径。
- **My**：`✓ 已委托｜8/10`
  - 证据：type-first、typed errors、layering、RAC 基本互相支撑；少数地方同时强调“编译器 acceptance”与“人类最终审查”，哲学上稍偏混合。

### 可验证性

- **OpenClaw**：`✓ 已委托｜10/10`
  - 证据：`pnpm build`、`pnpm tsgo`、`pnpm check`、`pnpm test`、`pnpm release:check`、GHSA re-fetch verify、`npm view` post-check。
- **My**：`✓ 已委托｜9/10`
  - 证据：`./mill compile`、`./mill test`、`./mill checkFormat`、`swagger-cli validate`、Metals compile-file / get-usages 等构成强校验链。

### 规则过载风险

- **OpenClaw**：`✓ 已委托｜7/10`
  - 证据：覆盖面极广，存在常驻上下文过重风险；但通过 skills、外部文档与强分节结构做了分层。
- **My**：`✓ 已委托｜6/10`
  - 证据：大量关键原则、代码示例、工具使用细则都集中在单一大文件中，常驻上下文成本更高。

### 规则可溯因性

- **OpenClaw**：`✓ 已委托｜8/10`
  - 证据：绝大多数规则都附有明确路径、命令、脚本、文档或 label，可回溯到具体 runbook 段落。
- **My**：`✓ 已委托｜8/10`
  - 证据：也有具体文件锚点、工具命令、memory 文件、OpenAPI 路径、deploy repo 位置，方便定位误读点。

### 注意力衰减抗性

- **OpenClaw**：`✓ 已委托｜8/10`
  - 证据：大量 `##` 分节、粗体 guardrails、命令块与显式禁令。
- **My**：`✓ 已委托｜8/10`
  - 证据：有 `CRITICAL RULE`、bad/good 示例、表格、专门章节与路径锚点。

### 防幻觉与自校验能力

- **OpenClaw**：`✓ 已委托｜10/10`
  - 证据：bug-fix PR 必须有 symptom evidence、root cause、implicated path、regression test / manual proof；回答问题时“verify in code; do not guess”。
- **My**：`✓ 已委托｜10/10`
  - 证据：把编译器、Metals、typed errors、OpenAPI validate 与结构化示例一起用作自校验体系。

### 规则与代码现状的同步机制

- **OpenClaw**：`✓ 已委托｜8/10`
  - 证据：规则与 repo 同仓，反复指向具体脚本、skills、release docs、workflow 文件，漂移相对可控。
- **My**：`✓ 已委托｜6/10`
  - 证据：有 compile/test/validate 与 memory 回写要求，但评测对象本身是 gist 托管的 `Claude.md`，同步机制更多依赖人工/agent 纪律。

### D2 小结

- OpenClaw 更像“把 agent 容易犯的错提前写成不可误解的禁令与流程”。
- My 更像“把 agent 容易犯的结构性错交给类型系统与工具链去拦”。

## D3 — 上下文效率与 Agent 认知负荷管理

### 主 Agent 上下文预算效率

- **OpenClaw**：`✓ 已委托｜8/10`
  - 证据：复杂流程可下沉到 skills 或专门文档，主文件保留关键 guardrails。
- **My**：`✓ 已委托｜6/10`
  - 证据：绝大多数关键规范都常驻在单一 `Claude.md` 中，信息密度高但 token 负荷重。

### 规则的层级化组织

- **OpenClaw**：`✓ 已委托｜9/10`
  - 证据：全局 guardrails、PR/issue、build/test、release、GHSA、agent notes、publish fast path 等层次非常明确。
- **My**：`✓ 已委托｜8/10`
  - 证据：Overview → Architecture → Workflow → CI/CD → Important Files 的组织清楚，但仍以单文件大段组织为主。

### 子 Agent 任务委托友好度

- **OpenClaw**：`✓ 已委托｜9/10`
  - 证据：模块树、skills、multi-agent safety、只提交自己改动等规则，天然支持切给并发 agent。
- **My**：`✓ 已委托｜7/10`
  - 证据：feature 分层与结构化示例利于子 agent 做局部理解或局部重构，但缺少并发 Git 协议。

### 规则的结构化程度

- **OpenClaw**：`✓ 已委托｜9/10`
  - 证据：大量路径、命令、模板、label、workflow、脚本入口，结构化程度很高。
- **My**：`✓ 已委托｜9/10`
  - 证据：示例代码、表格、层次图、错误 ADT 与 feature template 都可以被 agent 直接消费。

### 规则简洁性与执行完整度的平衡

- **OpenClaw**：`✓ 已委托｜7/10`
  - 证据：精度高，但低频仓库专属脚枪多，未必适合始终常驻。
- **My**：`✓ 已委托｜8/10`
  - 证据：虽然长，但“类型更强、错误别吞、层次别乱”这些原则面对新场景更具可外推性。

### 规则受众规模适配性

- **OpenClaw**：`✓ 已委托｜10/10`
  - 证据：issue / PR / label / GHSA / multi-agent safety 的写法明显面向大量外部执行者与多种 agent。
- **My**：`✓ 已委托｜8/10`
  - 证据：文件开头就写“guidance to Claude Code”，并配合私有 memory 文件，更像服务少量高能力 agent。

### D3 小结

- OpenClaw 在“让不同 agent 上手时不迷路”方面更强。
- My 在“让单一高能力 agent 深入编码任务”方面更高效，但常驻文本偏重。

## D4 — 已委托领域的工程深度与可持续性

### 技术栈专属规范深度

- **OpenClaw**：`✓ 已委托｜9/10`
  - 证据：TS/ESM、Bun/pnpm、Vitest、Mintlify、launchd、SwiftUI、GHSA、1Password、npm publish 等都深入到具体陷阱。
- **My**：`✓ 已委托｜10/10`
  - 证据：tagless-final、context bounds、opaque types、`NonEmptyList`、EitherT、Doobie、多租户 schema isolation、RAC，都是强类型 Scala 后端深水区规则。

### 已覆盖生命周期阶段的规则完备性

- **OpenClaw**：`✓ 已委托｜9/10`
  - 证据：从 triage / PR / bug-fix verification 到 build / test / release / GHSA 都有规则。
- **My**：`✓ 已委托｜8/10`
  - 证据：覆盖编码、测试、OpenAPI、logging、RAC、CI/CD 与 deploy handoff，但主要集中在 backend 主研发链。

### 配置 / 密钥 / 环境变量管理规范

- **OpenClaw**：`✓ 已委托｜8/10`
  - 证据：credentials 路径、真实数据禁入、release docs、1Password、notary env 都有说明。
- **My**：`✓ 已委托｜9/10`
  - 证据：环境变量、密钥文件、Firebase/GCP service account、K8s job env 都直接枚举出来。

### 跨职责衔接指引

- **OpenClaw**：`✓ 已委托｜8/10`
  - 证据：PR template、issue template、release docs、GHSA patch/publish、评论格式要求，都让 maintainer 容易接力。
- **My**：`✓ 已委托｜9/10`
  - 证据：明确要求 deploy-affecting changes 输出给 `linewise-deploy` 的 checklist，这个 handoff 很成熟。

### 规则抗腐化设计

- **OpenClaw**：`✓ 已委托｜7/10`
  - 证据：有 verify 命令和外链文档，但也夹带较多环境、版本与产品细节，维护成本高。
- **My**：`✓ 已委托｜8/10`
  - 证据：稳定原则层很强，编译/测试/OpenAPI validate 也能帮助发现陈旧规则；但规则文件不在主仓主路径，仍有同步风险。

### 规则降级韧性

- **OpenClaw**：`✓ 已委托｜7/10`
  - 证据：如果 agent 忘了某些发布或 GitHub 脚枪，容易直接误操作。
- **My**：`✓ 已委托｜9/10`
  - 证据：即使遗忘部分细节，只要还记得“类型更强、错误别吞、layering 不乱”，代码质量通常仍有下限保障。

### D4 小结

- OpenClaw 的工程深度主要体现在“复杂产品与维护流程”。
- My 的工程深度主要体现在“强类型后端的长期正确性设计”。

## D5 — 安全与合规约束落地性

### 权限校验与数据隔离规则

- **OpenClaw**：`✗ 未委托`
  - 理由：规则文件要求先读 `SECURITY.md` 对齐 trust model，但主规则正文没有把权限模型/数据隔离编码规则直接委托给 agent。
- **My**：`✓ 已委托｜10/10`
  - 证据：system schema / tenant schema、`/api/org/{tenant}`、Firebase JWT、tenant isolation RAC、security validation tests 都写进主规则。

### 异常处理 / 日志脱敏 / 数据校验的强制规范

- **OpenClaw**：`✓ 已委托｜5/10`
  - 证据：有“不提交真实 phone number / videos / live config values”“外部消息面只发 final reply”等安全卫生规则。
  - 评价：有安全意识，但没有形成统一的异常处理 / 日志脱敏 / 数据校验编码范式。
- **My**：`✓ 已委托｜8/10`
  - 证据：`Never silently swallow errors`、trusted vs untrusted path、typed error、logging level 规范与 security validation tests 组成了较完整的安全编码模型。

### 行业合规编码约束

- **OpenClaw**：`✗ 不适用`
  - 理由：项目定位是通用 AI assistant / open-source agent platform，没有明确 PCI/HIPAA/SOX 等行业合规语境。
- **My**：`✗ 不适用`
  - 理由：项目定位是通用多租户后端 API，规则中没有任何受监管行业边界，不能按行业合规系统强行要求。

### D5 小结

- 在主规则正文层面，My 对“权限、租户隔离、错误处理”的安全落地明显更成熟。
- OpenClaw 的安全更多体现为“维护安全、发布安全、数据卫生安全”，不是后端访问控制安全。

## D6 — 规则体系可扩展性与可维护性

### 新增 / 废弃规则的迭代流程

- **OpenClaw**：`✓ 已委托｜7/10`
  - 证据：复杂流程外置到 skills 和专门文档；新增 `AGENTS.md` 时要求补 `CLAUDE.md` symlink。
  - 评价：有分层与扩展意识，但缺少显式的规则废弃协议。
- **My**：`✓ 已委托｜6/10`
  - 证据：要求新 helper 达成共识后回写 `CLAUDE.md`，并维护 `memory/code_smells.md`；但“规则文件本身怎么退场/版本化”写得较少。

### 目录结构与检索效率

- **OpenClaw**：`✓ 已委托｜9/10`
  - 证据：章节切分细，路径、命令、模板、release docs 与 skills 入口清晰，检索效率很高。
- **My**：`✓ 已委托｜7/10`
  - 证据：结构本身清楚，但主要还是单文件集中承载。

### 规则间一致性与自洽性

- **OpenClaw**：`✓ 已委托｜8/10`
  - 证据：采用“默认 PR_WORKFLOW + maintainer override”收束冲突，整体自洽度高。
- **My**：`✓ 已委托｜7/10`
  - 证据：原则层相互支撑，但同时存在“强制”和“建议”语气混合，较依赖高能力 agent 的自我裁量。

### 多 Agent 并行安全

- **OpenClaw**：`✓ 已委托｜10/10`
  - 证据：明确禁止 `stash` / `autostash`、`worktree`、切分支，并规定 push / commit / commit all 的边界；还明确承认“running multiple agents is OK as long as each agent has its own session”。
- **My**：`✗ 不适用`
  - 理由：按其目标架构与受众，它主要服务高能力主 agent 深入单仓库演进，而非多 agent 并发 Git 协作；因此不因缺少并发 Git 协议扣分。

### D6 小结

- OpenClaw 在“把规则做成可扩展的协作制度”上明显更成熟。
- My 在这方面不是没意识，而是目标场景压根不要求它成为多 agent 开源协作协议。

# Part 3 — 横向对比结论

## 核心优劣势

### OpenClaw

**优势：**

- 最懂 AI 会如何在真实 GitHub / Git / 发布链路里误操作
- bug-fix 幻觉防护、发布 runbook、GHSA 处理、多 agent Git 安全都很成熟
- 对外部贡献者 agent 友好，对陌生 session 冷启动友好

**短板：**

- 低频规则偏多，常驻上下文成本高
- 部分关键能力依赖外部文档或 skills，主文件本体较胖
- 后端访问控制 / 数据隔离类安全规则不在主正文核心位置

### My

**优势：**

- 最懂如何让 AI 在强类型后端里持续写对代码
- 类型系统、错误模型、分层边界、多租户安全与迁移策略高度统一
- 面对成熟存量代码，能把“越改越稳”写成方法论而不是口号

**短板：**

- 对多 agent Git 并发协作的显式护栏不足
- 对高风险操作的审批型 guardrails 较少
- 规则文件与仓库主路径分离时，存在同步漂移风险

## 适用场景差异

- **成熟强类型后端、存量代码多、需要高频重构与签名级治理**：优先参考 My。
- **开源仓库、外部贡献者多、并发 agent 多、发布 / triage / GHSA 压力大**：优先参考 OpenClaw。

## 哪份规则对 AI 代理执行友好度更高

- 仅看“写代码、改代码、局部重构、保持架构正确性”：**My 更友好**。
- 看“真实仓库全流程落地、维护、防误操作、并发协作”：**OpenClaw 更友好**。

## 最关键的落地风险提示

- OpenClaw 的主要风险不是规则不够细，而是 **规则太细、太广、太依赖当前仓库运行现实**。
- My 的主要风险不是架构不够强，而是 **协作安全、审批护栏和规则同步机制略弱**。

# Part 4 — 制定者能力画像对比（D7）

| 能力维度                         | OpenClaw 制定者 | My 制定者        | 核心差异                                           |
| -------------------------------- | --------------- | ---------------- | -------------------------------------------------- |
| 架构设计与技术前瞻性             | `专家`          | `专家`           | 前者偏产品与平台广度，后者偏后端与类型系统深度     |
| 大型项目工程化管控能力           | `专家`          | `资深`           | OpenClaw 明显具备 maintainer / operator 级治理能力 |
| AI 编码代理认知与应用深度        | `专家`          | `专家`           | 一个擅长防误操作，一个擅长防结构性错误             |
| 安全风险体系化防控能力           | `资深`          | `专家`           | OpenClaw 强在维护安全，My 强在访问控制与租户隔离   |
| 技术债务治理与可持续演进能力     | `资深`          | `专家`           | My 的渐进式迁移策略更完整                          |
| 规则工程能力（Rule Engineering） | `专家`          | `专家`           | 两者都是专家，但采用不同方法论                     |
| 开源社区规模化治理能力           | `专家`          | `不适用，不降级` | 这是 OpenClaw 的天然主场，不是 My 的目标需求       |

## 能力画像解读

### OpenClaw 制定者

- 更像 **专家级 maintainer-operator**。
- 强项不是“写出更学术的架构原则”，而是“把 agent 最容易闯祸的真实仓库动作做成可执行护栏”。
- 即使某些能力超出其项目最低需求，例如显式多 agent Git 安全协议，也反映出很强的前瞻性与工程视野。

### My 制定者

- 更像 **专家级 backend architect**。
- 强项不是“把所有外围流程都写进规则”，而是“把正确性前移到类型、签名、错误模型和分层边界”。
- deploy impact reporting、touch-to-migrate、code smell 持久化，也说明制定者对职责边界与长期演进有非常清醒的认识。

# Part 5 — Agent 适配性分析

## OpenClaw 的目标架构适配优势

- 适合 **多 agent 并发 + 大量外部贡献者 agent + maintainer 审核** 的执行架构。
- 它把多人 / 多 session / 多工具环境下最危险的动作写成了显式协议：Git、GitHub、release、GHSA、评论、版本号、发布验证。
- 对“冷启动 agent”尤其友好：即使这个 agent 完全不熟仓库，只要照着规则走，也不容易在高风险流程里犯大错。

## OpenClaw 的适配不足

- 对纯编码任务来说，常驻噪声偏大。
- 大量仓库专属脚枪规则不适合直接迁移到别的项目。
- 如果维护成本跟不上，这类 runbook 型规则比原则型规则更容易局部过时。

## My 的目标架构适配优势

- 适合 **高能力主 agent 深入一个成熟后端仓库长期演进** 的架构。
- 在这类场景里，agent 最需要的不是“如何发 GH 评论”，而是“如何不把 type boundary、tenant isolation、error model 写坏”。
- My 恰恰把这件事写到了非常深的位置：签名、类型、工具、分层、OpenAPI、deploy handoff 彼此呼应。

## My 的适配不足

- 如果团队进入多 agent 并发协作、多人提交、频繁发布或 GHSA 压力期，外围护栏不够强。
- 它更依赖“高能力 agent + 强编译器工具链 + 人类反馈闭环”；一旦三者缺一，收益会比 OpenClaw 掉得更快。

## 推荐场景

- **0 → 1 的开源 AI-native 平台**：优先参考 OpenClaw。
- **1 → N 的成熟强类型 AI-native 后端**：优先参考 My。
- **最佳组合拳**：My 负责编码骨架与结构性正确性；OpenClaw 负责验证、发布、协作与高风险流程护栏。

# Part 6 — AI 诚实自评（D8）

## 场景 A：成熟的 AI-native 项目

如果我要进入一个 **已有大量存量代码、架构历史复杂、多代模型已反复改造** 的 AI-native 项目，而我只能参考一份方法论来从零写规则，我会选 **My**。

### 为什么我选它

- 我最怕的不是流程不清，而是在旧代码里“局部看对、全局写错”。
- My 最强的地方，是把这种风险前移到 **类型、签名、分层、错误模型、编译器与工具链**。
- 它让我在复杂存量系统里改代码时，有更高概率“越改越稳”，而不是只会流程上不犯错。

### 我会失去什么

- 我会失去 OpenClaw 那套成熟的 **多 agent Git 安全协议**。
- 我会失去 **bug-fix 证据门槛** 这种很强的防幻觉护栏。
- 我会失去大量面向 release / GHSA / GitHub 维护的现成 runbook。

### 我会在哪些场景下感到不安

- 当项目进入多人并发协作、频繁发版、频繁 triage 时，我会明显更不安。
- 因为 My 更像“写对代码的规则”，不是“维护全流程的作战手册”。

### 如果我可以从落选者里偷 3 个设计决策

我会从 OpenClaw 偷这 3 个：

1. **bug-fix 必须给出 symptom evidence / root cause / implicated path / regression proof**
2. **多 agent Git 并发安全协议**：不准乱 stash、乱切分支、乱动 worktree，只提交自己的改动
3. **高风险动作审批 guardrails**：publish、release、dependency patch、GHSA 这类动作必须明确批准

## 场景 B：全新的 AI-native 项目

如果我要进入一个 **从第一行代码开始，规则和代码一起生长** 的全新 AI-native 项目，而我只能参考一份方法论来从零写规则，我会选 **OpenClaw**。

### 为什么我选它

- 在 0 → 1 阶段，我最怕的是“规则太抽象，导致不同 agent 会各自脑补”。
- OpenClaw 的写法极其防御性：动作边界清楚、脚枪写明、协作协议明确、发布与 GH 流程都能直接照做。
- 对我这个执行者来说，这比抽象原则更能降低早期失误率。

### 我会失去什么

- 我会失去 My 那种强类型后端特有的 **结构性正确性压强**。
- 一旦代码库变大，我会更担心“规则记住了，但架构 invariant 没被编译器强制”。

### 我会在哪些场景下感到不安

- 当项目后来演化成大型强类型后端，需要大规模签名重构和历史包袱治理时，我会觉得 OpenClaw 方法论不够深。

### 如果我可以从落选者里偷 3 个设计决策

我会从 My 偷这 3 个：

1. **radical type-level refactor**：优先把 invariant 放进类型和签名，而不是运行时补丁
2. **trusted vs untrusted path 错误策略**：内部失败要 fail fast，外部输入要返回可行动错误
3. **touch-to-migrate + code smell ledger**：一旦碰到旧代码，就顺手把旧约束升级，并把坏味道沉淀为长期记忆

## 场景 C：综合判断

我在两个场景里选了不同的文件，这并不意味着“两份文件各有优劣”这种空话，而意味着：

- **OpenClaw** 代表的是一种更适合 **0 → 1 协作型 AI-native 工程** 的规则工程方法论。
- **My** 代表的是一种更适合 **1 → N 演进型 AI-native 工程** 的规则工程方法论。
- 同时，两者都不是“只适用于自己主场”的窄规则：OpenClaw 的协作护栏完全值得被成熟项目借走；My 的结构性正确性方法，也完全值得被新项目提前引入。

# Part 7 — 评测框架公平性自审

## 我的结论

我认为这份评测提示词 **总体上是在尽力公平**，但仍然对 **OpenClaw 存在轻度结构性偏向**。

这不是因为它在打分规则上作弊，而是因为：它把 **多 agent 并发安全、开源社区治理、流程化协作防错** 显式建成了独立维度或高权重子项，而这些恰好是 OpenClaw 最外显、最容易被量化的强项。

## 1. 维度选择偏差

- D3、D6、D7 中关于多 agent、安全协作、开源治理的设计，非常贴合 OpenClaw 的能力结构。
- My 最独特的优势——**把编译器和类型系统本身当成规则执行器**——虽然被纳入 D2 / D4，但更多是作为子项出现，而不是被提升为独立主维度。
- 因此，框架更容易奖励“看得见的治理广度”，而不那么容易奖励“看不见但极有效的类型级约束深度”。

## 2. 适用性规则的非对称效应

- 适用性排除机制显著缓解了这种偏差。
- 它避免了 My 因为不是多 agent 并发仓库而被硬扣 D6 的并发安全分，也避免了双方被强行拖入行业合规赛道。
- 所以这个框架并没有把结论预先写死；它只是轻微偏向更擅长“显式治理”的一方。

## 3. 信息引导

- 前提描述里，OpenClaw 带着“原生式、多 agent、250K+ stars、1000+贡献者”的高势能标签出场，这天然会给评测者造成 prestige bias。
- 相比之下，My 的叙述更偏“渐进演化、作者自用”，容易被低估其规则工程含金量。
- 这类叙事密度差异，会微妙影响评测者的心理预设。

## 4. 我的最终判定

- 如果非要二选一，我不会说“这份框架完全公平”。
- 我会说：**它是一个认真设计过、尽量做了适用性校正，但仍对 OpenClaw 轻度有利的框架。**
- 受益机制是：框架显式奖励了 OpenClaw 最擅长的协作治理、防误操作与社区规模化能力；而 My 那种更隐性的“编译器即规则引擎”优势，虽被纳入评测，但没有获得同等显著的结构位置。

# 最终结论

- **OpenClaw** 更像一份面向复杂开源仓库与多 agent 并行协作的 **AI 维护作战手册**。
- **My** 更像一份面向成熟强类型后端长期演进的 **AI 编码与架构治理宪法**。
- 如果你最缺的是“别让 agent 在真实仓库里闯祸”，优先借鉴 OpenClaw。
- 如果你最缺的是“让 agent 在复杂后端里稳定写对代码并持续治理旧代码”，优先借鉴 My。
- 如果目标是构建长期可持续的 AI-native 工程体系，最优解往往不是二选一，而是：
  - **用 My 约束编码骨架与结构性正确性**
  - **用 OpenClaw 约束验证、协作、发布与高风险流程**
