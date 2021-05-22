---
title: What is my learned after added ZIO support to legacy playframework project
date: 2021-05-13 18:37:55
tags: 
  - ZIO
  - Scala
  - Play Framework
  - Architecture design
---
- [当下](#当下)
- [进化 1](#进化-1)
- [进化 2](#进化-2)
- [进化 3](#进化-3)
- [结论](#结论)

In 2020, I participated in the China Scala Meetup as a speaker and shared ["Introduction to ZIO"](https://www.slideshare.net/ssuser81d309/scala-meetup-248313493). The content is, what is i learned from "I spend 3 months for migration from `Future` to `ZIO` in legacy playframework project.

2020 年 9 月我参与了中国 Scala Meetup 并分享《ZIO 入门分享》。其中展望了一个美好的愿景，借由 ZIO 的 R 实现代码的可移植性，来提高可测试性。
但想在遗留项目中实现这个愿景并不容易，主要挑战来自遗留项目的代码耦合，依赖耦合。
参见[反面教材](https://github.com/mingyang91/scala-meetup/tree/master/src/main/scala/meetup/di/legacy)。
仅仅想测试其中一小部分功能，却需要构所有依赖的实例

```scala
package meetup.di.legacy

import meetup.di.legacy.member.{Accountant, Baker, CandyMaker, Cashier, Decorator, HunanChef, Logistic, Manager, Security, SichuanChef, Waiter, Washer}
import meetup.di.legacy.tools.{Mixer, Oven, PipingTip, Turntable}
import meetup.di.legacy.utils.Demo

object djx314 extends App with Demo {
  val mixer = new Mixer()
  val oven = new Oven()
  val pipingTip = new PipingTip()
  val turntable = new Turntable()
  val baker = new Baker(oven, mixer)
  val decorator = new Decorator(mixer, pipingTip, turntable)
  val candyMaker = new CandyMaker
  val scChef = new SichuanChef
  val hnChef = new HunanChef
  val cashier = new Cashier
  val waiter = new Waiter
  val washer = new Washer
  val logistic = new Logistic
  val security = new Security
  val accountant = new Accountant
  val manager = new Manager
  val cs = new CakeShop(
    baker, decorator, candyMaker,
    scChef, hnChef, cashier,
    waiter, washer, logistic,
    security, accountant, manager
  )

  cs.甜在心蛋糕() // <- 测试一个函数的代价
    .onComplete(println)

}
```
Why do I have to do so much preparation to test this simple function.
为什么会这样？因为他是类的方法，而这个类有太多的构造参数，这些构造参数对于我们要测试的函数来说是不必要的。

[反面教材](https://github.com/spring-projects/spring-petclinic/blob/main/src/main/java/org/springframework/samples/petclinic/owner/OwnerController.java)

若想让工程代码最大程度上可移植、可测试，一个容易的方法是”不要将与对象无关(不使用 this)的函数放在类中，将他们移动到 object(or java static) 去。“
当然，尽可能编写纯函数、引用透明也对达成这一目标有正面作用。

但是，在遗留项目中实现这一点非常困难。大部分依赖注入框架都被错用了，就像上面的反面教材一样。

过多的不必要的依赖极大破坏了代码的可移植性，使他们变成难以测试的专用函数、代码。


zio layer 每次 unsafeRun 都会重新生成，这很纯函数式，但这不符合 web 服务。例如连接池
# 当下

社区中的几种方案...

# 进化 1

ZioController + PlayRunner

# 进化 2

ZController + ZRunner
```scala
```

```scala
```

# 进化 3

ZController + Runtime.Managed
```scala
trait ZController[Z, R[_], B] {
  def runtime: Runtime.Managed[Z]

  implicit class ActionBuilderOps(actionBuilder: ActionBuilder[R, B]) {
    def zio[E](zioActionBody: => ZIO[Z, Throwable, Result]): Action[AnyContent] = actionBuilder.async {
      runtime.unsafeRunToFuture(zioActionBody.resurrect)
    }

    def zio[E](zioActionBody: R[B] => ZIO[Z, Throwable, Result]): Action[B] = actionBuilder.async { req =>
      runtime.unsafeRunToFuture(zioActionBody(req).resurrect)
    }
  }
}
```

```scala
  /**
   * A runtime that can be shutdown to release resources allocated to it.
   */
  abstract class Managed[+R] extends Runtime[R] { /* ... */ }
```

使用起来

```scala
object ExampleController {
  case class Config(endpoint: String)
  val flow: ZIO[Has[WSClient], Throwable, String] = ???
}

class ExampleController(cc: ControllerComponents,
                        config: ExampleController.Config,
                        MAction: MemberAction)
                       (implicit val runtime: Runtime.Managed[Has[WSClient]],
                        val ec: ExecutionContext)
  extends AbstractController(cc) with ZController[Has[WSClient], MemberRequest, RawBuffer] {

  def handle(url: String): Action[RawBuffer] = MAction(parse.raw) zio { request: MemberRequest[RawBuffer] =>
    flow
      .map(name => Ok(name))
      .mapError(e => InternalServerError("Oh no!\n" + e.getMessage))
      .merge
  }
}

```

# 结论

