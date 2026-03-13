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

## 实现层的错误处理：三种风格的真实成本

签名即契约解决了"函数边界上的信息完整性"。但在实现层面，同一个逻辑也有不同的组织方式。我曾问 Claude：railway style（链式组合子）对你来说比 nested match/case 更容易处理吗？

它的回答很诚实：**两者对它的认知成本完全一样。**

这个回答其实不够精确。深入追问后，真正的对比轴不是"嵌套 vs 链式"，而是**错误处理的信息局部性**。实际上存在三种风格，它们对 AI 的处理成本有明显差异：

### 风格 A：Early Return Guards + 短路操作符

```rust
fn get_profile(id: &str) -> Result<HttpResult, AppError> {
    if id.is_empty() { return Err(InvalidInput("empty id")) }

    let user = fetch_user(id)?;           // ? 遇到 Err 自动短路
    let valid = validate(user)?;
    let score = fetch_score(&valid.email)?;
    let profile = Profile { user: valid, score };
    save_profile(&profile)?;

    Ok(HttpResult::ok(profile.to_json()))
}
```

每个 guard 是独立的决策点——条件和结果在同一行，自包含。`?` 操作符是隐式的 railway：遇到 `Err` 自动短路返回，不需要手动处理。**AI 处理第 5 行不需要记住第 2 行的分支结构。**

### 风格 B：EitherT Railway 链

```scala
EitherT(service.validate(body))
  .semiflatMap(user => service.fetchScore(user))  // 错误？自动短路
  .foldF(
    err   => BadRequest(err.asJson),
    score => Ok(score.asJson)
  )
```

错误自动沿链传播，只在终点处理一次。AI 只写 happy path，不需要在中间步骤决定怎么处理错误。

### 风格 C：深度嵌套 if-else

```rust
fn get_profile(id: &str) -> Result<HttpResult, AppError> {
    if !id.is_empty() {
        match fetch_user(id) {
            Ok(user) => {
                match validate(user) {
                    Ok(valid) => {
                        match fetch_score(&valid.email) {
                            Ok(score) => {
                                // 真正的逻辑埋在第四层缩进
                                let profile = Profile { user: valid, score };
                                Ok(HttpResult::ok(profile.to_json()))
                            }
                            Err(e) => Err(e)
                        }
                    }
                    Err(e) => Err(e)
                }
            }
            Err(e) => Err(e)
        }
    } else {
        Err(InvalidInput("empty id"))  // 这个 else 对应最外层的 if，距离很远
    }
}
```

happy path 藏在最深层缩进里，`else` 分支和它对应的条件距离很远。AI 必须做长距离的括号配对推理才能理解控制流。

### 真正的对比

|              | 错误处理位置                 | AI 处理成本 | 人类阅读感受 |
| ------------ | --------------------------- | ---------- | ----------- |
| Early Return + `?` | 就地短路，线性流       | **最低**——每行自包含 | 最舒适 |
| EitherT Railway    | 自动传播，终点处理     | **低**——需知道组合子语义，但信息局部 | 需要学习成本 |
| 深度嵌套 if-else    | 远距离 else 分支      | **最高**——长距离 brace 匹配 | 噩梦 |

一个关键洞察：**Rust 的 `?` 本质上就是语法糖化的 railway。** 它和 `EitherT` 的 `semiflatMap` 做的是同一件事——遇到错误自动短路传播——只是穿着命令式的外衣。这说明 railway 语义和人类可读性并不矛盾，语言层面的设计可以让两者兼得。

风格 A 和 B 对 AI 的认知成本接近，且都具备 railway 的核心优势：**错误自动传播，AI 不需要在中间步骤当场决定怎么处理错误——用默认值吞掉是最省事的选择，而 railway 语义从结构上消除了这个诱惑。**

但原文说"两者认知成本完全一样"不够准确。更准确的说法是：**风格 A 和 B 的成本接近且都很低，风格 C 的成本显著更高。** 真正的分界线不是"链式 vs 命令式"，而是"线性流（无论语法形式）vs 深度嵌套"。

Claude 的原话：**"这条规则对我来说零成本遵守，但它产出的代码更统一、更抗静默错误丢弃。最大的赢家不是我，是你们人类审查者。"**

AI-native 的代码风格选择，标准不是"AI 觉得哪个好写"，而是**"哪种风格在结构上减少出错空间"**。签名层如此，实现层同样如此。

