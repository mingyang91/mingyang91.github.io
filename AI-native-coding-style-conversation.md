# AI-native Coding Style 对话记录

- 日期：2026-03-11
- 来源：当前 Codex 会话

---

## User

对你来说哪种风格更适合你？

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

---

## 风格二：EitherT 全链式，零 match/case

错误是值不是异常。函数签名里写清楚了所有可能的失败路径，编译器帮你检查有没有漏处理。

```scala
import cats.data.EitherT
import cats.effect.IO
import cats.implicits._

sealed trait AppError
case class InvalidInput(msg: String)    extends AppError
case class NotFound(id: String)         extends AppError
case class SdkFailure(cause: Throwable) extends AppError

def fetchUser2(id: String): IO[Either[AppError, User]] = ???
def fetchScore2(email: String): IO[Int]                  = ???
def validate2(user: User): Either[AppError, User]        = ???
def saveProfile2(p: Profile): IO[Unit]                    = ???

def toHttpResult(err: AppError): HttpResult = err match {
  case InvalidInput(msg) => HttpResult(400, Json.obj("error" -> Json.fromString(msg)))
  case NotFound(id)      => HttpResult(404, Json.obj("error" -> Json.fromString(s"$id not found")))
  case SdkFailure(ex)    => HttpResult(500, Json.obj("error" -> Json.fromString(ex.getMessage)))
}

def getProfile2(id: String): IO[HttpResult] =
  EitherT(fetchUser2(id))
    .subflatMap(validate2)
    .semiflatMap { validUser =>
      fetchScore2(validUser.email)
        .map(score => Profile(validUser, score))
    }
    .semiflatTap(saveProfile2)
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
    .merge                                         // Either[HttpResult, HttpResult] -> HttpResult
    .value
```

## Codex

如果**必须二选一**，我会选**风格二**。  
但如果说“最适合我写、也最适合人维护”的版本，我会选：

**风格二的错误建模 + 风格一的边界收口。**

也就是：

- **业务内部**：错误尽量是值，签名显式表达失败路径
- **接口边界**：统一转成 `HttpResult` / JSON 错误响应
- **真正的异常**：只留给“不可预期”的系统故障，不拿它承载日常业务分支

我偏向风格二，核心原因有 4 个：

- **对 AI 更友好**：`Either[AppError, A]` 把失败路径写在类型里，我不需要“猜你会不会 throw”
- **对重构更安全**：签名一变，编译器会推着改；异常风格很容易漏掉隐式失败点
- **对组合更稳定**：多步骤流程里，值式错误比“半路跳异常”更容易推理
- **对测试更直接**：你测的是返回值，不是到处拦异常

但我**不完全喜欢你这个风格二的写法**，尤其是“**全链式，零 match/case**”这个目标本身。

因为对我来说，最舒服的不是“绝不 `match`”，而是：

- **在真正需要分支的地方，坦然分支**
- **在边界处集中做一次 `AppError -> HttpResult` 映射**
- **不要为了链式而链式**

换句话说，我喜欢的是：

- **显式错误**
- **少隐藏控制流**
- **少样板**
- **保留局部可读性**

所以如果更精确一点说：

### 我最不喜欢风格一的地方
- 失败路径藏在实现里，不在签名里
- `validate(user): User` 这种“看起来纯、实际会 throw”的函数，对 AI 和人都不透明
- 一旦代码变长，异常可能从任何地方冒出来，推理成本高

### 我最不喜欢风格二的地方
- `EitherT` 容易把简单逻辑写成“仪式化函数式管道”
- `recoverWith` 把所有异常都包成 `SdkFailure`，有时会把错误语义冲淡
- “零 match/case”会让代码为了形式牺牲可读性

### 所以我心里的最佳答案是
**不是风格一 vs 风格二，而是：**
**业务逻辑用 ADT + Either/IO，边界统一兜底，但不迷信 EitherT 链式到底。**

如果你这篇文章是写“AI-native coding style”，我会直接给一个判断句：

> **LLM 更偏爱显式错误模型，而不是隐藏在异常里的控制流。**  
> 但 LLM 同样不偏爱过度抽象；比起“纯链式”，它更偏爱“类型明确、边界清楚、局部可读”。

如果你愿意，我可以下一步直接帮你把这段观点改写成一段**适合放进博客正文的中文论述**，语气会更像你这篇文章。

---

## User

这里我需要你考虑到一点，如果整个项目的代码都由你来编写，维护，debug，阅读。
极端FP风格对人类来说阅读负担重，没个博士学位看不懂代码，但是对你来说你的训练集里有远超这个抽象程度的大量成功代码案例。
人类的作用是阅读输入/输出函数签名，确保符合预期。中间过程你来实现/推理。

你的结论是否有变化？

## Codex

会，而且**变化挺大**。

在你这个前提下，优化目标已经变了：

- 不是“让普通工程师顺着读懂中间过程”
- 而是“让我稳定地生成、修改、验证、debug 这套代码”
- 人类主要审核的是**签名、边界、输入输出、测试结果**
- 那么最优解就不再是“叙事型代码”，而是“**约束型代码**”

所以我的结论会从：

- **之前**：`风格二 + 不要过度 FP 仪式感`
- **现在**：**明显更偏向风格二，甚至愿意再往 FP 方向走一些**

**为什么结论会变**
- **类型就是协议**：如果人类只看函数签名，那把业务约束、失败路径、effect 都写进类型，信息密度最高。
- **编译器能替代很多人工 review**：漏处理错误、漏传依赖、返回值不一致，都能更早暴露。
- **对我更容易做局部推理**：纯函数 + 显式 effect + 显式错误，比“可能 anywhere throw”的代码更可预测。
- **大规模重构更机械化**：ADT 改了、签名改了，我可以顺着编译错误一路修下去。

**但注意，不是“越极端越好”**
我会更喜欢的是一种 **AI-friendly FP**，不是“FP 炫技版”：

- 要：`ADT`、`Either/IO/ZIO` 这类显式错误/效果、纯核心/脏边界、统一组合范式
- 不要：过度 `point-free`、自定义操作符泛滥、隐式魔法太多、类型体操、层层 transformer 套娃

原因很简单：

- 那些东西虽然我“见过很多”，
- 但它们会显著增加**局部编辑难度、编译错误复杂度、上下文搜索空间**
- 对“持续生成 + 持续修补”并不总是最优

所以如果你把问题说得更尖锐一点，我的回答会是：

> **如果整个项目都由我来写、维护、debug、阅读，那么我会主动把代码风格推向“强类型 FP 的受控子集”。**

不是为了“学术正确”，而是因为它真的更适合机器维护。

**我的新结论可以概括成一句话：**

> 在 AI-first 项目里，最重要的不是“人类能不能顺着过程看懂”，而是“机器能不能几乎不靠猜测地从签名推导实现、从类型驱动修复”。

所以是的，**在你的设定下，我的结论会变得更偏向风格二**。  
甚至我会说：

- 对**人类主维护**的项目：别太 FP，保持温和显式
- 对**AI 主维护**的项目：可以更 FP，而且应该更 FP
- 但前提是：**统一、克制、可机械化**，而不是炫技

如果你愿意，我可以下一步直接帮你把这段整理成你文章里的一段核心论点，标题甚至可以叫：

- `AI-first codebase 会天然偏向强类型 FP`
- 或者
- `当维护者从人类变成 LLM，可读性的定义就变了`

---

## User

将我们的对话历史，保存为一个md文件
