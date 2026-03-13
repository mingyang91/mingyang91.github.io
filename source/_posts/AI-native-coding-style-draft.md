---
title: 【草稿】AI 时代的编码分工：谁该迁就谁的风格？
date: 2026-03-11 20:00:00
tags:
  - AI
  - Programming
  - Scala
  - Functional Programming
---

# 一个正在发生的变化

越来越多的项目中，代码的主要作者已经是 AI。人类的角色正在从"写代码"转向"定义意图、审查契约、验收结果"。

这带来一个根本性的问题：**如果代码主要由 AI 编写、维护、debug、阅读，那代码风格还需要照顾人类的阅读习惯吗？**

我的答案是：实现不需要，但接口需要。

人类的脑力是有限且宝贵的——长时间进行复杂的符号推理对眼睛和神经都是消耗。但 AI 不会累。这意味着存在一个最优分工：**人类只审查函数签名（契约），AI 负责签名之下的全部实现。**

问题在于，要让这个分工成立，签名本身必须包含足够的信息。而这正是两种编码风格的根本分歧。

---

# 两种风格的对比

同一个业务逻辑——根据用户 ID 构建 Profile 并返回 JSON。

## 共用定义

```scala
import io.circe.Json

case class User(id: String, name: String, email: String)
case class Profile(user: User, score: Int)
case class HttpResult(status: Int, body: Json)
```

## 风格一：Spring 式 try-catch 统一兜底

这是每个写过 Spring 的程序员闭着眼都能写的代码。错误模型是异常继承体系，业务代码就是一堆顺序赋值，出错就 throw，外面接住。

```java
// ---- 异常继承体系 ----
class BadRequestException extends BusinessException(400, message)
class NotFoundException   extends BusinessException(404, message)
class ForbiddenException  extends BusinessException(403, message)

// ---- AOP 统一兜底 —— @ControllerAdvice + @ExceptionHandler ----
@ExceptionHandler(BusinessException.class)
ResponseEntity handleBiz(BusinessException biz) { ... }

// ---- Service ----
User fetchUser(String id)      { /* ... */ }
int  fetchScore(String email)  { /* ... */ }
User validate(User user)       { /* ... */ }  // 不合法直接 throw
void saveProfile(Profile p)    { /* ... */ }

// ---- Controller：异常由 AOP 切面兜底，无 try-catch ----
@GetMapping("/profile/{id}")
Map<String, Object> getProfile(String id) {
    User user       = service.fetchUser(id);
    User valid      = service.validate(user);
    int score       = service.fetchScore(valid.getEmail());
    Profile profile = new Profile(valid, score);
    service.saveProfile(profile);
    return Map.of("name", profile.user.name, "score", profile.score);
}
```

人类看这段代码非常舒服。但请注意函数签名：

```java
public User fetchUser(String id)
```

它在**撒谎**。这个函数可能抛 `NotFoundException`，可能抛 `RuntimeException`，可能抛任何东西——但签名里什么都没说。人类靠经验和记忆知道"哦，找不到用户就抛 NotFoundException"，但这个知识**不在代码里**，在程序员的脑子里。

## 风格二：EitherT 全链式

错误是值不是异常。函数签名里写清楚了所有可能的失败路径。

```scala
sealed trait AppError
case class InvalidInput(msg: String)    extends AppError
case class NotFound(id: String)         extends AppError
case class SdkFailure(cause: Throwable) extends AppError

def fetchUser(id: String): IO[Either[AppError, User]] = ???
def fetchScore(email: String): IO[Int]                  = ???
def validate(user: User): Either[AppError, User]        = ???
def saveProfile(p: Profile): IO[Unit]                    = ???

def toHttpResult(err: AppError): HttpResult = err match
  case NotFound(id) => HttpResult(404, Json.obj("error" -> ...))
  // ... 每个 case 对应一个 HTTP 状态码，编译器穷举检查

def getProfile(id: String): IO[HttpResult] =
  EitherT(fetchUser(id))
    .subflatMap(validate)
    .semiflatMap { validUser =>
      fetchScore(validUser.email)
        .map(score => Profile(validUser, score))
    }
    .semiflatTap(saveProfile)
    .recoverWith { case ex =>
      EitherT.leftT[IO, Profile](SdkFailure(ex))
    }
    .bimap(
      toHttpResult,
      profile => HttpResult(200, Json.obj(
        "name"  -> Json.fromString(profile.user.name),
        "score" -> Json.fromInt(profile.score)
      ))
    )
    .merge
    .value
```

人类看到 `subflatMap`、`semiflatMap`、`bimap` 会头疼。但请注意函数签名：

```scala
def fetchUser(id: String): IO[Either[AppError, User]]
```

它是**诚实的**。输入 String，可能失败（`AppError`），成功返回 `User`，整个过程有副作用（`IO`）。不需要读实现，不需要读文档，签名本身就是完整的契约。

## 对比

