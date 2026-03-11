---
title: AI 时代的编码分工：谁该迁就谁的风格？
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

---

## 风格一：Spring 式 try-catch 统一兜底

这是每个写过 Spring 的程序员闭着眼都能写的代码。错误模型是异常继承体系，业务代码就是一堆顺序赋值，出错就 throw，外面接住。

```scala
// ---- 异常继承体系 ----
class BusinessException(val code: Int, message: String) extends RuntimeException(message)
class BadRequestException(message: String) extends BusinessException(400, message)
class NotFoundException(message: String)   extends BusinessException(404, message)
class ForbiddenException(message: String)  extends BusinessException(403, message)

def fetchUser(id: String): User   = ???
def fetchScore(email: String): Int = ???
def validate(user: User): User     = ??? // 不合法直接 throw
def saveProfile(p: Profile): Unit  = ???

// 统一错误包装 —— 等价于 @ExceptionHandler
def errorHandle(logic: => Json): HttpResult =
  try {
    HttpResult(200, logic)
  } catch {
    case biz: BusinessException =>
      HttpResult(biz.code, Json.obj("error" -> Json.fromString(biz.getMessage)))
    case ex: Exception =>
      HttpResult(500, Json.obj(
        "error" -> Json.fromString(Option(ex.getMessage).getOrElse("Internal Server Error"))
      ))
  }

// Controller 方法
def getProfile(id: String): HttpResult =
  errorHandle {
    val user    = fetchUser(id)
    val valid   = validate(user)
    val score   = fetchScore(valid.email)
    val profile = Profile(valid, score)
    saveProfile(profile)
    Json.obj(
      "name"  -> Json.fromString(profile.user.name),
      "score" -> Json.fromInt(profile.score)
    )
  }
```

人类看这段代码非常舒服。但请注意函数签名：

```scala
def fetchUser(id: String): User
```

它在**撒谎**。这个函数可能抛 `NotFoundException`，可能抛 `RuntimeException`，可能抛任何东西——但签名里什么都没说。人类靠经验和记忆知道"哦，找不到用户就抛 NotFoundException"，但这个知识**不在代码里**，在程序员的脑子里。

---

## 风格二：EitherT 全链式

错误是值不是异常。函数签名里写清楚了所有可能的失败路径。