## 从签名到契约：表达力的天花板在哪？

> **以下为 Claude 留下的草稿框架，需要结合具体项目经历重写。核心论点和学术引用可参考，示例代码和实践描述需替换为真实场景。**

<!-- TODO(mingyang): 用项目中的真实例子替换 withdraw 示例，补充你在实践中遇到的"类型签名说不出来的约束"的具体场景 -->

前面的例子展示了一条递进的路线：`String` → `ProjectId`（防混淆）→ `NonEmptyList`（防空）→ `Either[AppError, _]`（穷举错误）。但做完这一切，类型签名仍然有说不出来的东西。

<!-- TODO(mingyang): 替换为项目中的真实签名，展示类型诚实但仍有隐含约束的情况 -->

看这个签名：

```scala
def withdraw(account: AccountId, amount: Money): IO[Either[LedgerError, Balance]]
```

类型层面它是诚实的——有副作用，可能失败，成功返回余额。但它**没有说**：

- `amount` 必须大于零
- 返回的 `Balance` 必须 ≥ 0
- 如果 `amount > currentBalance`，必须返回 `InsufficientFunds` 而不是其他错误

这些约束现在藏在哪？**实现里，或者注释里，或者程序员的脑子里**——和我们在文章开头批评的 `fetchUser(id): User` 一模一样的问题，只是换了一个层次。