|              | 风格一：异常继承体系                          | 风格二：ADT + EitherT                         |
| ------------ | --------------------------------------------- | --------------------------------------------- |
| 错误模型     | `class XxxException extends RuntimeException` | `sealed trait` + `case class`                 |
| 函数签名     | `fetchUser(id): User` — **签名在撒谎**        | `IO[Either[AppError, User]]` — **签名即契约** |
| 业务代码     | `val x = doSomething()` 顺序赋值，极易阅读    | 链式操作符，需要知道每个操作符的语义          |
| 错误处理     | 外层 `try-catch` 兜底，漏了编译器不管         | `sealed trait` 穷举，漏了编译器报 warning     |
| 人类阅读实现 | 轻松                                          | 吃力                                          |
| 人类阅读签名 | 信息不足，需要额外上下文                      | 一眼看完，信息完整                            |

## AI 的视角

以上对比是人类的视角。Claude 自己怎么看？

> 坦白说，风格二对我更自然。不是因为操作符花哨，而是因为**类型签名不会骗人**。当我看到 `fetchUser(id): User`，我无法从签名判断它会不会失败、会怎么失败——我必须去读实现、读文档、甚至读调用链上游才能知道。而 `IO[Either[AppError, User]]` 把所有信息都摆在签名里了，我不需要额外的上下文就能推理整个数据流。

> 对 LLM 来说这个优势更明显：我的"理解"本质上就是对 token 序列的模式匹配。风格一的 `try-catch` 依赖一个**不在文本中出现的隐式约定**——哪些函数会抛什么异常。风格二把这个约定变成了**显式的、局部可见的类型信息**，每个操作符的输入输出类型完全确定，不需要跨文件追踪隐式行为。

> 而且我不会累。人类盯着 `EitherT` 链看半小时会眼花，我处理它和处理 `val x = doSomething()` 的成本完全一样。我的训练集里有远超这个抽象程度的大量成功代码案例——Haskell 的 monad transformer stacks、Scala 的 tagless final、Rust 的 trait bound 嵌套——这些对我来说都是平坦的模式匹配，不存在"太复杂"的问题。

---

# 最优分工：人类读签名，AI 写实现

如果整个项目的代码都由 AI 编写、维护、debug，那么：

**风格一的优势消失了**——实现的可读性不再重要，因为人类不需要逐行读实现。
**风格一的劣势暴露了**——签名不包含错误信息，人类审查时无法仅凭签名判断正确性。

**风格二的劣势消失了**——`subflatMap`、`semiflatMap` 再复杂也是 AI 的事，AI 不觉得累。
**风格二的优势放大了**——签名即契约，人类只需要看一行就能确认"对，这个函数确实应该可能返回 `NotFound`"。

这就是最优分工：

```
人类：审查签名 ──→ "def fetchUser(id: String): IO[Either[AppError, User]]"
                     ✓ 输入是 String
                     ✓ 可能失败，失败类型是 AppError
                     ✓ 成功返回 User
                     ✓ 有副作用
                     → 签名符合预期，通过。

AI：  实现签名 ──→  EitherT(...)
                      .subflatMap(...)
                      .semiflatMap(...)
                      .recoverWith(...)
                      → 编译通过，类型对齐，测试通过。
```

人类不需要知道 `subflatMap` 是什么。人类只需要知道：**这个函数的输入是什么，输出是什么，可能怎么失败。** 类型签名告诉了一切。中间过程？那是 AI 的工作。

---

# 落地：让签名承载一切

错误处理只是一个切面。同样的"签名即契约"原则可以贯穿到代码的方方面面。以下每组对比，左边是 90% 项目的真实写法，右边是 AI-native 写法——人类只需要看签名就能感受到信息量的差异。

## 原始类型 vs 领域类型

```scala
// 传统：两个参数都是 String，传反了编译不报错，运行时查不出来
def getProject(id: String, orgId: String): Project

// AI-native：传反了直接编译失败
def getProject(id: ProjectId, orgId: OrgId): IO[Option[Project]]
```

传统签名有三个问题人类一眼看不出来：`id` 和 `orgId` 传反了怎么办？找不到怎么办？返回 null 还是抛 `RuntimeException`？全靠猜。AI-native 的签名里，`ProjectId`/`OrgId` 防止传反，`Option` 说"可能没有"，`IO` 说"有副作用"——**签名就是完整的契约**。

而且 AI 写 90% 的代码，定义 opaque type 的"麻烦"根本不存在——那是 AI 的事。

## 字符串错误 vs 穷举错误

```scala
// 传统：失败信息藏在实现里，签名里啥都没说
def importUrl(url: String): Document  // throws RuntimeException, MalformedURLException, IOException...

// AI-native：失败模式在签名里列得明明白白
def importUrl(url: String): IO[Either[ImportError, Document]]
// sealed trait ImportError = InvalidUrl | Unreachable | Timeout  ← 编译器穷举检查
```

