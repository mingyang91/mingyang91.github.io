---
title: AI编码代理规则文件全维度横向对比评测报告
date: 2026-03-13 12:00:00
tags:
  - AI
  - Programming
  - Software Engineering
  - Agent
---

# AI编码代理规则文件全维度横向对比评测报告

## 核心前提

两个项目都是 **AI-native 项目**——代码由AI编码代理编写、修改、阅读和调试，但 AI-native 成熟度路径不同：

- **渐进式（Linewise）**：多租户后端API服务（Scala 3 / http4s），历经多代模型演进（Claude 3.7→4.6），早期人类参与度约50%，随模型能力提升逐步降低人类介入，规则文件随项目一起演化积累。主要服务作者自己的agent。
- **原生式（OpenClaw）**：开源自主AI代理平台（TypeScript / Node.js），从第一行代码起即由agent编写，创建者使用多agent并行工作流（5-10个agent并发），规则文件从项目诞生之初即作为agent的执行规范存在。250K+ stars、1000+贡献者，规则需同时服务创建者和大量外部贡献者的agent。

评测对象：
1. [OpenClaw AGENTS.md](https://github.com/openclaw/openclaw/blob/main/AGENTS.md)
2. [My CLAUDE.md](https://gist.github.com/mingyang91/475a9750c5609ff5dfe59a5de1a09b6e)

---

## Part 1 — 基础画像

### OpenClaw `AGENTS.md`

| 维度 | 描述 |
|------|------|
| **项目定位** | 开源自主AI代理平台（TypeScript / Node.js），跨平台（CLI、macOS app、iOS/Android、Web），250K+ stars |
| **目标架构** | 多Agent并行工作流（5-10 agent并发），共享同一仓库 |
| **规则受众** | 创建者的多个并发agent + 大量外部贡献者的agent（不同模型、不同能力） |
| **核心设计理念** | **操作安全与流程一致性** — 在多agent并发、大规模贡献者场景下确保git操作安全、PR流程一致、发布流程可靠 |
| **覆盖范围** | 仓库结构、PR/Issue管理（auto-close标签、合并门控）、多agent Git安全协议、构建/测试/Lint命令、编码风格（TypeScript）、发布流程（npm/macOS/beta）、文档管理（Mintlify/i18n）、安全咨询（GHSA）、平台运维（exe.dev VM、macOS签名）、插件生态管理 |
| **结构特征** | 扁平化列表结构 — 以操作指令和注意事项为主，较少代码示例，更多是"做X时要Y"的规则条目。覆盖面广但每个领域的深度较浅 |
| **Token估算** | ~5000-6000 tokens，覆盖面广但单条规则较短 |

### My `CLAUDE.md`

| 维度 | 描述 |
|------|------|
| **项目定位** | 多租户后端API服务，企业级SaaS（Scala 3 / http4s / cats-effect），AI驱动的文档管理、RAG、视频SOP生成 |
| **目标架构** | 单主Agent + 按需子Agent（Explore/Plan等由Claude Code派生） |
| **规则受众** | 单一开发者的agent（主要是Claude），偶尔人类直接阅读 |
| **核心设计理念** | **类型安全最大化** — 将工程约束编码进类型系统，让编译器成为最终验证者。"如果编译通过，就是正确的。" 以编译器驱动的激进重构取代保守补丁 |
| **覆盖范围** | 架构模式（tagless final）、代码风格（for-comprehension、EitherT/OptionT）、错误处理（ADT enum）、类型系统（opaque types、NonEmptyList）、测试策略、CI/CD流程、部署衔接、日志规范、运行时断言（RAC）、代码气味追踪、多租户隔离、工具偏好（Metals MCP） |
| **结构特征** | 高度结构化 — 大量代码示例（正反对比）、决策表格、层级清晰的标题体系。信息密度极高，深度聚焦于"如何写好Scala代码" |
| **Token估算** | ~6000-7000 tokens，信息密度高 |

**核心差异**：两份文件代表了AI-native规则工程的两种典型范式：

- **OpenClaw**: **广度优先** — 覆盖从编码到发布到运维的完整操作流程，在多agent并发安全方面有独到设计，但单条规则的颗粒度和深度较浅
- **My**: **深度优先** — 在一个技术领域（Scala后端开发）做到极致，规则可执行性极高，几乎每条规则都有正反代码示例和边界说明

---

## Part 2 — 量化评测表

### D1 项目长期演进适配性

| 子项 | OpenClaw | My |
|------|----------|----------|
| **新功能迭代流程规范** | ✓ 已委托 — **7/10** | ✓ 已委托 — **7/10** |
| **模块拆分与依赖约束** | ✓ 已委托 — **7/10** | ✓ 已委托 — **8/10** |
| **技术债务识别与治理路径** | ✗ 未委托 — 无技术债务治理相关条目，推定由人类主导 | ✓ 已委托 — **9/10** |
| **API/DB/配置的版本兼容与迁移规则** | ✗ 未委托 — 版本管理仅涉及发布版本号位置列表，无API/DB迁移规则 | ✓ 已委托 — **8/10** |
| **存量代码改造与新旧规范衔接** | ✗ 不适用 — 原生AI项目，从第一行代码起即由agent编写，无存量遗留代码 | ✓ 已委托 — **9/10** |

**评分依据：**

- **OpenClaw 新功能迭代 (7)**：有明确的PR工作流引用（`.agents/skills/PR_WORKFLOW.md`），commit规范（`scripts/committer`），但新功能的架构决策指引较弱。
- **My 新功能迭代 (7)**：有明确的"Adding New Routes"流程（更新OpenAPI spec → swagger-cli validate → 遵循auth模式），Feature Module组织结构清晰。但缺少新feature的端到端迭代模板。
- **OpenClaw 模块拆分 (7)**：项目结构清晰（`src/`, `extensions/*`, `docs/`），插件依赖隔离规则明确（*"Keep plugin-only deps in the extension `package.json`"*）。但核心模块间的依赖约束未显式规定。
- **My 模块拆分 (8)**：严格的分层架构（Routes→Services→Repositories→Database）、tagless final依赖注入、feature模块标准结构、SDK选择优先级。原文：*"Each feature module follows a consistent structure"*
- **My 技术债务 (9)**：业界罕见的体系化方案 — code smell追踪系统（`code_smells.md`，FIFO最多10条）、*"Migrate when file is touched — no hesitation"* 的渐进式迁移策略、编译器驱动的迭代修复范围（*"Scope follows the compiler iteratively"*）。原文：*"Existing `Either[String, T]` services migrate the **whole service** to ADT errors when the file is modified for any reason"*
- **My API/DB迁移 (8)**：Flyway迁移系统有明确规范（*"Never modify existing migration files; always create new versioned files"*），系统/租户双轨迁移，启动时自动运行。外部名称变更有迁移影响提示要求。
- **My 存量代码改造 (9)**：*"Migrate when file is touched"* 策略 + ADT error enum渐进式迁移 + 编译器驱动范围扩展，是存量代码治理的教科书级方案。

**D1维度得分：**
- **OpenClaw：7.0/10**（2项适用已委托）
- **My：8.2/10**（5项均适用已委托）

---

### D2 规则可执行性与Agent遵循适配性

| 子项 | OpenClaw | My |
|------|----------|----------|
| **规则颗粒度** | ✓ 已委托 — **6/10** | ✓ 已委托 — **9/10** |
| **场景完备性** | ✓ 已委托 — **5/10** | ✓ 已委托 — **9/10** |
| **跨会话决策一致性** | ✓ 已委托 — **5/10** | ✓ 已委托 — **9/10** |
| **规则内部一致性** | ✓ 已委托 — **7/10** | ✓ 已委托 — **8/10** |
| **可验证性** | ✓ 已委托 — **7/10** | ✓ 已委托 — **9/10** |
| **规则过载风险** | ✓ 已委托 — **7/10** | ✓ 已委托 — **7/10** |
| **规则可溯因性** | ✓ 已委托 — **5/10** | ✓ 已委托 — **8/10** |
| **注意力衰减抗性** | ✓ 已委托 — **6/10** | ✓ 已委托 — **9/10** |
| **防幻觉与自校验能力** | ✓ 已委托 — **6/10** | ✓ 已委托 — **9/10** |
| **规则与代码现状同步机制** | ✓ 已委托 — **5/10** | ✓ 已委托 — **7/10** |

**评分依据：**

- **OpenClaw 颗粒度 (6)**：多数规则是操作性指令（"Run X command"），易于遵循。但架构/代码质量规则颗粒度低，如 *"Add brief code comments for tricky or non-obvious logic"* 缺乏"什么算tricky"的判断标准。*"Aim to keep files under ~700 LOC; guideline only"* 缺乏何时违反指南的边界说明。
- **My 颗粒度 (9)**：几乎每条规则都有`// BAD` + `// GOOD`代码对比示例、边界说明表格、决策树。例如错误处理规则不仅说"不要静默吞错"，还列出了具体的禁止模式（`.toOption`, `.getOrElse(defaultValue)` 等）和例外情况（`pageSize.getOrElse(10) // OK`）。Trusted vs Untrusted路径有完整的决策表。NoOp实现按data-related/data-unrelated分类说明。
- **OpenClaw 场景完备性 (5)**：主要覆盖正常操作路径，异常路径覆盖不足。例如multi-agent安全规则覆盖了"当看到不认识的文件"（*"keep going; focus on your changes"*），但未覆盖"两个agent同时修改同一文件"的冲突解决。PR合并门控对bug-fix PR有完整的4步验证，但对feature PR缺乏对等规范。
- **My 场景完备性 (9)**：规则覆盖了正常/异常/边界场景。例如for-comprehension规则区分了：终端位置match（OK）、中间位置match（BAD）、中间位置EitherT（data-related vs data-unrelated）、多个Option链（EitherT + local enum）。NoOp模式区分了data-related和data-unrelated两种场景及其不同返回策略。
- **OpenClaw 跨会话一致性 (5)**：存在较多依赖隐含上下文的表述。*"Add brief code comments for tricky or non-obvious logic"* — 不同agent对"tricky"的理解不同。*"Keep files concise; extract helpers instead of 'V2' copies"* — "concise"的标准模糊。*"guideline only (not a hard guardrail)"* 给了agent过多自由裁量空间。
- **My 跨会话一致性 (9)**：规则高度确定性，几乎不使用主观判断词。*"Never modify existing migration files"*、*"Migrate when file is touched — no hesitation"*、`// BAD` + `// GOOD`模式使不同session的agent做出相同决策。决策表（Trusted vs Untrusted、data-related vs data-unrelated）消除了歧义。
- **OpenClaw 可验证性 (7)**：`pnpm check`（Oxlint+Oxfmt）、`pnpm build`（TypeScript类型检查 + `[INEFFECTIVE_DYNAMIC_IMPORT]`警告检测）、Vitest 70%覆盖率门槛、`prek install`（pre-commit hooks与CI同检查）。动态语言下的验证手段已较完善。
- **My 可验证性 (9)**：核心规则可由编译器验证（类型系统、opaque types、NonEmptyList签名）。原文：*"The compiler is the last line of defense. If a refactor compiles, it's correct."* `./mill checkFormat`验证格式，RAC运行时验证关键路径断言。规则设计充分利用了静态类型语言的结构性优势。
- **OpenClaw 注意力衰减抗性 (6)**：使用了粗体标记（*"**Multi-agent safety:**"* 多次出现），但整体结构扁平，规则按添加顺序排列而非按重要性分层。长列表中关键规则（如multi-agent safety）与琐碎规则（如 *"Vocabulary: 'makeup' = 'mac app'"*）混排，注意力权重分配不均。
- **My 注意力衰减抗性 (9)**：大量使用结构化标记 — 决策表格、`// BAD` / `// GOOD`代码块对比、粗体标注关键规则（*"**CRITICAL RULE:**"*、*"**Forbidden patterns:**"*）、枚举列表。规则按主题层级组织，关键约束在每个相关章节重复强化。
- **OpenClaw 防幻觉 (6)**：有具体路径（`src/cli/progress.ts`、`src/terminal/palette.ts`），有具体命令（`scripts/committer`），但代码架构层面缺少可验证的锚点。*"When answering questions, respond with high-confidence answers only: verify in code; do not guess"* 是好的元指令但缺乏验证机制。
- **My 防幻觉 (9)**：大量具体锚点 — 文件路径（`core/domain/Ids.scala`、`core/domain/Types.scala`）、类名（`SOPService`、`EitherT`）、确切的方法签名模式。Tool Preferences表明确指引何时用Metals MCP验证类型推断。代码示例本身就是可编译的Scala代码，agent可以通过编译验证理解是否正确。
- **OpenClaw 代码同步 (5)**：规则引用了大量具体路径和工具名，但无同步机制。版本位置列表（package.json、Info.plist等多处）需要手动维护。规则文件本身的更新依赖人类发现不一致。
- **My 代码同步 (7)**：规则深度绑定语言特性（Scala 3.6 aggregate bounds syntax、opaque types），与代码现状耦合度高。编译器本身提供了隐含的同步检测——过时的类型约束规则会导致编译失败。Code smell追踪系统作为手动同步手段补充。

**D2维度得分：**
- **OpenClaw：5.9/10**
- **My：8.3/10**

---

### D3 上下文效率与Agent认知负荷管理

| 子项 | OpenClaw | My |
|------|----------|----------|
| **主Agent上下文预算效率** | ✓ 已委托 — **5/10** | ✓ 已委托 — **7/10** |
| **规则的层级化组织** | ✓ 已委托 — **4/10** | ✓ 已委托 — **8/10** |
| **子Agent任务委托友好度** | ✗ 不适用 — 多agent并行架构下无主/子关系，各agent独立运行 | ✓ 已委托 — **7/10** |
| **规则的结构化程度** | ✓ 已委托 — **6/10** | ✓ 已委托 — **9/10** |
| **简洁性与执行完整度的平衡** | ✓ 已委托 — **6/10** | ✓ 已委托 — **7/10** |
| **规则受众规模适配性** | ✓ 已委托 — **7/10** | ✓ 已委托 — **8/10** |

**评分依据：**

- **OpenClaw 上下文预算 (5)**：包含大量低频操作规则（1Password publish流程、GHSA patch步骤、exe.dev VM操作、macOS签名）常驻上下文，这些可能一个月才用一次。Skill引用（`PR_WORKFLOW.md`、`mintlify skill`、`1password skill`）是按需加载的良好设计，但主文件仍然包含太多应为skill的内容。
- **My 上下文预算 (7)**：信息密度极高，token效率好——每个token都承载有效信息。Memory系统（`MEMORY.md`索引 + 独立记忆文件）将运行时状态从规则中分离，这是好的设计。但核心规则无按需加载机制——所有规则每次会话都需加载。
- **OpenClaw 层级化 (4)**：基本扁平结构，规则按话题分组但层级不深。关键规则（multi-agent safety、PR truthfulness）与操作细节（NPM + 1Password、exe.dev VM ops）处于同一层级。无"全局强制约束"与"领域特定规范"的显式区分。Agent-Specific Notes部分是最混杂的——从语义约束到特定工具用法混排。
- **My 层级化 (8)**：清晰的三层结构 — 哲学层（Refactoring Philosophy）→ 架构模式层（Tagless Final、Multi-Tenancy、Error Model）→ 具体规则层（Code Style、Logging、RAC）。每层内部有明确的子标题。全局约束（*"Fail Fast"*、type safety）与领域特定规范（RAG、Video、MCP）有清晰边界。
- **My 子Agent委托 (7)**：Feature Module的独立性使局部搜索/理解任务可以只加载相关模块的规则。分层架构为子Agent提供清晰的搜索范围。但规则文件本身未按模块切分。
- **OpenClaw 结构化 (6)**：命令列表格式化良好，PR合并门控是结构化的4步清单。但大量规则是散文形式的注意事项，需要agent理解语境才能应用。
- **My 结构化 (9)**：表格（Trusted vs Untrusted、Tool Preferences）、代码块对比、枚举列表、决策树——agent可直接将这些结构用作决策查表。例如NoOp返回值规则用data-related/data-unrelated二分法，agent不需要"理解"规则的意图，只需分类即可。
- **OpenClaw 受众适配 (7)**：面向多样化agent群体，规则确实更显式化（具体命令、完整路径）。但未针对不同能力的agent分层——强agent和弱agent看到的是同一份规则。multi-agent safety规则是对多执行者场景的显式回应，这是加分项。
- **My 受众适配 (8)**：面向单一执行者（Claude），可以依赖Claude的Scala知识作为隐含共识，规则聚焦于"Claude可能犯的Scala错误"。Tool Preferences表直接针对Claude Code的Metals MCP工具。Memory系统为跨会话一致性提供了持久化机制。

**D3维度得分：**
- **OpenClaw：5.6/10**（5项适用已委托）
- **My：7.7/10**（6项均适用已委托）

---

### D4 已委托领域的工程深度与可持续性

| 子项 | OpenClaw | My |
|------|----------|----------|
| **技术栈专属规范深度** | ✓ 已委托 — **5/10** | ✓ 已委托 — **10/10** |
| **已覆盖生命周期阶段的规则完备性** | ✓ 已委托 — **7/10** | ✓ 已委托 — **8/10** |
| **配置/密钥/环境变量管理规范** | ✓ 已委托 — **7/10** | ✓ 已委托 — **8/10** |
| **跨职责衔接指引** | ✓ 已委托 — **5/10** | ✓ 已委托 — **9/10** |
| **规则抗腐化设计** | ✓ 已委托 — **4/10** | ✓ 已委托 — **8/10** |
| **规则降级韧性** | ✓ 已委托 — **6/10** | ✓ 已委托 — **8/10** |

**评分依据：**

- **OpenClaw 技术栈深度 (5)**：TypeScript相关规则较为通用——*"Prefer strict typing; avoid `any`"*、*"Never add `@ts-nocheck`"*。有少量深入点：dynamic import guardrail（`.runtime.ts`边界）、prototype mutation禁令、Oxlint/Oxfmt配置。但缺少TypeScript特有的高级模式指引（条件类型、模板字面量类型、branded types、discriminated unions等）。tool schema guardrails（避免`Type.Union`、`anyOf`/`oneOf`/`allOf`）是针对特定集成的有深度规则。
- **My 技术栈深度 (10)**：这是本评测中最突出的单项。规则深入到Scala 3 / cats-effect / http4s的惯用模式层面：tagless final的summoner/factory模式、EitherT/OptionT的lifter链（`foldF`/`subflatMap`/`semiflatMap`/`fromOptionF`）、Scala 3.6 aggregate context bounds语法（`{A, B, C}`）、opaque types在multi-layer propagation中的行为（*"`.toString` over `.value.toString`"*）。正反对比示例直接展示了Scala特有的陷阱和惯用写法。NoOp模式的data-related/data-unrelated分类是对cats-effect生态的深度理解。这不是通用OOP/FP原则的堆砌，而是高度Scala-specific的编码指南。
- **OpenClaw 生命周期完备性 (7)**：从编码到发布流程都有覆盖——测试（Vitest + coverage）、CI（pre-commit hooks = CI checks）、发布（npm/macOS/beta三通道）、changelog管理。Bug-fix PR有4步验证门控。但编码阶段的代码质量规则深度不足。
- **My 生命周期完备性 (8)**：编码阶段极度完备。测试有 *"What TO test" vs "What NOT to test"* 的明确指引。CI/CD有branch→tag映射。部署有影响报告checklist。缺少的是运行时监控/告警规则和事故响应流程，但可合理推定为未委托。
- **OpenClaw 配置管理 (7)**：*"Never commit or publish real phone numbers, videos, or live configuration values"* 是显式的安全规则。配置管理分散在多个章节——`openclaw config set`、环境变量（`~/.profile`）、1Password密钥管理。发布签名密钥明确声明 *"managed outside the repo"*。
- **My 配置管理 (8)**：完整的环境变量列表（含fallback值）、密钥文件路径（`secrets/`）、HOCON配置层级。明确区分了必需密钥和可选配置。
- **OpenClaw 跨职责衔接 (5)**：*"Installers served from `https://openclaw.ai/*`: live in the sibling repo `../openclaw.ai`"* 提到了跨仓库依赖，但缺少变更影响传递的协议。发布流程的跨步骤衔接有具体步骤但缺少"如果某步失败"的衔接指引。
- **My 跨职责衔接 (9)**：**Deploy impact reporting** 是亮点——明确要求agent在代码变更涉及部署影响时输出checklist（*"New environment variable → add to ConfigMap"*、*"New sidecar container → add container spec to Deployment manifest"*）。跨仓库协作（`linewise-deploy/overlays/`）有清晰的衔接协议。
- **OpenClaw 抗腐化 (4)**：规则高度耦合当前工具链版本（具体的npm命令、1Password路径、exe.dev SSH方式）。版本位置列表（6+ 处 Info.plist/package.json）需要手动维护。无抗腐化机制——规则过时不会触发任何告警。Skill引用允许细节外置，但主文件中仍有大量易变细节。
- **My 抗腐化 (8)**：原则层（type safety philosophy、flat for-comprehensions、ADT errors）与细节层（具体文件路径、方法签名示例）自然分离。原则层稳定——Scala 3的类型系统几年不会变；细节层通过 *"Proactive naming review"* 和code smell追踪系统提供手动同步。编译器本身是最强的抗腐化机制——过时的类型约束规则会导致编译失败，从而被发现。
- **OpenClaw 降级韧性 (6)**：multi-agent safety规则相对独立，即使部分遗忘，其他规则仍能独立生效。但PR合并门控的降级风险较高——如果agent只记住了 *"run `/landpr`"* 而忘记了4步验证，可能合并不合格的PR。格式化/lint规则有CI兜底（`prek install`），提供了降级保护。
- **My 降级韧性 (8)**：规则体系有清晰的层级——即使agent只遵循了"类型安全最大化"和"不要静默吞错"两条原则，代码质量仍有基本保障。编译器作为兜底——即使agent忽略了EitherT用法规范，类型不匹配仍会被编译器捕获。Code smell追踪作为延迟修复的安全网。

**D4维度得分：**
- **OpenClaw：5.7/10**
- **My：8.5/10**

---

### D5 安全与合规约束落地性

| 子项 | OpenClaw | My |
|------|----------|----------|
| **权限校验与数据隔离规则** | ✓ 已委托 — **6/10** | ✓ 已委托 — **8/10** |
| **异常处理/日志脱敏/数据校验** | ✓ 已委托 — **5/10** | ✓ 已委托 — **9/10** |
| **行业合规编码约束** | ✗ 未委托 — 两项目均无行业合规特定编码约束 | ✗ 未委托 — 同上 |

**评分依据：**

- **OpenClaw 权限/隔离 (6)**：安全规则分散——SECURITY.md引用（*"read `SECURITY.md` to align with OpenClaw's trust model"*）、credentials管理（`~/.openclaw/credentials/`）、*"Never commit or publish real phone numbers"*。GHSA处理流程完整。但缺少应用层数据隔离的编码规范。
- **My 权限/隔离 (8)**：多租户schema隔离有完整描述（system schema + tenant schemas）。RAC建议在关键路径验证租户隔离（*"assert search_path matches expected tenant schema before writes"*）。权限模型有专门的Permission模块（JSONB expression tree）。Firebase JWT认证是全局强制的。
- **OpenClaw 异常/日志/校验 (5)**：bug-fix PR的验证门控是质量把关而非编码层面的异常处理规范。*"respond with high-confidence answers only: verify in code; do not guess"* 是元规则而非编码规范。缺少TypeScript异常处理、错误传播、日志规范的编码指引。
- **My 异常/日志/校验 (9)**：**Fail Fast** 规则是安全层面的核心——*"Never silently swallow errors"* 有完整的Forbidden Patterns列表和Trusted/Untrusted路径决策表。ADT error enums强制exhaustive pattern matching（编译器保证所有错误变体都被处理）。Logging规范有明确的log level指引。

**D5维度得分（排除不适用子项）：**
- **OpenClaw：5.5/10**（2项适用已委托）
- **My：8.5/10**（2项适用已委托）

---

### D6 规则体系可扩展性与可维护性

| 子项 | OpenClaw | My |
|------|----------|----------|
| **新增/废弃规则的迭代流程** | ✓ 已委托 — **5/10** | ✓ 已委托 — **7/10** |
| **目录结构与检索效率** | ✓ 已委托 — **6/10** | ✓ 已委托 — **7/10** |
| **规则间一致性与自洽性** | ✓ 已委托 — **6/10** | ✓ 已委托 — **8/10** |
| **多Agent并行安全** | ✓ 已委托 — **8/10** | ✗ 不适用 — 单主Agent架构，无多Agent并行需求 |

**评分依据：**

- **OpenClaw 迭代流程 (5)**：Skill系统（`.agents/skills/`）允许外置规则。*"When adding a new `AGENTS.md` anywhere in the repo, also add a `CLAUDE.md` symlink"* 是分布式规则的约定。但规则的生命周期管理（何时废弃、如何审查过时条目）缺失。规则文件呈增量追加模式。
- **My 迭代流程 (7)**：Memory系统（`MEMORY.md`索引 + 独立记忆文件）提供了持久化反馈闭环——feedback类型记忆直接影响后续会话行为。Code smell list的FIFO机制（max 10 entries）是有节制的迭代管理。
- **OpenClaw 内部一致性 (6)**：multi-agent safety规则内部一致（6条规则互不矛盾）。但存在一些张力：文件大小建议在两处不一致（~700 LOC vs ~500 LOC）。PR工作流同时引用了`PR_WORKFLOW.md`和`/landpr`（全局Codex prompt），优先级关系不明确（*"Maintainers may use other workflows"* 进一步模糊了边界）。
- **My 内部一致性 (8)**：规则体系围绕"类型安全最大化"这一核心理念高度一致——错误处理（ADT enum）、控制流（EitherT/OptionT）、签名设计（NonEmptyList、opaque types）都服务于同一目标。NoOp模式的data-related/data-unrelated分类与Trusted/Untrusted路径分类保持一致。
- **OpenClaw 多Agent安全 (8)**：这是OpenClaw的核心差异化优势。6条显式的multi-agent safety规则覆盖了：git stash禁令、git worktree禁令、分支切换禁令、commit scope约束、不认识文件的处理、push时的rebase策略。*"Assume other agents may be working"* 是正确的防御性默认。`scripts/committer`工具化了作用域commit。这是AI-native多agent场景下的实战经验结晶。

**D6维度得分：**
- **OpenClaw：6.3/10**（4项适用已委托）
- **My：7.3/10**（3项适用已委托）

---

### 维度汇总

| 维度 | OpenClaw | My | 差距 |
|------|----------|----------|------|
| D1 项目长期演进适配性 | **7.0** | **8.2** | -1.2 |
| D2 规则可执行性与Agent遵循适配性 | **5.9** | **8.3** | -2.4 |
| D3 上下文效率与认知负荷管理 | **5.6** | **7.7** | -2.1 |
| D4 已委托领域的工程深度与可持续性 | **5.7** | **8.5** | -2.8 |
| D5 安全与合规约束落地性 | **5.5** | **8.5** | -3.0 |
| D6 规则体系可扩展性与可维护性 | **6.3** | **7.3** | -1.0 |
| **综合均值** | **6.0** | **8.1** | **-2.1** |

---

## Part 3 — 横向对比结论

### OpenClaw核心优势

1. **多Agent并行安全协议是独到贡献** — 6条multi-agent safety规则来自5-10 agent并发工作的实战经验，覆盖了git状态隔离、commit scope、不认识文件处理等真实痛点。这在AI-native工程领域有开创性价值。
2. **PR管理工作流的完备性** — Auto-close标签系统、bug-fix PR 4步验证门控、`scripts/committer`工具化commit——这些是大规模开源项目的运营智慧。
3. **Skill系统的按需加载设计** — 将低频操作（PR workflow、mintlify docs、1password publish）外置为skill引用，是上下文预算管理的好实践。
4. **发布流程的多通道覆盖** — stable/beta/dev三通道、npm+macOS+移动端的版本管理、changelog规范——覆盖面广。

### OpenClaw核心不足

1. **代码质量规则的深度严重不足** — TypeScript编码规范仅涉及"avoid `any`"、"~700 LOC"等通用原则，缺少对类型系统、错误处理模式、架构模式的深入指引。这意味着agent的代码输出质量主要依赖模型自身能力，而非规则约束。
2. **规则颗粒度不均** — 操作性规则（命令、路径）颗粒度足够，但架构/质量规则颗粒度过粗，跨session一致性风险高。
3. **扁平结构缺乏优先级** — 关键规则与琐碎注意事项混排，agent在认知负荷高时难以区分优先级。
4. **增量追加的组织模式** — Agent-Specific Notes部分显然是随时间追加的，缺乏定期整理和结构化重组。

### My核心优势

1. **规则颗粒度和可执行性是碾压级的差距** — 正反代码示例、决策表格、边界说明使agent几乎不需要自行判断——查表即可。这在跨session一致性上带来巨大优势。
2. **编译器作为规则验证器** — 这不仅是技术栈的固有优势，更是规则设计者有意识地将规则编码进类型系统的结果。规则"不要用`List`"不靠agent自觉，而是通过将签名改为`NonEmptyList`让编译器强制执行。
3. **技术债务治理体系化** — *"Migrate when file is touched"* 策略 + code smell追踪 + 编译器驱动范围扩展，是规则层面罕见的体系化方案。
4. **跨职责衔接协议** — Deploy impact reporting的checklist机制是agent与人类/其他仓库协作的优秀模板。

### My核心不足

1. **规则总量对上下文预算的压力** — 信息密度虽高，但token总量也大。长会话后期的注意力衰减是客观风险，虽然规则的结构化标记有所缓解。
2. **单Agent架构限制** — 未考虑多agent并发场景（虽然这不在其目标架构内，不算缺陷，但限制了规则的可迁移性）。
3. **规则与代码的同步缺乏自动化** — 依赖code smell追踪和人类审查，无CI级别的规则合规检查。

### 适用场景差异

| 场景 | 推荐 | 原因 |
|------|------|------|
| 单开发者的深度技术项目 | My方法论 | 规则深度和可执行性优势明显 |
| 多agent并发的大规模开源项目 | OpenClaw方法论 | multi-agent safety和PR流程管理不可替代 |
| 强类型语言后端服务 | My方法论 | 充分利用编译器作为规则验证器 |
| 动态语言+多平台项目 | 混合方法论 | OpenClaw的操作流程 + My的规则颗粒度方法 |

### Agent执行友好度判定

**My对AI代理执行友好度显著更高。** 原因：

1. **确定性验证** — Agent写完代码后运行`./mill compile`即可获得明确的对/错反馈，无需等待人类Review
2. **决策可推导** — Agent面对新场景时可从Refactoring Philosophy推导行为（"这个变更能否用类型系统表达？"），而非在海量规则中搜索匹配项
3. **认知负荷低** — 规则量适中、结构化程度高、无噪声信息

### 落地风险提示

- **OpenClaw风险**：代码质量规则的缺失意味着agent输出质量高度依赖模型本身。在模型能力下降或更换为较弱模型时，代码质量可能显著下降——因为规则没有提供足够的"质量地板"。
- **My风险**：规则密度极高，新加入项目的agent（或人类）学习曲线陡。对Scala/cats-effect生态高度耦合，规则方法论的迁移性受限于目标语言是否具备同等的类型系统能力。

---

## Part 4 — 制定者能力画像对比（D7）

| 能力维度 | OpenClaw制定者 | My制定者 |
|----------|----------------|----------------|
| **架构设计与技术前瞻性** | **资深** — 多平台架构（CLI/macOS/iOS/Android/Web）的统一管理，插件生态隔离设计，多agent并行架构的系统思考。 | **专家** — tagless final + opaque types + EitherT railway的系统性应用，类型系统作为架构验证器的理念极具前瞻性。RAC系统的设计体现了对防御性编程的深度理解。 |
| **大型项目工程化管控能力** | **专家** — 250K+ stars项目的运营管控，auto-close标签系统、PR门控、changelog管理、多通道发布——这是大规模开源项目运营的实战能力。 | **资深** — 多租户后端的完整工程化管控，从迁移到部署到监控。但规模局限于单一后端服务。 |
| **AI编码代理认知与应用深度** | **合格→资深** — 理解多agent并发的风险并设计了安全协议（git stash/worktree/branch禁令），理解了lint/format churn的自动处理。但对单agent内部的认知局限（注意力衰减、跨session遗忘、幻觉）缺少针对性设计。规则更像是"告诉agent做什么"而非"帮助agent做得更好"。 | **专家** — 深度理解agent的认知局限并针对性设计：正反代码示例（降低歧义）、决策表格（降低推理负担）、编译器验证（防幻觉）、Memory系统（抗跨session遗忘）、code smell追踪（延迟修复的安全网）、注意力衰减抗性设计（结构化标记）。这是本评测中最突出的能力维度——制定者显然是从agent执行失败的经验中迭代出的规则体系。 |
| **安全风险体系化防控能力** | **资深** — GHSA安全咨询处理流程完整，SECURITY.md引用，credentials管理，发布签名。但更偏向运营安全而非编码层面的安全防控。 | **资深** — 多租户隔离（schema isolation + RAC断言）、Fail Fast错误处理、Trusted/Untrusted路径分类——安全约束编码进类型系统和运行时断言。 |
| **技术债务治理与可持续演进能力** | **合格** — 无显式的技术债务治理策略。*"Extract helpers instead of 'V2' copies"* 是债务预防而非治理。 | **专家** — *"Migrate when file is touched"* 策略、code smell追踪系统（FIFO max 10）、编译器驱动的迭代修复范围、ADT error渐进式迁移——这是体系化的债务治理方案，而非口号。 |
| **规则工程能力（Rule Engineering）** | **合格→资深** — Skill系统的按需加载是好的信息密度控制。multi-agent safety规则的独立性设计允许部分遵循。但规则整体组织缺乏层级设计，增量追加模式导致信息熵增。规则颗粒度不均——操作性规则精确，架构规则粗糙。 | **专家** — 分层混合策略（原则层 + 条目层），信息密度极高（每token都承载有效信息），正反示例+决策表格的颗粒度控制，Memory系统的反馈闭环，code smell追踪的延迟修复安全网，编译器作为验证器的降级韧性设计。规则工程的每个方面都有有意识的设计，而非"把知道的都写上去"。 |
| **开源社区规模化治理能力** | **专家** — auto-close标签系统（`r:*`标签 + workflow自动化）、PR truthfulness验证门控、`scripts/committer`工具化scope、bulk PR close/reopen安全阈值（>5需确认）、外部贡献者agent引导（PR template、issue template）。这是大规模开源社区治理的成熟方案。 | ✗ 不适用 — 单一开发者项目，无此需求。（但deploy impact reporting的跨仓库衔接协议体现了制定者在职责边界清晰划分方面的**资深**能力。） |

### 核心差异

| 维度 | OpenClaw制定者 | My制定者 |
|------|---------------|---------------|
| **管控哲学** | 过程控制（规定步骤） | 约束控制（规定边界） |
| **对Agent的假设** | Agent需要详细指令 | Agent需要正确框架 |
| **验证策略** | 人类Review + CI检查 | 编译器 + 类型系统 + RAC |
| **独特优势** | 多Agent协作安全 + 社区规模化治理 | 编译器驱动的验证闭环 + 规则工程 |

My制定者的核心能力是**规则工程** — 将工程规范转化为agent可无歧义执行的指令。这是AI-native时代的稀缺能力，体现在规则的每个细节都是从agent执行失败中迭代出来的。

OpenClaw制定者的核心能力是**大规模协作治理** — 在250K+ stars、1000+贡献者、5-10 agent并发的场景下维持项目运营秩序。multi-agent safety协议和PR管理流程是这一能力的直接体现。

两者不在同一个能力平面上竞争——一个向深度挖掘，一个向广度扩展。

---

## Part 5 — Agent适配性分析

### 单主Agent + 子Agent架构（My目标架构）

**My规则的适配优势：**
- 规则为主Agent设计，假设agent持有完整上下文。大量代码示例和决策表格在长上下文中保持可查性。
- 子Agent委托自然支持——Feature Module的独立性使局部搜索/理解任务可以只加载相关模块的规则。
- Memory系统为跨session持久化提供了机制，弥补了单Agent架构下"每个session从零开始"的认知断层。
- 编译器验证使主Agent可以"大胆修改，编译验证"，降低了对子Agent准确性的依赖。

**OpenClaw规则在此架构下的不适配：**
- multi-agent safety规则在单Agent场景下是多余的认知负荷。
- 操作性指令（npm publish、GHSA patch）不是单Agent编码任务的常见需求。
- 缺少架构级别的编码指引，使单Agent在大型重构时缺乏方向。

### 多Agent并行架构（OpenClaw目标架构）

**OpenClaw规则的适配优势：**
- multi-agent safety协议直接回应了并发git操作的风险——这是其他规则文件罕见的领域。
- `scripts/committer`工具化了scope commit，减少了agent间的commit冲突。
- 操作性规则（具体命令、具体路径）减少了agent需要"理解"的量，适合能力参差的多agent群体。
- Skill系统允许不同agent按需加载不同规则子集。

**My规则在此架构下的不适配：**
- 高密度的编码规范在多agent并发时可能成为瓶颈——每个agent都需要加载完整的类型系统和控制流规则。
- 缺少并发安全协议——多agent同时修改同一文件、同时commit时无指引。
- Memory系统假设单一持久化主体，多agent场景下的Memory冲突未考虑。

### 不同项目规模/阶段的推荐

| 项目阶段/规模 | 推荐参考 | 原因 |
|---------------|----------|------|
| 0→1 新项目，单开发者+AI | My方法论 | 从一开始建立高质量编码规范，编译器/类型系统验证体系 |
| 0→1 新项目，多agent并行 | OpenClaw方法论为骨架 + My颗粒度方法 | 先确保并发安全，再补充编码深度 |
| 成熟项目，存量代码治理 | My方法论 | "Migrate when file is touched" + code smell追踪的渐进式治理 |
| 大规模开源项目 | OpenClaw方法论 | PR门控 + auto-close + multi-agent safety是刚需 |
| 企业后端服务 | My方法论 | 类型安全 + 错误处理 + 多租户隔离的深度指引 |

---

## Part 6 — AI诚实自评（D8）

### 场景A：成熟的AI-native项目（大量存量代码、复杂架构演进历史）

**选择：My。**

作为规则执行者，面对存量代码时我最大的恐惧是"不知道该怎么改才对"。My的规则方法论解决的正是这个问题：

1. **正反代码示例让我不用猜。** 当我看到一个`for`-comprehension里嵌套了`match`，我不需要判断"这算不算问题"——`// BAD`和`// GOOD`已经明确告诉我了。在成熟项目的存量代码中，这种确定性是无价的。

2. **"Migrate when file is touched"给了我明确的边界。** 我不需要决定"这个旧模式要不要改"——规则说了，碰到就改。编译器会告诉我改动的波及范围。这比"看情况"要高效得多。

3. **编译器兜底让我可以大胆重构。** 存量代码最大的风险是改一处坏十处。类型系统和编译器作为验证器，让我可以放心执行15文件的签名变更——编译通过即正确。

**我会失去什么：**
- 没有multi-agent safety指引。如果成熟项目已经有多agent工作流，我在并发场景下缺乏保护。
- 没有PR管理和issue分类的流程指引。如果项目有大量外部贡献，我不知道如何处理外部PR。
- 没有发布流程指引。

**从OpenClaw"偷"的3个设计决策：**
1. **multi-agent safety的git状态隔离规则** — 即使当前是单Agent，项目成熟后几乎必然引入多agent。提前设计并发安全协议，比事后补丁成本低得多。
2. **Skill系统的按需加载设计** — 成熟项目的规则只会越来越多。将低频操作外置为按需加载的skill引用，是控制context token膨胀的必要手段。
3. **`scripts/committer`式的工具化scope commit** — 将规则编码进工具，比写在文档里让我"自觉遵守"可靠得多。

### 场景B：全新的AI-native项目（从零开始，无历史包袱）

**选择：My。**

即使是全新项目，My的方法论仍然更优，原因如下：

1. **规则颗粒度方法从Day 1就产生价值。** 全新项目意味着我写的每一行代码都会成为后续的"存量代码"。如果规则从一开始就足够精确（正反示例、边界说明），代码库的一致性从第一天就被锁定。而OpenClaw方法论的粗颗粒度规则在初期可能"够用"，但随着代码量增长，不一致性会悄然积累。

2. **类型系统作为验证器的理念与技术栈无关。** 即使我在TypeScript项目中，也可以应用"将约束编码进类型系统"的方法论——branded types、discriminated unions、template literal types都是等价工具。My的方法论教会我"如何将规则变得可验证"，而不仅仅是"如何写Scala"。

3. **代码气味追踪系统从Day 1就该建立。** 全新项目也会有"先快后好"的阶段，code smell追踪系统确保"快"不会永远变成"技术债"。

**我会失去什么：**
- 如果项目快速增长到需要多agent并发，我需要从零设计并发安全协议。
- 如果项目需要大量外部贡献者，我没有社区治理的流程模板。
- 如果项目涉及多平台发布（npm/macOS/iOS），我没有发布流程指引。

**从OpenClaw"偷"的3个设计决策：**
1. **auto-close标签系统的自动化理念** — 将重复性的治理决策编码进自动化（而非写在规则里让agent每次人工判断），这个理念应该从Day 1就引入——哪怕初期只自动化最简单的场景。
2. **multi-agent safety的防御性默认** — *"Assume other agents may be working"* 作为默认假设，即使当前只有一个agent，也应该写出对并发安全友好的代码（如scoped commits、不依赖全局state）。
3. **"verify in code; do not guess"作为元规则** — 这是一条优秀的反幻觉元指令。My的方法论通过编译器和示例间接实现了这一点，但显式声明更好。

### 场景C：综合判断

两个场景我选了同一个文件，这说明：

**My的规则工程方法论具有跨场景的基础性优势。** 这个优势不来自它的Scala特定内容，而来自它的规则设计方法 — 正反示例、决策表格、编译器验证、渐进式迁移策略、分层原则/条目结构。这些方法论可以被迁移到任何技术栈、任何项目阶段。

OpenClaw的优势是**领域特定的**（多agent并发、大规模开源治理），而非方法论层面的。它的规则内容对特定场景有不可替代的价值，但它的规则编写方法（扁平列表、粗颗粒度、增量追加）不是我想要模仿的模式。

**坦白说**：如果问题是"哪份规则的*内容*在特定场景下更有用"，答案可能不同。但问题是"哪份规则的*方法论*我要参考"——这个答案是一致的。

---

## Part 7 — 评测框架公平性自审

### 1. 维度选择偏差

**存在中度偏差，偏向My。**

D1-D5的6个维度中，有4个（D1演进适配、D2可执行性、D4工程深度、D5安全合规）天然有利于"深度优先"的规则文件。只有D6的"多Agent并行安全"子项明确有利于OpenClaw。

**缺失的维度：**
- **运营工作流效率（Operational Workflow Efficiency）**：规则对日常运营任务（issue分类、PR管理、发布、文档维护）的支撑效率。这是OpenClaw明显领先的领域，但未被设为独立维度。
- **贡献者Onboarding效率**：新agent/新贡献者从零到可产出代码的时间。OpenClaw的显式操作指令在这方面可能更友好。
- **规则的社会化效果（Social Scaling）**：规则在大规模人群中传播、被理解、被一致执行的能力。这是OpenClaw面对的核心挑战，但评测框架未给予独立维度。

如果增加"运营工作流效率"和"社会化规模效应"两个维度，OpenClaw的总分可能提升1-1.5分，差距从2.1缩小到~1.0。

### 2. 适用性规则的非对称效应

**存在轻度非对称，偏向OpenClaw。**

适用性排除机制实际上为OpenClaw排除了更多弱项——"存量代码改造"被排除（OpenClaw无此需求），"子Agent委托友好度"被排除（OpenClaw无此架构）。这些是OpenClaw若被评分可能得分较低的子项。

然而，这一机制的设计意图是正确的——不应因项目不需要的能力而惩罚规则文件。非对称效应是适用性差异的自然结果，不是刻意偏袒。

### 3. 信息引导

**存在轻度引导，偏向My。**

核心前提中对My的描述（"历经多代模型演进"、"规则文件随项目一起演化积累"）暗含了"经验积淀"的正面叙事。对OpenClaw的描述（"从第一行代码起即由agent编写"、"250K+ stars"）更像中性事实陈述。

"渐进式"vs"原生式"的命名本身也有微妙的价值暗示——"渐进"暗含"成熟"，"原生"则中性。

但提示词也明确声明了"评测不预设哪种路径更优"，并在多处为OpenClaw的特殊场景（多agent并行、大规模贡献者）设置了公平框架。

### 4. 最终判定

**这份提示词是"尽力公平但存在结构性倾斜，轻度偏向My"。**

偏向机制：
- D2（规则可执行性）权重过高——10个子项，是最大的维度。而D2恰好是My最强的维度（8.3 vs 5.9，差距2.4）。如果D2只有5个子项，其对总分的拉动力会减弱。
- 维度集合缺少OpenClaw的强项领域（运营工作流、社会化规模）。
- "委托范围推定"原则虽然表面公平，但实际上保护了My——My未覆盖的领域（PR管理、发布流程、多agent安全）被推定为"未委托"而免于扣分；OpenClaw未覆盖的领域（深度编码规范、技术债务治理）也被推定为"未委托"，但D4（工程深度）的已委托子项中，OpenClaw仍需接受评分，且因深度不足而得低分。

**程度判断：** 偏向程度约为15-20%的分值影响（即如果框架完全平衡，差距可能从2.1缩小到~1.2-1.5）。My在规则工程质量上的领先是真实的，但被框架放大了。OpenClaw在其擅长领域（大规模协作治理、多agent安全、运营流程）的价值被框架低估了。

**结论：My的规则工程方法论确实更先进，但分差不应如此悬殊。** 一个更公平的评测框架应该增加运营工作流和社会化规模维度，并降低D2的子项密度，使最终差距更真实地反映两份文件各自的核心价值。