类型签名能表达"什么类型"，但表达不了"什么条件"。这个表达力缺口在 PL 学术界早有系统研究——Findler & Felleisen 在 [Contracts for Higher-Order Functions (2002)](https://users.cs.northwestern.edu/~robby/pubs/papers/ho-contracts-techreport.pdf) 中正式提出：**传统类型系统缺乏表达 API 全部义务和承诺的能力，契约（Contracts）正是为了弥补这个缺口。**

### 契约的表达力梯度

把前面所有例子放到一条连续的梯度上：

```
Level 0  fetchUser(id: String): User
         → 签名在撒谎。输入类型过宽，错误路径不可见。

Level 1  fetchUser(id: String): IO[Either[AppError, User]]
         → 类型诚实。副作用、错误路径都在签名里。

Level 2  fetchUser(id: UserId): IO[Either[AppError, User]]
         → 领域类型。编译器防止 UserId/OrgId 传反。

Level 3  withdraw(account: AccountId, amount: Money Refined Positive)
           : IO[Either[LedgerError, Balance]]
           ensuring { case Right(b) => b.value >= 0 }
         → 契约完整。前置条件（amount > 0）、后置条件（balance ≥ 0）
           都编码在签名里，编译器 + SMT solver 联合验证。
```

每升一级，签名中编码的信息越多，人类审查时需要的额外上下文越少，AI 实现时的约束越紧、出错空间越小。

### Refinement Types：把契约编进类型

Refinement types 是这条梯度的关键跳跃。微软研究院的 [Principles and Applications of Refinement Types](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/MSR-TR-2009-147-SP1.pdf) 把它定义为 **Floyd-Hoare 逻辑的类型化泛化**——本质上就是把前置条件和后置条件从注释/断言提升到了类型系统层面。

<!-- TODO(mingyang): 补充你在项目中使用 Stainless 或 refined 的真实经历，或者你尝试过但遇到了什么问题 -->

在 Scala 生态中，这已经不是理论：

- **[Stainless](https://github.com/epfl-lara/stainless)**（EPFL LARA）—— Scala 的形式化验证框架。用 `require`（前置条件）和 `ensuring`（后置条件）表达契约，翻译成验证条件交给 SMT solver：

```scala
def withdraw(
  account: AccountId,
  amount: Money,
  current: Balance
): Either[LedgerError, Balance] = {
  require(amount.value > 0)            // 前置条件：金额为正
  // ... 实现 ...
}.ensuring {
  case Right(balance) => balance.value >= 0   // 后置条件：余额非负
  case Left(_) => true
}
```

- **[refined](https://github.com/fthomas/refined)** —— 轻量级 refinement types 库，`NonEmpty`、`Positive`、`MatchesRegex` 等约束在编译期验证，零运行时开销。

### 为什么这对 AI 协作特别重要？

<!-- TODO(mingyang): 补充你自己的实践观察——AI 在有/无契约约束时的行为差异 -->

IEEE 2025 年发表的实证研究 [Preconditions and Postconditions as Design Constraints for LLM Code Generation](https://ieeexplore.ieee.org/document/11218044/) 直接测量了这个效应：**在 prompt 中加入显式的前置/后置条件，显著提升 LLM 代码生成的首次正确率，弱模型的提升尤为明显。**

<!-- TODO(mingyang): 用你的真实经验替换或补充以下段落 -->

这和我们的实践经验完全吻合：给 AI 的约束越精确，它犯错的空间越小。类型签名是一种约束，refinement types 是更强的约束，完整的契约（前置 + 后置 + 不变量）是最强的约束。

而且，Findler & Felleisen 提出的 **blame semantics** 在 AI 协作场景下获得了新的意义：当契约被违反时，blame 机制能精确定位是谁的责任——**AI 的实现违反了后置条件？blame 指向 AI。人类传入了不满足前置条件的参数？blame 指向人类。** 在传统开发中这是调试工具，在 AI 协作中这变成了**分工协议的执行机制**。

### 契约不是银弹

<!-- TODO(mingyang): 补充你在实践中遇到的 refinement types 工具链限制 -->

但必须承认，当前的 refinement types 工具链还不成熟。Stainless 只支持 Scala 的一个纯函数式子集（Pure Scala），refined 库只能表达单值约束，跨调用的不变量仍然需要 SMT solver 介入。完整的 dependent types（Coq、Agda）表达力够了，但验证不可判定，实际工程中难以大规模使用。

这就是为什么我们需要后面讨论的**工程纪律和规则文件**——类型系统和契约能覆盖的部分尽量覆盖（Level 0 → Level 3），覆盖不了的部分用可执行规则补位。两者不是替代关系，而是**同一条防线的不同段**。

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

### 为什么规则文件里充满了绝对化表述

读过我的规则文件的人可能会注意到大量绝对化的断言——"信任编译器，不做额外防御性编程"、"类型系统的判断是最终裁决"、"禁止 `.getOrElse` 静默吞掉错误"。严格来说，这些并不总是对的：编译器有 bug，类型系统有表达力盲区，有些场景确实需要默认值。

但这是**故意的**，而且服务于两个目的。

**第一，信任类型体操的防护。** 前面几节我们花了大量精力把约束编码到类型系统里——`opaque type` 防混淆、`sealed trait` 穷举错误、`NonEmptyList` 防空。既然已经在类型层面投入了这些成本，就应该信任编译器能守住这些防线，**不需要在运行时再加一层防御性检查**。

举个具体的例子：前面提到的 `NonEmptyList`。当一个函数签名写的是 `NonEmptyList[String]`，agent 应该**绝对信任**这个类型——它不可能是空的，不需要在函数体里加 `if (list.isEmpty)` 的防御检查。这个"不可能为空"不是注释里的承诺，不是文档里的约定，而是编译器强制保证的不变量。加防御检查不仅多余，而且有害——它向阅读代码的人（和下一个 session 的 agent）暗示"这个类型可能为空"，污染了类型系统已经建立的信任链。

绝对化表述的第一层意思是：编译器已经在守门了，你不需要在门后面再修一堵墙。

**第二，对抗模型的训练偏差。** 这是更隐蔽的问题。模型在训练阶段见过太多"遇到类型不匹配就用 `.asInstanceOf` 绕过"、"遇到 `Either` 就用 `.getOrElse(默认值)` 吞掉 Left"的代码。这些在训练集中是高频的"成功"模式——代码确实能编译通过、确实能跑。结果就是：**当模型遇到严格的类型约束时，它的第一反应往往不是修正自己的逻辑，而是找捷径绕过约束。**

这个偏差在实践中反复出现，而且不只是 `.getOrElse` 一种形式。它有一整个家族：

```scala
// 形式一：.getOrElse 吞掉 Either 的 Left
val user = fetchUser(id).getOrElse(defaultUser)  // Left 里的错误信息？没了。

// 形式二：try-catch 吞掉异常，转换为默认值
val config = try { parseConfig(raw) } catch { case _: Exception => Config.default }
// 配置文件解析失败？用默认配置跑。不崩溃，但跑的是错误的配置。

// 形式三：IO.handleErrorWith 吞掉真实异常
fetchFromDB(id).handleErrorWith(_ => IO.pure(fallbackValue))
// 数据库连接超时？网络断了？schema 不匹配？全部静默吞掉，返回 fallback。
```

三种形式，同一个模式：**把异常/错误转换为默认值，让代码继续跑下去。** 模型之所以偏爱这个模式，是因为训练数据里这是"让代码编译通过并且不崩溃"的最短路径——而训练奖励的恰恰是"能跑"。

来自配置文件的数据——吞掉。来自数据库的查询结果——吞掉。来自用户提交的输入——吞掉。每一个被吞掉的错误都是一个藏在地毯下的 bug，直到用户问"我的数据去哪了"才被发现。

所以规则文件里写的是：**除非业务场景明确要求默认值（例如 `Option` 的缺省行为），否则禁止用 `.getOrElse`、`try-catch` 兜底、`IO.handleErrorWith` 静默吞掉错误。** 这条规则从字面上看是"绝对禁止"，但它的真实意思是：把默认行为从"吞掉错误"翻转为"传播错误"，只有在人类显式决定"这里确实应该用默认值"时才例外。

两个目的归结到同一个原则：**绝对化表述是对抗训练偏差的校准参数。** 就像矫正视力的镜片——镜片本身是"歪"的，但戴上之后看到的世界是正的。

这也意味着：**规则文件的绝对化程度应该随模型能力变化而调整。** 如果未来的模型不再倾向于绕过类型检查、不再默认吞掉错误，那这些"绝对禁止"就可以放松为"优先避免"甚至移除。规则文件不是宪法，它是针对特定模型版本的校准参数。

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

---

# 适用范围声明

本文的所有实验、观察和结论，都基于当下主流的 transformer 架构——**固定上下文窗口、无跨 session 状态、每次对话从零开始的无状态推理模型。**

这个前提影响的是文章的哪些部分？并非全部。

**架构无关的结论——不会因模型进化而改变：**

- 签名/契约应该诚实完整（§1-§4）。不管什么推理架构，显式信息都优于隐式约定。这是信息论层面的判断，不是对特定模型能力的假设。
- 人类审契约、AI 写实现的分工模型（§3）。这源于人类认知带宽的物理限制，与 AI 的架构无关。
- 类型系统和 refinement types 提供确定性反馈。编译器不会因为 AI 变强而变得不重要。

**架构相关的结论——会随模型能力演进而变化：**

- **纠正训练偏好的规则**（§5 中的 Grep vs LSP 选择、错误处理偏好等）。这些规则本质上是在补偿当前模型的训练偏差。随着模型在现有架构上继续进化，这些偏差会变化——某些坏习惯可能被修正，新的偏差可能出现。**规则文件必须跟随模型能力持续维护微调，这本身就是规则工程的一部分。**
- **跨 session 流程约束**（§6 中的 Code Smell Tracking、memory 文件等）。这些机制完全是为了补偿无状态推理的缺陷。

甚至不需要等到"完美记忆"的那一天。哪怕是一小步——比如 RWKV 这类具备持久化状态的架构，如果推理能力能接近当前 transformer 的水平——就已经能改变游戏规则。

想象这样一个工作流：你花几周时间和一个 agent 协作，它在持久化状态中逐渐积累了对项目编码风格、架构决策、模块边界的理解。然后当你需要并行处理多个任务时，**从这个状态 fork 出多个 session**——每个 fork 都继承了同一份项目认知，可以独立去做 code review、refactor、bug fix，而不需要每个 session 都从零开始读 CLAUDE.md 和 memory 文件。

这和当前的工作模式是本质不同的。现在每开一个新 session，都是一个**新手 agent + 文本化的规则文件**。你必须把所有隐性知识——"这个项目用 tagless final"、"NoOp 实现数据相关的要返回失败"、"持久化后的数据是 trusted"——全部文字化写进规则文件，然后祈祷 agent 能在有限的上下文窗口里正确理解它们。规则文件本质上是在用文本模拟长期记忆——能用，但笨拙，且有 token 预算上限。

而一个积累了项目理解的持久化状态，就像一个在团队待了几个月的工程师：不需要每天早上重新读编码规范，不需要把"我们为什么选择这个架构"写成文档才能记住。**你不再需要文字化描述所有规则，因为规则已经内化在状态里了。**

到那时，本文第二类结论中的大部分——规则文件的精确措辞、跨 session 的 memory 机制、Code Smell Tracking 的文件系统 workaround——都可以大幅简化甚至拆除。规则工程不会消失，但从"事无巨细地文字化"退化为"偶尔纠偏"，负担量级完全不同。

但那一天到来之前，脚手架仍然是必需品。