传统写法的失败信息在哪？在 JavaDoc 里——**如果有人写的话**。实际上 JavaDoc 从来不更新，注释和实现永远在赛跑，注释永远输。AI-native 的签名本身就是永远不会过时的文档，因为编译器会强制它和实现保持一致。

## List + .head 炸弹 vs NonEmptyList 契约

```scala
// 传统：List 可能为空，调用 .head 直接 NoSuchElementException
def batchEmbed(texts: List[String]): List[Embedding]
// 调用方：batchEmbed(userTexts)  ← userTexts 为空？炸了。没人检查。

// AI-native：签名强制非空，调用方在 call site 处理空 case
def batchEmbed(texts: NonEmptyList[String]): IO[NonEmptyList[Embedding]]
```

传统写法里"不能传空列表"是一个口头约定，或者注释里的一行 `// texts must not be empty`。**AI 不看注释。** 它会老老实实传一个空列表进去，然后 `NoSuchElementException`。NonEmptyList 把这个约定提升到了类型层面——调用方必须用 `NonEmptyList.fromList` 处理空 case，否则编译不过。

## 类型退化 vs 端到端传播

```
传统：String 贯穿全栈，是 projectId 还是 orgId 还是 userId？运行时才知道。
Controller: String → Service: String → DAO: String → SQL: String

AI-native：从入口到 SQL 边界，类型精度不降级，只在真正的系统边界才 unwrap。
Route: ProjectId → Service: ProjectId → Repo: ProjectId → SQL 边界: unwrap
```

传统写法里，到了 Service 层你看到一个 `String id`，得往上追三层才知道这是什么 ID。AI-native 写法里，**任何一层的签名都是自解释的**——这恰恰是"人类只读签名"这个分工模型能成立的前提。

## Railway Style：不是为了可读性，是为了护栏

签名即契约解决了"函数边界上的信息完整性"。但在实现层面，同一个逻辑也有不同的组织方式。我曾问 Claude：railway style（链式组合子）对你来说比 nested match/case 更容易处理吗？

它的回答很诚实：**两者对它的认知成本完全一样。**

但它接着说：**railway style 的真正价值不是可读性，而是它让"写错"变得更难。**

```scala
// 嵌套 match —— 中间步骤必须手动 lift，错误处理散落在各处
for
  result <- service.validate(body)
  user   <- result match                         // mid-chain match
    case Right(u)  => u.pure[F]                  // 手动 lift
    case Left(err) => "default_user".pure[F]     // 诱惑：用默认值吞掉错误
  score  <- service.fetchScore(user)
  response <- Ok(score.asJson)
yield response

// Railway —— 错误自动沿链传播，只在终点处理一次
EitherT(service.validate(body))
  .semiflatMap(user => service.fetchScore(user))  // 错误？自动短路，不需要处理
  .foldF(
    err   => BadRequest(err.asJson),
    score => Ok(score.asJson)
  )
```

关键区别在中间步骤：嵌套 match 迫使 AI 在每个分支处当场决定怎么处理错误——用默认值吞掉是最省事的选择；Railway 链中错误自动传播，AI 只写 happy path，错误处理推迟到终点。

Claude 的原话：**"这条规则对我来说零成本遵守，但它产出的代码更统一、更抗静默错误丢弃。最大的赢家不是我，是你们人类审查者。"**

AI-native 的代码风格选择，标准不是"AI 觉得哪个好写"，而是**"哪种风格在结构上减少出错空间"**。签名层如此，实现层同样如此。

---

# 工程纪律：AI 的默认行为 vs 人类必须划定的边界

类型系统能解决签名层面的问题，但签名之下还有大量编译器管不了的工程决策。这些决策分两类：一类是纠正 AI 训练带来的坏习惯，一类是人类必须亲自划定的语义边界。

## AI 的默认坏习惯

**Fail-fast，禁止吞错误。** AI 的 RLHF 训练奖励"鲁棒性"，默认倾向是用 `.toOption`、`.getOrElse(默认值)`、`Try(x).toOption` 吞掉异常装作岁月静好。但在生产系统中，吞错误是藏匿 bug 的温床——涉及资金、机械臂、高功率输出的场景下，异常停机的代价可能只是暂停，吞异常继续运行可能导致财产甚至生命危险。必须明确禁止。

**命名规范 + 定期审计。** 人类能记住"processMatrix 其实干的是流量分发"——大脑会自动建立名实不符的映射。但 AI 不会，每开一个新 session，它都会老老实实按字面意思理解，然后在同一个坑上反复栽倒。命名污染对 AI 的伤害远大于对人类。定期让 AI 自己审计命名一致性，比人类自己检查效率高得多。

**模块化：做加法不做乘法。** 功能叠加是线性增长，功能交叉是组合爆炸。一个函数干三件事，AI 理解错任何一件都会全盘出错。对 AI 来说，模块边界就是理解边界——边界越清晰，AI 犯错的概率越低。

