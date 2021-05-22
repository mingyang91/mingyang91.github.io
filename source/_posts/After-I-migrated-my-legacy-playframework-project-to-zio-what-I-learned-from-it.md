---
title: >-
  After I migrated my legacy playframework project to zio, what I learned from
  it.
date: 2021-05-13 18:37:55
tags: 
  - ZIO
  - Scala
  - Play Framework
  - Architecture design
---
- [Foreword](#foreword)
- [What is `R`](#what-is-r)
- [What are the problems caused by DI tools?](#what-are-the-problems-caused-by-di-tools)
- [Current Situation](#current-situation)
- [Evolution Stage 1](#evolution-stage-1)
- [Evolution Stage 2](#evolution-stage-2)
- [Evolution Stage 3](#evolution-stage-3)
- [Conclusion](#conclusion)
- [References](#references)

# Foreword

On April 17, 2020, I start a huge project to migrate the `Future[T]` from legacy playframework project to `ZIO`. Three months later, after tens of thousands of lines of code modification, the migration was a complete success. In September, I used this experience as the background to share in the Chinese Scala Meetup community with the title ["Introduction to ZIO"](https://www.slideshare.net/ssuser81d309/scala-meetup-248313493).
In this share, I explained a fanatic imageation, 
在这次分享中，我展望了一个美好的愿景，借由 `ZIO` 的类型参数 `R` 提供的抽象能力来实现代码的可移植性，和提高可测试性。但想在遗留项目中实现这个愿景并不容易，主要挑战来自遗留项目的代码耦合，和开发者的思维惯性。如今，这个愿景已经达成。我会在这篇 Post 中与你分享我的进化之路。

# What is `R`

> A `ZIO[R, E, A]` value is an immutable value that lazily describes a workflow or job. The workflow requires some environment `R`, and may fail with an error of type `E`, or succeed with a value of type `A`.

上面这段来自 `ZIO` 源码中的注释，其中指出 `R` 是 workflow 所需要的环境参数的类型。我们可以借助这个环境参数，来抽象出过程对环境的依赖。
这听起来非常像依赖注入，实际上确实如此。不同的是，常见的控制反转框架，注入入口都是业务逻辑类的成员以及其构造函数（比如：[spring autowire](https://docs.spring.io/spring-framework/docs/current/reference/html/core.html#beans-factory-autowire)、 [guice](https://github.com/google/guice)、 [macwire](https://github.com/softwaremill/macwire) 等）；而 `ZIO`  的做法是，在运行时提供环对象的实例。

Example:

Spring `@Autowired`: Inject the dependent instance into the object as a member of the class
```Java
public class MovieRecommender {

    private final CustomerPreferenceDao customerPreferenceDao;

    @Autowired
    public MovieRecommender(CustomerPreferenceDao customerPreferenceDao) {
        this.customerPreferenceDao = customerPreferenceDao;
    }

    // ...
}
```
ZIO `R`: Treat the instance as part of the environment, and provide it on demand at runtime
```scala
object MovieRecommender {
    def recommend(): ZIO[CustomerPreferenceDao, Throwable, RecommendResult] = {
      ...
    }

    // ...
}
```

# What are the problems caused by DI tools?
I want to ask the reader a question: ***How much does it cost to test a small feature in your software system?***

See: [Negative example](https://github.com/mingyang91/scala-meetup/tree/master/src/main/scala/meetup/di/legacy)。

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

  cs.simpleCake()
    .onComplete(println)

}
```

I just want to test a small part of the functions, why do I need to construct all dependent instances. Why do I have to do so much preparation to test this simple function. Because it belongs to the method of the class, and this class has too many construction parameters, these construction parameters are unnecessary for the function we want to test


若想让工程代码最大程度上可移植、可测试，一个简单易行的方法是：***不要在类中编写与对象无关(no use `this`)的函数，将他们移动到 `object` 中(in java: mark method `static`)。***同时，编写引用透明的代码对达成这一目标有正面作用。

但是，在遗留项目中实现这一点有些困难,  因为大多数开发者都把依赖注入框架错用了，就像上面的反面教材一样。Even Spring contributors made the same mistake. See: [Spring's sample project](https://github.com/spring-projects/spring-petclinic/blob/main/src/main/java/org/springframework/samples/petclinic/owner/OwnerController.java)

Too many irrelevant dependencies have brought huge obstacles to the portability of codes, turning them into ad hoc codes that are difficult to test.

The whole system is like a balls made up of strings and knots.
![Software System like a ball made up of strings and knots](/images/mass-string-ball.jpeg)


# Current Situation

社区中的方案...
zio layer 每次 unsafeRun 都会重新生成，这很纯函数式，但这不符合 web 服务。例如连接池

遇到的问题
* 连接池
* 信号量

所以，我只能自己尝试：


# Evolution Stage 1

ZioController + PlayRunner

# Evolution Stage 2

ZController + ZRunner
```scala
```

```scala
```

# Evolution Stage 3

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
  def flow(endpoint: String, url: String, body: RawBuffer): ZIO[Has[WSClient], Throwable, String] = ???
}

class ExampleController(cc: ControllerComponents,
                        config: ExampleController.Config,
                        MAction: MemberAction)
                       (implicit val runtime: Runtime.Managed[Has[WSClient]],
                        val ec: ExecutionContext)
  extends AbstractController(cc) with ZController[Has[WSClient], MemberRequest, RawBuffer] {

  def handle(url: String): Action[RawBuffer] = MAction(parse.raw) zio { request: MemberRequest[RawBuffer] =>
    flow(config.endpoint, url, request.body)
      .map(name => Ok(name))
      .mapError(e => InternalServerError("Oh no!\n" + e.getMessage))
      .merge
  }
}

```

# Conclusion


# References

[Dependency Injection Trade-offs](https://www.markopapic.com/dependency-injection-tradeoffs/)