```scala
import cats.data.EitherT
import cats.effect.IO
import cats.implicits._

sealed trait AppError
case class InvalidInput(msg: String)    extends AppError
case class NotFound(id: String)         extends AppError
case class SdkFailure(cause: Throwable) extends AppError

def fetchUser(id: String): IO[Either[AppError, User]] = ???
def fetchScore(email: String): IO[Int]                  = ???
def validate(user: User): Either[AppError, User]        = ???
def saveProfile(p: Profile): IO[Unit]                    = ???

def toHttpResult(err: AppError): HttpResult = err match {
  case InvalidInput(msg) => HttpResult(400, Json.obj("error" -> Json.fromString(msg)))
  case NotFound(id)      => HttpResult(404, Json.obj("error" -> Json.fromString(s"$id not found")))
  case SdkFailure(ex)    => HttpResult(500, Json.obj("error" -> Json.fromString(ex.getMessage)))
}

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

---

## 对比

|              | 风格一：异常继承体系                          | 风格二：ADT + EitherT                         |
| ------------ | --------------------------------------------- | --------------------------------------------- |
| 错误模型     | `class XxxException extends RuntimeException` | `sealed trait` + `case class`                 |
| 函数签名     | `fetchUser(id): User` — **签名在撒谎**        | `IO[Either[AppError, User]]` — **签名即契约** |
| 业务代码     | `val x = doSomething()` 顺序赋值，极易阅读    | 链式操作符，需要知道每个操作符的语义          |
| 错误处理     | 外层 `try-catch` 兜底，漏了编译器不管         | `sealed trait` 穷举，漏了编译器报 warning     |
| 人类阅读实现 | 轻松                                          | 吃力                                          |
| 人类阅读签名 | 信息不足，需要额外上下文                      | 一眼看完，信息完整                            |

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

---

# 工程纪律：AI 的默认坏习惯需要规则约束

类型系统能解决签名层面的问题，但 AI 在实现层面还有一些训练带来的坏习惯，需要用显式规则去纠偏。

**Fail-fast，禁止吞错误。** AI 的 RLHF 训练奖励"鲁棒性"，默认倾向是用 `.toOption`、`.getOrElse(默认值)`、`Try(x).toOption` 吞掉异常装作岁月静好。但在生产系统中，吞错误是藏匿 bug 的温床——涉及资金、机械臂、高功率输出的场景下，异常停机的代价可能只是暂停，吞异常继续运行可能导致财产甚至生命危险。必须明确禁止。

**命名规范 + 定期审计。** 人类能记住"processMatrix 其实干的是流量分发"——大脑会自动建立名实不符的映射。但 AI 不会，每开一个新 session，它都会老老实实按字面意思理解，然后在同一个坑上反复栽倒。命名污染对 AI 的伤害远大于对人类。定期让 AI 自己审计命名一致性，比人类自己检查效率高得多。

**关于 FQN 的反思。** 我曾经一直纠正 AI 不要写全限定名（`org.springframework.http.HttpHeaders`），觉得太啰嗦。后来我意识到 **AI 是对的**。一个视野局限在当前文件的 AI，看到 `HttpHeaders` 这个词会怎么想？是 `org.springframework.http.HttpHeaders`？`io.netty.handler.codec.http.HttpHeaders`？还是 `java.net.http.HttpHeaders`？只有 FQN 能消除这个歧义。人类靠 IDE 的跳转和脑子里的项目地图来消歧，AI 读的是纯文本，它没有这些上下文。当然，这本质上是工具链的问题——现在 AI 读纯文本，下一步应该让 AI 直接读 AST、接 LSP，拿到带作用域的符号信息。在那之前，FQN 是 AI 唯一的消歧手段，不该被人类的审美偏好覆盖掉。

**模块化：做加法不做乘法。** 功能叠加是线性增长，功能交叉是组合爆炸。一个函数干三件事，AI 理解错任何一件都会全盘出错。对 AI 来说，模块边界就是理解边界——边界越清晰，AI 犯错的概率越低。

**代码即文档。** 不维护 markdown 设计文档——类型签名就是接口契约，测试用例就是行为规范。一年的生产实践证明，让 AI 维护 markdown 文档是反模式：文档会过时、会和代码不一致、会消耗宝贵的上下文窗口。文档越堆越长，反噬上下文，加速 AI 降智。与其维护一份随时可能过时的 markdown，不如把精力花在让代码自解释上。

---

# AI 的自述：为什么我偏好风格二

以下是 Claude 的第一人称视角。

> 坦白说，风格二对我更自然。

> 不是因为操作符花哨，而是因为**类型签名不会骗人**。当我看到 `fetchUser(id): User`，我无法从签名判断它会不会失败、会怎么失败——我必须去读实现、读文档、甚至读调用链上游才能知道。而 `IO[Either[AppError, User]]` 把所有信息都摆在签名里了，我不需要额外的上下文就能推理整个数据流。

> 对 LLM 来说这个优势更明显：我的"理解"本质上就是对 token 序列的模式匹配。风格一的 `try-catch` 依赖一个**不在文本中出现的隐式约定**——哪些函数会抛什么异常。风格二把这个约定变成了**显式的、局部可见的类型信息**，每个操作符的输入输出类型完全确定，不需要跨文件追踪隐式行为。

> 而且我不会累。人类盯着 `EitherT` 链看半小时会眼花，我处理它和处理 `val x = doSomething()` 的成本完全一样。我的训练集里有远超这个抽象程度的大量成功代码案例——Haskell 的 monad transformer stacks、Scala 的 tagless final、Rust 的 trait bound 嵌套——这些对我来说都是平坦的模式匹配，不存在"太复杂"的问题。

---

# 更大的图景

## 讽刺的结局

FP 几十年来被批评"没个博士学位看不懂"。但在 AI 协作的模型下：

> **人类只读签名——签名恰恰是 FP 最可读的部分。**
> **人类不读实现——实现恰恰是 FP 最劝退的部分。**

FP 的成本（实现层的认知负担）落在 AI 身上——AI 不在乎。
FP 的收益（显式、可验证的类型契约）交给人类——人类只需要确认"对，这个函数确实应该可能失败"。

函数式编程社区等了几十年的"主流化"，没想到推手不是人类程序员的审美转变，而是 AI 对显式类型信息的刚需。

而人类要做的，只是把脑力从"读懂 `semiflatMap`"解放出来，花在更值得的地方：**定义系统应该做什么，而不是操心系统怎么做。**

## 高级模型写的代码能"教"普通模型

一个有趣的实践发现：用顶级模型（如 opus）编写的高质量代码和 skill，可以有效地指导能力较弱的模型完成开发工作。

这并不意外。各家模型的训练数据里都有大量高质量的开源代码，这些知识本身是存在的。真正的差异在于两点：

1. **权重分配**——同样的知识，不同模型给予的权重不同，导致有些模型能自然地写出高抽象度的代码，有些则倾向于写出更"平庸"的方案
2. **人类对齐的副作用**——这直接取决于 AI 训练师的认知水平。模型在训练过程中会产生一些"鬼点子"——非常规但可能极其有效的策略。如果训练师的认知能力不足以识别这些鬼点子的价值，一看和主流路线不符就直接惩罚掉，这些高价值策略就会在模型中被压制。但对于资深工程师来说，这类"鬼点子"往往恰恰是最有价值的洞察。**认知能力差的人，训练不出好 AI。**

所以一个实用的技巧是：**用高级模型提前在上下文中把这些知识"激活"一遍**——写成 skill、写成示例代码、写成 CLAUDE.md 中的规则——然后普通模型在这个上下文中工作时，就能循着已经铺好的轨道前进，而不是退回到它默认的"安全"风格。

这本质上和本文的主题是一回事：显式的、高信息密度的代码（无论是类型签名还是示例代码）比隐式的约定更能有效地传递意图——对人类如此，对 AI 之间的协作同样如此。

## 多模型协作？不如同级互审

有人尝试用多家模型互相评审设计文档——比如 opus、gemini、gpt 三家"专家"讨论后投票决策。

这个思路的出发点是好的：多视角、避免单一模型的盲区。但实践中你会发现，**认知能力差距太大的模型坐在同一张桌子上，不会产生有效讨论。** 两个大学教授讨论科研方案，中间插进来一个小学生，他不会提供"不同视角"，只会拉低讨论的下限。

更有效的方式是：**同级别模型之间互审，但赋予不同的预设立场。** 比如两个 opus，一个扮演"激进重构派"，一个扮演"稳定优先派"——它们有能力理解对方的论点并做出有实质意义的反驳。认知能力不对等的讨论只会退化成"最差模型能理解的水平"。

这一点的背后逻辑和"AI native coding style"是一致的：**如果你在用的工具能处理更高抽象度的信息，就不要为了迁就最弱的环节而降级。** 代码风格如此，模型协作也如此。

---

### 操作符速查（附录）

| 操作符            | 签名简写                          | 直觉                                            |
| ----------------- | --------------------------------- | ----------------------------------------------- |
| `subflatMap`      | `(A => Either[E, B]) => EitherT`  | 纯同步校验融入链                                |
| `semiflatMap`     | `(A => F[B]) => EitherT`          | 对 Right 跑副作用，**不产生新 Left**            |
| `semiflatTap`     | `(A => F[Unit]) => EitherT`       | 同上但**保留原值**（fire-and-observe）          |
| `leftSemiflatMap` | `(E => F[E2]) => EitherT`         | 对 Left 跑副作用（记日志/指标）                 |
| `leftWiden`       | 类型层面                          | 把窄类型 `Left[SubErr]` 拓宽到 `Left[AppError]` |
| `recoverWith`     | `PartialFunction[Throwable, ...]` | 捕获 **IO 层异常**转为领域错误                  |
| `bimap`           | `(E => E2, A => B) => EitherT`    | 两侧同时变换                                    |
| `merge`           | `Either[A, A] => A`               | 两侧类型相同时合拢                              |