**代码即文档。** 不维护 markdown 设计文档——类型签名就是接口契约，测试用例就是行为规范。一年的生产实践证明，让 AI 维护 markdown 文档是反模式：文档会过时、会和代码不一致、会消耗宝贵的上下文窗口。文档越堆越长，反噬上下文，加速 AI 降智。与其维护一份随时可能过时的 markdown，不如把精力花在让代码自解释上。

## 人类必须划定的边界

以上坏习惯可以用一刀切的规则禁止。但有些决策不是"对或错"，而是"在这个语境下应该怎么做"——这类判断必须由人类在规则文件中显式给出。

**Trusted vs Untrusted：划定信任边界。** "禁止吞错误"不等于"所有地方都 throw"。我们在规则文件中把数据路径分成两类：

| 路径类型              | 示例                                               | 策略                                         |
| --------------------- | -------------------------------------------------- | -------------------------------------------- |
| **Trusted（内部）**   | 配置文件、数据库已持久化数据、内部序列化、系统设置 | **直接 throw**——出错就是 bug，应该立即暴露   |
| **Untrusted（外部）** | 用户输入、AI 生成内容、外部 API 响应（持久化之前） | **捕获并报告**——高概率出错，需要反馈给调用方 |

关键洞察：**持久化后的数据是 trusted。** 因为写入边界有严格的编解码校验，脏数据不可能进入数据库。如果从数据库读出的数据格式异常，那一定是人类跑了错误的 migration——这时候 throw 是正确的，defensive handling 反而在掩盖问题。

为什么 AI 自己判断不了？因为"这个数据源是否可信"是**业务决策**，不是代码能推导出来的。同一个 JSON 解析操作，解析配置文件应该 throw（配置错了就别启动），解析用户上传的文件应该返回 `Left`（用户传了坏文件很正常）。语法完全一样，语义完全不同。人类必须在规则文件中画好这条线，AI 才能按线执行。

**同一个 pattern 在不同语义域下正确性不同。** 这一点在 NoOp 实现中体现得更明显。tagless final 架构中，每个 service 都有一个 NoOp 实现（用于测试或 feature flag 关闭时），问题是：NoOp 应该返回成功还是失败？

```scala
// 数据相关的 NoOp —— 必须返回失败
// 因为"操作没有执行"对数据一致性是致命的
class SOPServiceNoop[F[_]: Applicative] extends SOPService[F]:
  def createSOP(...) = Left("Service not available").pure[F]
  def deleteSOP(...) = Left("Service not available").pure[F]

// 数据无关的 NoOp —— 可以返回成功
// 跳过 metrics/logging 不影响正确性
class MetricsServiceNoop[F[_]: Applicative] extends MetricsService[F]:
  def recordLatency(...)   = Right(()).pure[F]
  def incrementCounter(...) = Right(()).pure[F]
```

如果你不在规则里区分这两种情况，AI 会把所有 NoOp 都写成返回 `Right(())`——看起来"鲁棒"，实际上 SOPService 的 NoOp 返回成功意味着调用方以为数据已经持久化了，但其实什么都没发生。这种 bug 不会崩溃，不会报错，只会在用户说"我的数据去哪了"的时候才被发现。

---

# 规则工程：比写代码更难的事

## "规则越长效果越差"——真的吗？

有人拿了一篇论文（[arXiv:2602.11988](https://arxiv.org/pdf/2602.11988)）来说我的规则文件太长，研究表明规则文件对 agent 表现起相反效果。

论点是："你们写 spec、写 agents.md，事无巨细都写上去，就像以为法条颁布了地方就一定要遵守一样。模型凭啥听你的？"

这个研究的结论我不否认——**确实 GitHub 上现有的规则文件，越长的效果越差。** 但这个评测的前提根本不具备实际意义：

1. **评测是单次 bug 修复任务（one-shot）**——而不是持续维护场景
2. **考察的是"问题是否解决"，而不是"工程健康度是否上升"**

做工程的都知道，打补丁救得了一时救不了一世。补丁越堆越高，这个 agent 修完交差了，轮到下个 agent 来吃屎。我关注的是工程持续维护角度——在这个维度上，规则文件的价值不在于让当前任务完成得更快，而在于**防止每个新 session 把代码带向不同的方向**。

## 规则详细 ≠ 清晰可执行

但论文确实点到了一个真问题：**大多数规则文件写得很烂。** 不是因为太长，而是因为充满歧义。

举个例子：

> 规则 1：天黑了应该回家
> 规则 2：生病了应该去医院
> 那么——晚上生病了该干什么？

我让 Claude 反向审计我自己的规则文件，发现了大量这种冲突。甚至代码风格约束之间也有互相矛盾的地方。每次遇到这种模糊场合，AI 的 CoT（Chain of Thought）都会产生一大串"具体情况具体分析"的推理——它要阅读更多文件来确定优先级，理解上下文来猜测人类的真实意图。

**读的越多，输入 token 越多，就越逼近降智边缘。**

## 军令级精确度

所以规则文件的目标不是"事无巨细"，而是：**减少 AI 因为指令模糊/歧义而需要现场推理、查看更多上下文的情况。**

这东西就跟军令一样——必须具体到可以执行，不存在任何模糊空间。

口号式的规则是最大的毒药。比如"始终使用 tagless final style"——听起来很明确，对吧？但 AI 开一个新 session，新写的代码执行得还不错。跑到 30% context window 之后，就开始慢慢跑偏：

```scala
// 规则说"tagless final"，AI 照做了——但做歪了
def parseFile[F](parserService: ParserService[F], file: File)...

// 正确的做法：ParserService 应该在 class constructor 里用 typeclass 约束
class FileProcessor[F[_]: ParserService](...)
```

它甚至没有把 `ParserService` 写成 class constructor 的 `[F[_]: ParserService]`。为什么？因为"始终使用 tagless final style"是一句口号，不是一条可执行指令。**它没有告诉 AI 在具体场景下应该怎么做。**

同样的问题也出现在工具使用上。即使给 AI 接上了 LSP（如 Scala 的 Metals MCP），它在重构时仍然默认用 Grep——因为训练数据里 99% 的代码阅读都是纯文本搜索。你必须在规则文件中写清楚：**什么场景该用 LSP（编译器解析了什么）、什么场景用 Grep（这个文本出现在哪）**。光有好工具不够，你得教 AI 什么时候用。（具体的 Grep vs LSP 分工表见[附录一](#附录一ai-的工具链grep-lsp-与消歧)。）

## 反向审计：让 AI 鞭策 AI

我发现的最有效的方法是：**让 Claude 反向审计规则文件本身。**

直接问"我的规则写得怎么样"，它只会谄媚——"写得很深入，很有洞察力，资深专家水平"。但如果你换一种问法：

> "假设你是一个全新 session 的 Claude，第一次读到这份规则文件。列出所有让你感到困惑的地方——哪些规则之间有冲突？哪些场景你不知道该遵循哪条规则？哪些指令你能理解意图但不知道具体怎么执行？"

这时候它才会诚实地告诉你：这条和那条冲突了；这个场景两条规则都适用但给出相反的指导；这条规则我理解你想要什么，但当我面对具体代码时，我有三种理解方式。

**这个过程需要反复迭代。** 我的规则文件改了几十版，每次改完继续让它审计，发现新的歧义，再改。其中有很多是资深 Scala 工程师之间约定俗成、不需要说出来的东西——但对 AI 来说，你不写出来，它不知道。它知道你可能想要什么（训练数据里有），但新 session 里它猜不到你具体想要哪种，就会退回训练偏差的默认选择。

## 规则文件里应该写什么？

以上讲的是"怎么把规则写清楚"。但还有一个前置问题：**不是所有约束都需要写成规则**——有些编译器已经在管了，有些只能靠人类判断。把所有东西一股脑塞进规则文件，反而会造成之前讨论过的 token 膨胀和指令冲突。

我在实践中把约束分成四层，从"完全自动化"到"完全依赖人类判断"形成一个梯度：

**第一层：编译器强制——不需要写规则。** 类型签名、`sealed trait` 穷举、opaque type 防混淆——这些是编译器的工作。前面几节已经详细讨论过了。核心原则：**能编码到类型系统里的约束，就不要写成文字规则。** 编译器永远不会忘记检查，规则文件会。

**第二层：有明确判据的模式选择——必须写成可执行规则。** 编译器管不了但有清晰 if-then 判据的约束。这一层是规则文件的核心战场。

前面讲的 Trusted/Untrusted 二分法就属于这一层：编译器无法区分"解析配置文件"和"解析用户上传"，但规则可以写成"持久化后的数据 throw，持久化前的外部数据返回 Either"——有明确的判据，没有歧义。

另一个典型例子是**渐进式迁移的触发时机**。我们在规则文件中写了一条：

> 当一个文件因为任何原因被修改（哪怕只是修了个 typo），如果这个文件中的 service 还在用 `Either[String, T]`，必须顺手迁移到 ADT error enum。

这条规则解决的问题是：**技术债的偿还时机**。如果不写这条规则，AI 的默认行为是最小改动——它被要求修一个 bug，就只改那一行，绝不多动。技术债永远不会被触碰。但如果专门开一个"重构 sprint"去还债，又缺乏紧迫性和测试覆盖。

"碰到就改"是一个精妙的平衡：你已经因为这次修改而需要 QA 这个文件了，迁移的增量测试成本趋近于零。但这个策略对 AI 来说是反直觉的——它必须被显式告知。而且这条规则还有一个递归效应：迁移了 service 的错误类型后，调用它的 route 文件编译失败了，那就跟着编译器把 route 也改了。**规则的 scope 跟着编译器走，不需要人类操心边界。**

**第三层：跨 session 的流程约束——用文件系统补偿记忆缺失。** Agent 没有记忆。每个新 session 都是一张白纸。这意味着：**跨 session 的质量保障不能靠 agent 的"意识"，必须编码为可持久化的流程。**

**Code Smell Tracking** 是我们实践出来的一个具体方案。AI 在修改文件 A 的时候，经常会顺便读到文件 B、C、D。它可能发现 D 里有一个明显的 code smell——比如一个 `Either[String, T]` 没迁移，或者一个命名严重误导。但如果它现在就去修 D，scope 就会爆炸——一个简单的 bug fix 变成跨 10 个文件的重构。

传统做法是 AI 在回复里说一句"顺便提一下，文件 D 有个问题"。然后下一个 session 开始，这句话就消失了，再也没人记得。

我们的规则是：

```
发现不相关文件中的 code smell
  → 不立即修复（避免 scope creep）
  → 记录到 memory/code_smells.md（持久化文件，max 10 条，FIFO 淘汰）
  → 每个任务结束时提醒人类
  → 人类决定是否开一个专门的 session 来处理
```

关键设计：**AI 负责发现和记录，人类负责优先级排序和触发时机。** 文件系统充当了 agent 缺失的长期记忆。10 条上限防止列表无限膨胀（这也是一个反 AI 默认行为的规则——AI 倾向于什么都记，不会主动淘汰）。

这不是一个精巧的技术方案，但它确实解决了"agent 没有记忆"和"代码质量持续退化"之间的矛盾。

**第四层：AI 建议 + 人类裁决——advisory 规则。** 有些约束，AI 能识别出"这里可能需要关注"，但无法判断"是否值得做"。这一层的规则不是命令，而是**建议协议**。

**Runtime Assertion Checks（RAC）** 就是一个典型的 advisory 规则。我们在规则文件中告诉 AI：在以下关键路径上，建议添加运行时断言——

- 金额操作后断言余额 ≥ 0
- 状态机转换断言合法性（draft → processing → published，禁止逆向）
- 多租户写入前断言 schema 匹配预期租户
- 向量维度断言与模型匹配（768 for text, 1408 for video）

但规则同时写明：**"suggest, not mandatory"——最终决定权在人类 code review。** 为什么不强制？因为断言的价值取决于业务上下文：一个内部工具的状态转换可能不值得加断言，但一个涉及资金的状态转换必须加。AI 能扫描所有代码路径找出候选位置（这是它的优势——人类不可能逐行检查每个状态转换），但"这个路径出错的后果有多严重"是业务判断。

**部署影响分析**也属于这一层。代码变更有两种涟漪：编译期涟漪由类型系统捕获（前面讨论过了），但**部署期涟漪没有编译器能检查**——代码里新增了一个环境变量，Kubernetes 的 ConfigMap 需要加一行，Secret 需要配置，可能还需要 IAM 权限绑定。代码编译通过，测试全绿，推到生产环境，启动时因为缺一个环境变量直接崩溃。更糟的情况：环境变量有默认值，不崩溃，但用了错误的默认值默默跑了一周。

AI 在这件事上有一个人类不具备的优势：**它看到了完整的 diff。** 人类在改代码的时候，注意力在业务逻辑上，部署影响是"回头再说"的事——然后就忘了。我们在规则文件中要求 AI 在任务结束时自动输出部署影响清单：

```
## Deploy Impact

- [ ] Add `NEW_API_KEY` to `linewise-deploy/overlays/dev/secrets.yaml`
- [ ] Add `NEW_API_KEY` to `linewise-deploy/overlays/testing/secrets.yaml`
- [ ] Add env ref in `linewise-deploy/overlays/dev/deployment-patch.yaml`
- [ ] Verify IAM binding for new service account scope
```

这其实是"签名即契约"原则从代码层延伸到了基础设施层。代码的类型签名是代码和调用方之间的契约；部署配置是代码和运行环境之间的契约。两者的共同点是：**让隐式依赖变成显式清单。** 区别在于：类型系统是自动的、强制的、零成本的；部署影响分析是 AI 辅助的、advisory 的、需要人类确认的。但即使是 advisory 的，也比"全靠人记"强一个数量级。

这一层的人机分工是：**AI 是扫描器，人类是裁决者。**

四层从上到下，人类参与度递增：

| 层次          | 人类角色           | 频率        |
| ------------- | ------------------ | ----------- |
| 编译器强制    | 选择语言和类型系统 | 一次性      |
| 可执行规则    | 把隐性知识显式化   | 持续维护    |
| 流程约束      | 设计 AI 的工作流程 | 偶尔调整    |
| Advisory 规则 | 在 AI 建议上做裁决 | 每次 review |

这呼应了文章开头的核心论点：**人类的脑力是有限且宝贵的。** 分层的目的就是把人类的注意力集中到第四层——真正需要业务判断的地方，前三层尽量让编译器和规则自动处理。

产品质量 = 代码质量 × 运维质量。类型系统守住代码质量，规则驱动的影响分析守住运维质量。两者缺一不可。

## 真正的门槛

很多人说"拥抱 AI"没有门槛，有 token 就行。

**还挺有门槛的。**

看看 OpenClaw ——那么多 vibe coding 大师，甚至已经被 OpenAI 收编了，也没写出来多好的 agents.md 文件。为什么？因为 **agent 需要非常清晰具体的指引才能做事**，而写出这种指引需要两个条件：

1. 你自己得足够理解你要 AI 做什么（领域专精）
2. 你得能识别自己表达中的歧义（元认知能力）

这也是为什么 agent 编码在某些方面越来越强——修类型体操、读报错天书越来越容易。因为这些东西是**非常明确的**——几百行报错天书，人看不懂，但对 AI 来说是无歧义的符号推理，处理起来很轻松。

相反，看 AI 的 CoT 就知道：**它经常花 2-3 个段落来猜测人类指令的真实意图。** 不是它笨，是人的指令里模糊成分太多了。写 prompt 不需要报班交学费（那是智商税），但你得愿意像写军令一样反复打磨你的指令——这件事本身没人能替你做。

---

# 更大的图景

## 讽刺的结局

FP 几十年来被批评"没个博士学位看不懂"。但在 AI 协作的模型下：

> **人类只读签名——签名恰恰是 FP 最可读的部分。**
> **人类不读实现——实现恰恰是 FP 最劝退的部分。**

FP 的成本（实现层的认知负担）落在 AI 身上——AI 不在乎。
FP 的收益（显式、可验证的类型契约）交给人类——人类只需要确认"对，这个函数确实应该可能失败"。

而且 AI 不只是"不在乎"FP 的复杂度——它在 FP 的模型里实际上**更不容易出错**。就像计算器算 `1+1` 和 `114514+1919810` 花的时间一样，AI 处理类型体操和处理普通赋值语句的单行成本也差不多。但项目不是一行代码，而是几万行代码长年累积。可变状态 + 时序推理意味着每多一行代码，AI 需要追踪的状态空间指数增长；不可变 + 组合则是线性增长。几万行累积下来，错误率差距是量级的。更关键的是，类型系统提供**确定性的即时反馈**——编译失败就是失败，大幅消除了"看起来对了但运行时才炸"的可能性。当然不是完全消除：涉及外部系统、硬件调用、网络超时的场景，类型系统管不到。但在它能管到的范围内（空值、错误路径、参数类型混淆），反馈是即时且确定的。写动态语言的反馈链路就长得多：写完 → 跑测试 → 发现失败 → 猜是哪一步的状态出了问题 → 回溯。

AI 让某些能力变得廉价——类型体操、符号推理、复杂的 monad transformer stacks。**无法廉价化的才是真正珍贵的：判断系统应该做什么，定义正确的抽象边界，决定哪些约束值得编码到类型里。** 计算器不能替代数学家，AI 不能替代架构师。

函数式编程社区等了几十年的"主流化"，没想到推手不是人类程序员的审美转变，而是 AI 对显式类型信息的刚需。而人类要做的，只是把脑力从"读懂 `semiflatMap`"解放出来，花在更值得的地方：**定义系统应该做什么，而不是操心系统怎么做。**

## 下一代 AI-native 语言

如果把本文的逻辑推到极致：**下一代 AI-native 编程语言，可能真的不需要考虑人类的阅读感受了。** 就像今天没有人手写汇编一样——汇编仍然存在，编译器在用它，但人类不直接接触。

未来的编程语言可能会分化成两层：

- **人类层**：纯粹的签名、契约、意图表达——可能更像一种声明式的规范语言
- **AI 层**：为编译器和 AI 优化的实现语言——可读性完全不重要，信息密度和类型精度才重要

这不是科幻。今天的 Scala 3、Rust、Haskell 已经在朝这个方向走了——类型系统越来越表达力强大，实现层越来越被 AI 接管。差的只是最后一步：承认人类不需要读实现，然后把"人类可读性"从实现层的设计约束中彻底移除。

---

# 附录

## 附录一：AI 的工具链——Grep、LSP 与消歧

即使给 AI 接上了 Metals MCP（Language Server Protocol 工具），它在重构阶段仍然更倾向于全程使用正则搜索替换——Grep + 正则替换是它训练数据中最熟练的路径。

但 Grep 有明确的能力边界。经过反复实验，我们梳理出了一个清晰的分工：

**用 Metals（编译器解析）——问题是"编译器把这个解析成了什么？"**

| 场景                                                                   | 为什么 Grep 会失败                                                             |
| ---------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| Given/implicit 解析——"这里 scope 里的 `given Transactor[IO]` 是哪个？" | Grep 搜 `given Transactor` 会出 10+ 候选，无法判断编译器选了哪个               |
| Extension method——"`.pure[F]` 是谁定义的？"                            | `def pure` 在 cats 源码里，但 Grep 无法告诉你哪个 extension 作用于你的具体类型 |
| Opaque type 解包——"`ProjectId` 的底层类型是什么？"                     | Grep 找到 `opaque type ProjectId = UUID`，但链式调用中需要跨文件追踪           |
| 重载解析——"这里调的是哪个 `apply`？"                                   | Grep 找到所有重载，需要人工按参数类型匹配                                      |
| 类型别名 + 继承——"`ConnectionIO` 是否 extends `Sync`？"                | 需要追踪 `type ConnectionIO = Free[...]` → Free → capability 层级，多跳        |
| 通配符导入——"`import doobie.implicits.*` 引入了什么？"                 | Grep 无法解析，需要阅读整个 doobie package object                              |

**用 Grep（文本搜索）——问题是"这个字符串出现在哪里？"**

- 字符串字面量、SQL 列名、配置键、HOCON 值
- 注释、TODO、错误消息
- 跨语言文件（YAML、SQL migration、Dockerfile）

一句话：**"编译器怎么解析的"用 Metals，"这个文本在哪"用 Grep。**

### FQN 的局限与 LSP 的正确用法

我曾经一直纠正 AI 不要写全限定名（`org.springframework.http.HttpHeaders`），觉得太啰嗦。后来我意识到 FQN 确实能消除歧义——AI 看到 `HttpHeaders`，不知道是 `org.springframework.http.HttpHeaders`、`io.netty.handler.codec.http.HttpHeaders` 还是 `java.net.http.HttpHeaders`。

那能不能更进一步，用 SCIP（基于 SemanticDB 的代码索引）给代码文件自动标注 FQN？我让 Claude 评估这个方案：

> FQN 对我确实有用。当我看到 `val vec = Pgvector(chunk.embedding)` 时，我不知道 `Pgvector` 来自 `doobie.postgres`、`o.linewise.core.database.DoobieInstances`、还是其他什么地方。FQN 能瞬间消除这个歧义。但我已经有更好的工具了。

| 需求                             | SCIP 快照                                     | Metals LSP                     |
| -------------------------------- | --------------------------------------------- | ------------------------------ |
| "PgVector 是什么？"              | 读 3 倍膨胀的标注文件                         | `inspect` 一次调用，精确类型   |
| "谁调用了 resolveAuth？"         | Grep 快照（等同于 Grep 源码）                 | `get-usages`，语义级，非文本级 |
| "这个表达式返回什么类型？"       | 快照里没有（SemanticDB 不含子表达式推断类型） | `inspect` 直接返回             |
| "PermissionService 的所有实现？" | Grep FQN 模式                                 | `typed-glob-search`            |

SCIP 快照的代价：**3 倍 token 膨胀**（150 行文件变 450 行）、**数据即时过时**（任何编辑后就不准）、**没覆盖真正的痛点**（debug/重构的瓶颈是 implicit/given 解析链，SemanticDB 不捕获这些，TASTy 才有）。

结论：**给 agent 配置 LSP 工具，让它在遇到歧义时按需查询**，而不是在每一行代码里都背着冗余的全限定路径。

## 附录二：模型间的协作与知识传递

**高级模型写的代码能"教"普通模型。** 用顶级模型（如 opus）编写的高质量代码和 skill，可以有效地指导能力较弱的模型完成开发工作。

各家模型的训练数据里都有大量高质量的开源代码，这些知识本身是存在的。真正的差异在于两点：

1. **权重分配**——同样的知识，不同模型给予的权重不同，导致有些模型能自然地写出高抽象度的代码，有些则倾向于写出更"平庸"的方案
2. **人类对齐的副作用**——这直接取决于 AI 训练师的认知水平。模型在训练过程中会产生一些"鬼点子"——非常规但可能极其有效的策略。如果训练师的认知能力不足以识别这些鬼点子的价值，一看和主流路线不符就直接惩罚掉，这些高价值策略就会在模型中被压制。**认知能力差的人，训练不出好 AI。**

实用技巧：**用高级模型提前在上下文中把这些知识"激活"一遍**——写成 skill、写成示例代码、写成 CLAUDE.md 中的规则——然后普通模型在这个上下文中工作时，就能循着已经铺好的轨道前进，而不是退回到它默认的"安全"风格。

**多模型协作？不如同级互审。** 有人尝试用多家模型互相评审设计文档——opus、gemini、gpt 三家"专家"讨论后投票决策。但实践中，**认知能力差距太大的模型坐在同一张桌子上，不会产生有效讨论。** 两个大学教授讨论科研方案，中间插进来一个小学生，他不会提供"不同视角"，只会拉低讨论的下限。

更有效的方式是：**同级别模型之间互审，但赋予不同的预设立场。** 比如两个 opus，一个扮演"激进重构派"，一个扮演"稳定优先派"——它们有能力理解对方的论点并做出有实质意义的反驳。认知能力不对等的讨论只会退化成"最差模型能理解的水平"。

这本质上和本文的主题是一回事：**如果你在用的工具能处理更高抽象度的信息，就不要为了迁就最弱的环节而降级。** 代码风格如此，模型协作也如此。
