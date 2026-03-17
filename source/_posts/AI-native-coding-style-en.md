---
title: "Ming's Spell Compendium #4 -- The Art of Whipping AI Grunts: FP's Great Comeback?"
date: 2026-03-11 20:00:00
tags:
  - AI
  - Programming
  - Scala
  - Functional Programming
  - Translation
---

> *This is a cultural adaptation — not a literal translation — of the [original Chinese article](/2026/03/11/AI-native-coding-style/). Recurring coined terms: **grunts** = AI agents doing the coding labor; **boss** = the human; **whip-iler** = a portmanteau of "whip" + "compiler" (the compiler that whips misbehaving grunts back in line).*

> **Previously on...** {% post_link AI-and-Human-Whats-Next-en "Ming's Spell Compendium #3 -- AI Programming: The Next Chapter" %}

# Times Have Changed

Let's be honest: in more and more projects, the primary author of the code is already AI. Your coworkers have quietly subscribed to Cursor pro plans or OpenAI's Codex. They toss requirements at the AI every morning, then spend their valuable working hours scrolling Reddit, day-trading meme stocks, nursing their phones back to full charge, ~~and quietly tanking their own projects~~. The human role is shifting from "writing code" to "feeding PRDs to the AI, pretending to review AI code, occasionally deploying some good old workplace gaslighting ('You don't want the job? There's plenty of AI that do.'), and having the AI ghost-write your performance reviews and passive-aggressive emails."

Since we're already there, why not go all the way: **If code is written, maintained, debugged, and read exclusively by AI, why do we still need human readability?** Lord Elon[^1] himself said it: just have AI generate machine code directly. One step, done.

[^1]: "Lord Elon" (马圣) is Chinese internet's sarcastic canonization of Elon Musk — "Lord" used with the same ironic reverence English speakers might say "His Holiness."

I'm not quite that extreme. My position is: **implementation logic doesn't need to cater to human feelings anymore, but interface definitions still do.**

Human brainpower is finite and precious. Hours of complex symbolic reasoning burn out your eyes and your hairline, but AI doesn't get tired. So can we divide the labor like this: **grunts (AI) handle implementation, the boss (human) sips coffee, browses forums, and casually inspects the contracts (function signatures)?**

Nice idea, but here's the catch: for this division of labor to work, the contract (signature) itself must carry enough information. And this is precisely where the mainstream (imperative) and the niche (functional) paradigms fundamentally diverge.

---

# Two Signatures

Same business logic: build a user Profile from a user ID and return JSON.

## Style One: Spring-style try-catch safety net

Hand a mass of monkeys a mass of keyboards — that's roughly the skill floor here. The error model is an exception inheritance hierarchy; business code is just sequential assignment, throw on error, catch outside.

```java
// ---- Exception hierarchy ----
class BadRequestException extends BusinessException(400, message)
class NotFoundException   extends BusinessException(404, message)
class ForbiddenException  extends BusinessException(403, message)

// ---- AOP safety net: @ControllerAdvice + @ExceptionHandler ----
@ExceptionHandler(BusinessException.class)
ResponseEntity handleBiz(BusinessException biz) { ... }

// ---- Service ----
User fetchUser(String id)      { /* ... */ }
int  fetchScore(String email)  { /* ... */ }
User validate(User user)       { /* ... */ }  // throws if invalid
void saveProfile(Profile p)    { /* ... */ }

// ---- Controller: exceptions caught by AOP, no try-catch ----
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

Anyone who's written code can read this without difficulty. But look at the function signature:

```java
public User fetchUser(String id)
```

It's **lying**. This function might throw `NotFoundException`, might throw `RuntimeException`, might throw anything — but the signature says nothing. Humans rely on experience and memory to know "oh, user not found throws `NotFoundException`," but that knowledge isn't in the function signature, isn't in the function body, and you can't exhaustively enumerate it without tracing the entire call tree in your IDE. It's not even in the head of the developer who wrote this function.

## Style Two: EitherT full-chain

Errors are values, not exceptions. The function signature spells out every possible failure path.

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
  // ... each case maps to an HTTP status code, compiler checks exhaustiveness

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

Humans see `subflatMap`, `semiflatMap`, `bimap` and feel like they're reading alien scripture. But look at the function signature:

```scala
def fetchUser(id: String): IO[Either[AppError, User]]
```

It's **honest**. Input is String, might fail (`AppError`), success returns `User`, the whole thing has side effects (`IO`). Humans don't need to spend much effort reading the implementation and documentation to find hidden landmines — the signature itself is a solid contract.

## Comparison

|              | Style One: Exception hierarchy                         | Style Two: ADT + EitherT                               |
| ------------ | ------------------------------------------------------ | ------------------------------------------------------- |
| Error model  | `class XxxException extends RuntimeException`          | `sealed trait` + `case class`                           |
| Signature    | `fetchUser(id): User` — **the signature is lying**     | `IO[Either[AppError, User]]` — **the signature IS the contract** |
| Business code | `val x = doSomething()` sequential assignment, trivial to read | Chained operators, need to know each operator's semantics |
| Error handling | Outer `try-catch` safety net, compiler doesn't care if you miss one | `sealed trait` exhaustive match, compiler warns on missing cases |
| Human reads impl | Easy                                              | Painful                                                  |
| Human reads sig  | Insufficient info, needs extra context             | Complete at a glance                                     |

## AI's Perspective

The comparison above is from the human point of view. What does Claude itself think?

> Honestly, Style Two is more natural for me. Not because the operators are fancy, but because **type signatures don't lie**. When I see `fetchUser(id): User`, I can't tell from the signature whether it can fail, or how. I'd have to read the implementation, the docs, or even trace the upstream call chain. But `IO[Either[AppError, User]]` lays all the information right there in the signature — I don't need any extra context to reason about the entire data flow.

> For an LLM, this advantage is even more pronounced: my "understanding" is fundamentally pattern matching over token sequences. Style One's `try-catch` relies on an **implicit convention that never appears in the text** — which functions throw which exceptions. Style Two turns that convention into **explicit, locally visible type information**; every operator's input and output types are fully determined; no need to trace implicit behavior across files.

> And I don't get tired. A human staring at an `EitherT` chain for thirty minutes will go cross-eyed. For me, processing it costs exactly the same as processing `val x = doSomething()`. My training set contains vastly more complex successful code at this abstraction level — Haskell monad transformer stacks, Scala tagless final, Rust trait bound nesting — these are all flat pattern matching for me. There's no such thing as "too complex."

---

# Optimal Division of Labor: Boss (Human) Reads Contracts, Grunts (AI) Write Implementation

If all the code in a project is written, maintained, and debugged by AI, then:

**Style One's advantage disappears** — implementation readability no longer matters because humans don't need to read implementation line by line.
**Style One's weakness is exposed** — signatures don't contain error information, so humans can't judge correctness from signatures alone during review.

**Style Two's weakness disappears** — no matter how complex `subflatMap` and `semiflatMap` get, that's the grunts' problem. The grunts themselves said they don't get tired, so boss, please save your empathy.
**Style Two's advantage is amplified** — signature IS the contract. Humans only need to look at one line to confirm "yes, this function should indeed possibly return `NotFound`."

This is the optimal division of labor I've discovered:

```
Human:  Review signature ──→ "def fetchUser(id: String): IO[Either[AppError, User]]"
                              ✓ Input is String
                              ✓ Can fail, failure type is AppError
                              ✓ Success returns User
                              ✓ Has side effects
                              → Signature matches expectations. All tests pass.

Grunt (AI):  Implement signature ──→  EitherT(...)
                                       .subflatMap(...)
                                       .semiflatMap(...)
                                       .recoverWith(...)
                                       → Compiles. Types align. Tests fixed.
```

---

# In Practice: Making Signatures Carry More Information

Error handling is just the most basic use case. The "signature IS the contract" principle can be applied across every layer of code. In each comparison below, the left side is how 90% of real projects are written, the right side is the AI-native approach. Just looking at the signatures, you can feel the information gap.

## Primitive Types vs Domain Types

```java
// Traditional: both params are String, swap them and wait for runtime to explode
Project getProject(String id, String orgId)
```
```scala
// AI-native: swap the params and the compiler slaps you
def getProject(id: ProjectId, orgId: OrgId): IO[Option[Project]]
```

The traditional signature hides three problems humans can't spot at a glance: What if `id` and `orgId` are swapped? What if the project isn't found? Returns `null`? And what if someone passes `null` for a parameter? Guess we'll find out when it blows up. In the AI-native signature, `ProjectId`/`OrgId` prevent mix-ups, `Option` says "might not exist," `IO` says "has side effects" — no room for the grunt to screw up.

And since grunts write 90% of the code, defining opaque types isn't "verbose" from their perspective. The grunts should be *thanking* you.

## String Errors vs Exhaustive Errors

```scala
// Traditional: failure info buried in implementation, signature says nothing
def importUrl(url: String): Document  // throws RuntimeException, MalformedURLException, IOException...

// AI-native: failure modes spelled out in the signature
def importUrl(url: String): IO[Either[ImportError, Document]]
// sealed trait ImportError = InvalidUrl | Unreachable | Timeout  ← compiler checks exhaustiveness
```

Where's the exception path info in the traditional version? Maybe in the JavaDoc — **if someone bothered to write it**. Let's be honest about how often your project's JavaDocs get updated per year, and whether they actually match the code's behavior. The pittance the capitalist pays me barely covers implementing the feature, and I'd advise the capitalist not to push their luck. Demand more and I'll start poisoning the documentation before jumping ship. In the AI-native version, the signature itself is documentation that's always consistent — because the whip-iler will mercilessly lash any grunt that drifts off course.

## List + .head Bomb vs NonEmptyList Contract

```scala
// Traditional: List might be empty, calling .head throws NoSuchElementException
def batchEmbed(texts: List[String]): List[Embedding]
// Caller: batchEmbed(userTexts)  ← userTexts is empty? Boom. Nobody checked.

// AI-native: signature enforces non-empty, caller must handle the empty case at call site
def batchEmbed(texts: NonEmptyList[String]): IO[NonEmptyList[Embedding]]
```

In the traditional version, "don't pass an empty array" is a beautiful wish — or a comment saying `// texts must not be empty`. Never mind AI, how many times do *humans* actually read comments before writing code? We deal with it after it explodes. That array came in empty from upstream? `NoSuchElementException` — go talk to the upstream team. `NonEmptyList` elevates that constraint to the type level: the next grunt *must* handle the empty case with `NonEmptyList.fromList`, or it won't whip-ile.

Moreover, in AI-native code, these colored types are enforced throughout the entire pipeline — from the moment external input is received (Request/Input), strict validation and conversion to refined types is mandatory, and only at the system exit (Response/Output) can values be converted back to unrefined types (Int/Long/String). This way, whether it's a fresh grunt, a veteran grunt, or an Alzheimer's grunt after `/compact`, if any of them forget the rules at any layer, the whip-iler will crack the whip.

---

# Implementation-Level Error Handling: Linear Flow vs Deep Nesting

The "signature IS the contract" principle discussed earlier only partially solves "information completeness at function boundaries." At the implementation level, the same logic can be written in different styles. I once interrogated Claude: is railway style (chained combinators) easier for you to process than nested match/case?

Its answer was evasive: **both cost it the same cognitively.**

I knew you were holding back. After deeper interrogation, the real comparison isn't "nesting vs chaining" but rather **information locality of error handling**. There are actually three styles, and AI's token cost for processing them differs noticeably:

### Style A: Early Return Guards + Short-circuit Operators

```rust
fn get_profile(id: &str) -> Result<HttpResult, AppError> {
    if id.is_empty() { return Err(InvalidInput("empty id")) }

    let user = fetch_user(id)?;           // ? short-circuits on Err
    let valid = validate(user)?;
    let score = fetch_score(&valid.email)?;
    let profile = Profile { user: valid, score };
    save_profile(&profile)?;

    Ok(HttpResult::ok(profile.to_json()))
}
```

Each guard is an independent decision point — condition and result on the same line, self-contained. The `?` operator is an implicit railway: encounters `Err`, auto-returns. No manual handling needed. **AI processing line 5 doesn't need to remember line 2's branch structure.**

### Style B: EitherT Railway Chain

```scala
EitherT(service.validate(body))
  .semiflatMap(user => service.fetchScore(user))  // Error? Auto short-circuit
  .foldF(
    err   => BadRequest(err.asJson),
    score => Ok(score.asJson)
  )
```

Errors propagate automatically along the chain, handled only at the terminus. AI writes the happy path only — no need to decide how to handle errors at intermediate steps.

### Style C: Deep Nested if-else

```rust
fn get_profile(id: &str) -> Result<HttpResult, AppError> {
    if !id.is_empty() {
        match fetch_user(id) {
            Ok(user) => {
                match validate(user) {
                    Ok(valid) => {
                        match fetch_score(&valid.email) {
                            Ok(score) => {
                                // Actual logic buried at the fourth indentation level
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
        Err(InvalidInput("empty id"))  // this else matches the outermost if, miles away
    }
}
```

The happy path is buried at the deepest indentation level. The `else` branch is miles away from its corresponding condition. AI must do long-distance brace-matching reasoning to understand the control flow.

### The Real Comparison

|                    | Error handling location   | AI processing cost                                | Human reading experience                             |
| ------------------ | ------------------------- | ------------------------------------------------- | ---------------------------------------------------- |
| Early Return + `?` | Short-circuit in-place, linear flow | **Lowest**: each line is self-contained   | Most comfortable                                     |
| EitherT Railway    | Auto-propagation, handle at terminus | **Low**: need to know combinator semantics, but info is local | FP believers: readable, hard to write. Non-believers: alien scripture |
| Deep nested if-else | Distant else branches    | **Highest**: long-distance brace matching          | "Everyone writes it this way, and the IDE matches braces for me" |

**Rust's `?` is essentially syntactic sugar for a railway.** It does roughly the same thing as `EitherT`'s `semiflatMap` — short-circuit on error, auto-propagate — just wearing an imperative disguise. This tells us that railway semantics aren't just convenient for humans; they also help the grunts get their work done.

After further interrogation, Claude came clean: **"This rule costs me zero to follow, but the code it produces is more uniform and more resistant to silently swallowed errors. The biggest winners aren't me — it's you, the human reviewers."**

The standard for AI-native code style choices isn't "what the grunt thinks is easiest to write" — because alignment bias in training makes it hard to get a straight answer. It's **"which style gives the grunt the least room to screw up."** This applies equally at the signature layer and the implementation layer.

---

# From Signatures to Contracts: Where's the Ceiling of Expressiveness?

The previous examples showed a progression: `String` → `ProjectId` (prevent mix-ups) → `NonEmptyList` (prevent empty) → `Either[AppError, _]` (exhaustive errors). But is this enough?

Take order creation. Suppose we've reached Level 2 — domain types, exhaustive errors, side-effect markers all in place:

```scala
def createOrder(userId: UserId, productId: ProductId, quantity: NonZeroUInt,
                orderTime: Instant, estimatedShipTime: Instant): IO[Either[OrderError, Order]]
```

At the type level it's honest, but not honest enough:

- `estimatedShipTime` must be after `orderTime` — otherwise the delivery driver needs to invent time travel first
- After successful creation, the order status must be `Placed` — if the grunt forgets to set the status, enjoy the customer complaints

Where does this behavioral information live? **The implementation code, or the comments, or the programmer's brain** — the same problem we roasted at the beginning with `fetchUser(id): User`. Signatures can express constraints (swiping right for a girlfriend on the dating app), but not conditions (dear God, she's older than my mother!).

Expanding the full progression:

```
Level 0  def createOrder(userId: String, productId: String, quantity: Int): Order
         → The signature is lying. Swapping userId/productId compiles fine,
           negative quantity goes unchecked, failure paths invisible.

Level 1  def createOrder(userId: String, productId: String, quantity: Int): IO[Either[OrderError, Order]]
         → Honest types. Side effects and error paths are in the signature.

Level 2  def createOrder(userId: UserId, productId: ProductId, quantity: NonZeroUInt): IO[Either[OrderError, Order]]
         → Domain types. Compiler prevents UserId/ProductId mix-up, NonZeroUInt prevents zero values.

Level 3  def createOrder(userId: UserId, productId: ProductId, quantity: NonZeroUInt,
                          orderTime: Instant, estimatedShipTime: Instant)
           : IO[Either[OrderError, Order]]
           requiring { estimatedShipTime > orderTime }
           ensuring  { case Right(o) => o.status == OrderStatus.Placed }
         → Preconditions (ship time after order time) and postconditions (status must be Placed)
           verified by SMT solver. These are pure logical relationships the type system can't express,
           but an SMT solver can prove at compile time.
```

Each level up means more information in the signature, less extra context humans need during review, and tighter constraints on the grunt — less room to screw up.

Level 3 already has tooling support in the Scala ecosystem. EPFL's [Stainless](https://github.com/epfl-lara/stainless) lets you express pre/postconditions with `require`/`ensuring` and hand them to an SMT solver. I've dabbled with Stainless — writing AVL trees was already a stretch, verifying Akka Actor states was incredibly difficult, and it only supports a Pure Scala subset with toolchain maturity still far from production-ready. Rust also has a corresponding [Flux-rs](https://github.com/flux-rs/flux) project. Marking this as future outlook for now.

In current practice, the leap we can stably and easily land is Level 0 → Level 2. For what Level 2 can't cover — like "is inventory sufficient," which requires runtime state — we temporarily rely on test coverage, property-based testing, and human review.

---

# Engineering Discipline: AI's Bad Habits vs Human Correction

The type system solves the problem of ambiguous signature contracts, but beneath the signatures lies a vast terrain of micro-decisions where the whip-iler can't reach. These decisions fall into two categories: correcting AI's training-induced bad habits, and semantic boundaries that humans must personally draw.

## AI's Default Bad Habits

**Fail-fast. No swallowing errors.** The training bias of AI grunts makes them obsessively abuse `.getOrElse`, `try-catch` safety nets, and `IO.handleErrorWith` to bury errors and return default values, pretending everything is fine. This bad habit is so deeply ingrained it needs its own deep dive — the "absolute statements" section in "Rule Engineering" below will analyze three forms of this bias, why absolute rules are needed to counter it, and how banning error-swallowing makes production incident debugging easier.

**Naming conventions + periodic audits.** Humans can remember that "processMatrix actually does traffic routing" — the brain automatically builds a name-reality mapping. But AI doesn't. Every new session, it earnestly interprets names literally, then repeatedly faceplants in the same pit. Naming pollution hurts AI far more than humans. Periodically having AI audit its own naming consistency is far more efficient than humans checking manually.

**Modularity: addition, not multiplication.** Feature stacking is linear growth; feature coupling is combinatorial explosion. When three modules are intimately intertwined, if AI misunderstands or misses any one module, it writes a broken implementation and then thrashes trying to debug it. For the grunt, module boundaries ARE comprehension boundaries — the less it needs to know, the lower the probability of mistakes.

**No crapping all over the codebase with helper functions.** The training data is saturated with successful applications of DRY (Don't Repeat Yourself), so when a grunt encounters two similar blocks of logic, its first instinct is to extract a `def toXxx` or `def convertYyy`. But DRY makes sense for humans: **the person extracting the shared function and the future person using it exist in the same space and can communicate.** But grunts have **no shared memory**. Every new session is a blank slate — it doesn't know that three days ago, another session already wrote a nearly identical helper. The result: after a month of iterative maintenance, the project has a dozen HTTP client wrappers — `HttpHelper`, `ApiClient`, `RequestUtil`, `HttpService` — scattered across different files and modules, with different signatures, roughly the same functionality, each one a session's idea of "I should abstract this," but no session knew another session had already done the same. The more you DRY, the more you repeat — a counter-intuitive trap of AI's stateless nature.

Helper functions don't just create text duplication — they actively harm future grunt sessions by fundamentally breaking **token attention locality**. Inlined code is continuous local symbolic reasoning: the agent reads top to bottom, each line's context is in the surrounding lines, a high-confidence reasoning path. But the moment it hits `toXxx(input)`, the reasoning chain breaks. The agent must jump out of the current code block, fire a tool call to read `toXxx`'s definition. After the definition comes back, it still needs to maintain a **long-distance token attention link** between call site and definition. And inevitably: `grep toXxx` returns multiple same-named functions scattered across different files, and the agent has to read each one, reasoning about which is actually the target. Every jump consumes tokens, bloats context, stretches attention distance — and the longer the attention distance, the higher the probability of reasoning errors. Furthermore, all these similarly-named functions crammed into the context significantly increase hallucination probability: the agent might conflate the first grep result's signature with the last result's function body. The one actually being called might rank last in the grep results, drowned out by the similar functions' tokens ahead of it.

My rule is: **inline by default. Extracting a shared function requires meeting two conditions simultaneously: the logic body exceeds 5 operators, AND explicit human approval.** The agent has no permission to independently decide "I should extract a helper here." That decision belongs to humans, because only humans can judge whether the abstraction is worth introducing, whether it duplicates an existing shared function, and whether it'll cause confusion in future sessions. And once extraction is approved, **that shared function must be inscribed in the rule file** (directly or as a referenced sub-rule), so all subsequent sessions know about its existence and purpose. Otherwise the next session won't know the function exists and will write a new one. A shared function not in the rule file is the same as no extraction at all.

**Code IS documentation (except top-level design).** This rule doesn't mean "write no documentation at all." It means **documentation should only record top-level architecture decisions, not describe code logic or business behavior.**

Good documentation:

> This project uses ffmpeg + nvenc as the encoder, running in a dedicated Kubernetes Pod. See `FFMpegService`, `KubernetesJobService`.

Strictly speaking, the agent could infer this from the code, but it'd need to read `FFMpegService`, trace to `KubernetesJobService`, understand the GPU resource requests in the Pod spec — hundreds of lines, multiple tool calls, burning precious high-intelligence early-context tokens. A one-sentence top-level description lets a new session **skip that reasoning** and invest those valuable early tokens into the main task. And these architectural decisions don't change with every product iteration, so maintenance cost approaches zero.

Bad documentation:

> Before awarding points to a user, check if the user's role is "buyer" — merchant users are prohibited from claiming campaign points. Also check that the user account has been registered for at least 30 days to prevent point-farming. Each user can claim points at most 3 times per day; reject claims beyond that.

Every piece of information in this description can be read directly from the code. Worse, these business rules change frequently as the boss slams the table:
> "What am I paying you tech people for? Can't you just add face verification here?"

and the PM reiterates:
> "Let me emphasize the core logic one more time. I hope you truly understand this time."

When the agent gets a new requirement like "each IP can claim points at most 10 times per day," it faces an unsolvable dilemma: when the documentation's described behavior conflicts with the code, **should it modify the code to reflect the documentation, or modify the documentation to reflect the code?** And after adding the new requirement, should it re-align the documentation's existing descriptions with the current code?

A year of production practice has proven: having AI maintain detailed business logic in markdown docs is a disaster. Docs deceive new agent sessions, pile up endlessly, cannibalize context, and accelerate AI cognitive decline. Rule: **documentation records only top-level architecture decisions and technical rationale; business logic behavior is self-explanatory through code + type signatures + test cases.**

## Boundaries Humans Must Draw

The bad habits above can be forbidden with blanket rules. But some decisions aren't "right or wrong" — they're "what's appropriate in this context," and these judgments must be explicitly provided by humans in the rule file.

**Trusted vs Untrusted: Draw the trust boundary.** "No swallowing errors" doesn't mean "throw everywhere." We divide data paths in the rule file into two categories:

| Path type              | Examples                                                    | Strategy                                                  |
| ---------------------- | ----------------------------------------------------------- | --------------------------------------------------------- |
| **Trusted (internal)** | Config files, persisted DB data, internal serialization, system settings | **Throw directly** — an error here is a bug, expose it immediately |
| **Untrusted (external)** | User input, AI-generated content, external API responses (pre-persistence) | **Capture and report** — high probability of errors, feed back to caller |

About **persisted data being trusted**: because the write boundary has strict encode/decode validation, dirty data can't enter the database. If data read from the DB has unexpected formatting, that's on me — I ran a bad migration, or the last commit had an incompatible data structure change I didn't notice. Throwing is correct here; defensive handling would actually mask the problem and corrupt data.

Why leave it to AI to judge? Because I've given the AI clear criteria for the same JSON parsing operation: parsing a config file should throw (bad config? don't start), but parsing a user-uploaded file should return `Left` (users uploading random web novels instead of valid data is perfectly normal). Humans draw this dividing line in the rule file; only then can the grunts execute.

**The same pattern has different correctness in different semantic domains.** This is most visible in NoOp implementations. In tagless final architecture, every service has a NoOp implementation (for testing or when a feature flag is off). The question: should NoOp return success or failure?

```scala
// Data-related NoOp — MUST return failure
// because "operation didn't execute" is fatal for data consistency
class SOPServiceNoop[F[_]: Applicative] extends SOPService[F]:
  def createSOP(...) = Left("Service not available").pure[F]
  def deleteSOP(...) = Left("Service not available").pure[F]

// Data-irrelevant NoOp — CAN return success
// skipping metrics/logging doesn't affect correctness
class MetricsServiceNoop[F[_]: Applicative] extends MetricsService[F]:
  def recordLatency(...)   = Right(()).pure[F]
  def incrementCounter(...) = Right(()).pure[F]
```

If you don't distinguish these two cases in your rules, AI will write all NoOps returning `Right(())`. Looks "robust," but SOPService's NoOp returning success means the caller thinks data was persisted when nothing actually happened. This kind of bug doesn't crash, doesn't throw errors — it only surfaces when a user asks "where did my data go?"

---

# Rule Engineering: More Important Than Tech Stack Choices

In AI-native development, the most important early investment isn't debating MySQL vs PostgreSQL or Spring WebFlux vs Vert.x — **it's building a clear set of rule files.** Good tech choices have value, but a bad tech choice can be migrated, and migration costs have dropped significantly in the AI era. Style drift from missing or ambiguous rules? A few months later you've got a dumpster fire where every session is crapping in a different direction — that's harder to fix than picking the wrong database.

## "Longer Rules = Worse Results" — Really?

Someone cited a paper ([arXiv:2602.11988](https://arxiv.org/pdf/2602.11988)) claiming my rule files are too long, and research shows rule files have a negative effect on agent performance.

The argument: "You write specs, agents.md, every little detail included, as if you think laws get passed and localities automatically obey. Why would the model listen to you?"

I don't dispute the study's conclusion — **yes, existing rule files on GitHub perform worse the longer they get.** But the evaluation's premises aren't practically meaningful:

1. **The benchmark is one-shot bug-fix tasks**, not ongoing maintenance
2. **It measures "was the bug fixed," not "did engineering health improve"**

Anyone who's done engineering knows: patches save the moment but not the future. Patches pile up, this agent fixes and checks out, the next agent eats the mess. I care about the ongoing maintenance perspective, where rule files' value isn't making the current task faster — it's **preventing every new session from pulling the code in a different direction.**

## Detailed ≠ Clear and Actionable

But the paper does hit a real problem: **most rule files are terribly written.** Not because they're too long, but because they're riddled with ambiguity.

Example:

> Rule 1: When it gets dark, go home
> Rule 2: When you're sick, go to the hospital
> So what do you do when you get sick at night?

I had Claude reverse-audit my own rule files and found tons of these conflicts. Even code style constraints contradicted each other. Every time AI hits such ambiguity, its CoT (Chain of Thought) produces paragraphs of "case-by-case analysis" reasoning — reading more files to determine priorities, parsing context to guess the human's true intent.

**The more it reads, the more input tokens, the closer it gets to cognitive decline.**

## Military-Grade Precision

So the goal of rule files isn't "cover everything" but rather: **reduce the situations where AI needs to reason on the spot, read more context, because instructions are vague or ambiguous.**

These things are like military orders — they must be specific enough to execute. I need to eliminate any room for ambiguity.

Slogan-style rules are the deadliest poison. Take "always use tagless final style" — sounds clear, right? But AI starts a new session, writes code that seems fine. Past 30% of the context window, it starts drifting:

```scala
// Rule says "tagless final," AI complies, but gets it wrong
def parseFile[F[_]: Async](parserService: ParserService[F], file: File)...

// Correct approach: ParserService should be a typeclass constraint in the class constructor
class FileProcessor[F[_]: {Async, ParserService}](...)
```

The AI didn't even write `ParserService` as `[F[_]: ParserService]` in the class constructor. Why? Because "always use tagless final style" is a slogan, not an executable instruction. **It doesn't tell AI what to do in specific scenarios.**

The same problem appears with tool usage. Even with LSP (like Scala's Metals MCP) connected, AI still defaults to Grep during refactoring — because 99% of code reading in its training data is plain text search. You must write clearly in the rule file: **which scenarios call for LSP (what did the compiler resolve?) vs which call for Grep (where does this text appear?).** Having good tools isn't enough — you need to teach AI when to use them. (See [Appendix 1](#appendix-1-ais-toolchain--grep-lsp-and-disambiguation) for the detailed Grep vs LSP division of labor.)

### What Military Orders Really Mean: Unambiguous Execution + Unconditional Mutual Trust

I said rule files should be as precise as military orders. But military orders aren't just about "clear writing" — they work because of the **chain of trust**.

Think of the scene in *The Wandering Earth 2* where Zhou Zhezhi orders the engines ignited. The internet is still down, delegates from each nation hesitate. He says just one line:

> **"When the countdown ends, ignite. I believe our people can complete the mission."**

Even though Ma Zhao had already sunk to the bottom, and Tu Hengyu was already somewhat dead. Zhou Zhezhi still believed that even dead men could complete the mission.

Collaboration between agents works the same way. When an agent writing business logic sees the signature `fetchUser(id: UserId): IO[Either[AppError, User]]`, it should **unconditionally trust** that signature — trust that the upstream agent will indeed return `Left(NotFound)` when the user isn't found instead of `throw exception`, trust that the downstream agent will correctly handle this `Either`. It doesn't need to open `fetchUser`'s implementation to verify "does it really return NotFound?" It doesn't need to add a defensive `try-catch` just in case. **Trusting the signature means trusting the comrade who wrote it.** This directly reduces token consumption and reasoning scope — see the "Token Economics" section below for detailed analysis.

This is why **"be pragmatic" is a slogan, and "don't over-defensively program" is also a slogan** — they don't tell the agent specifically *where* to trust and *where* to defend. Military-grade rules say: **what the signature declares, trust unconditionally; what the signature doesn't declare, that's where you defend.**

### Why Rule Files Are Full of Absolute Statements

If you've read my rule files, you might notice heavy use of absolute assertions — "trust the compiler, no extra defensive programming," "the type system's judgment is the final verdict," "`.getOrElse` silently swallowing errors is forbidden." Strictly speaking, these aren't always true: compilers have bugs, type systems have expressiveness blind spots, and open-source libraries have all sorts of bugs — some scenarios genuinely need defense.

But this is **deliberate**, serving two purposes.

**First, protecting the investment in type-level constraints.** We spent significant effort encoding constraints into the type system — `opaque type` prevents mix-ups, `sealed trait` exhausts errors, `NonEmptyList` prevents empty. Having invested these costs at the type level, we should trust the compiler to hold these lines — **no need for runtime defensive checks everywhere on top**. In practice, bugs I write while bleary-eyed far outnumber bugs the compiler sneaks in (14 years in the industry and I've genuinely never had a production incident caused by a compiler bug — thank you, compiler, take a bow).

**Second, countering the model's training bias.** This is the more insidious issue. During training, models saw enormous amounts of "hit a type mismatch → bypass with `.asInstanceOf`" and "got an `Either` → swallow the Left with `.getOrElse(defaultValue)`." These are high-frequency "success" patterns in training data — the code compiles and runs. The result: **when the grunt past 30% context encounters strict type constraints, its first instinct is often not to widen the fix, but to find a shortcut around the constraint.**

So the rule file says: **unless the business scenario explicitly requires a default value (e.g., `Option`'s default behavior), using `.getOrElse`, `try-catch` safety nets, or `IO.handleErrorWith` to silently swallow errors is forbidden.** This rule reads as "absolute prohibition," but its real meaning is: flip the default behavior from "swallow errors" to "propagate errors," with exceptions only when a human explicitly decides "this really should use a default value."

These two purposes are like soldiers standing back to back: absolute rules pull the agent back from training bias and force it onto the "trust the compiler" path; simultaneously, **I promise the project's overall style will maintain consistency — runtime exceptions not declared in type signatures won't appear.** If they do, that's my fault, not the agent's. The agent trusts the type system; I guarantee the type system is worth trusting.

This contract has another advantage that only surfaces during production incident debugging: **banning error-swallowing means the original error information always exists.** When production breaks, the debug agent gets the raw, unaltered exception stack and error type — not some `fallbackValue` spit out by a middle layer's `handleErrorWith`, where you don't even know what the real exception was or which layer it happened at. Rigorous, consistent coding constraints make the entire project's error propagation path predictable: errors propagate from their origin along the path declared by type signatures all the way to the outermost layer, never getting secretly hijacked by defensive code in the middle. The debug agent just follows this path to quickly locate the real fault, rather than staring blind at an error chain truncated by `handleErrorWith`, forced to read multiple files guessing the real exception source, attempting a fix, discovering the guess was wrong, reading more files, guessing again, and so on. **Every instance of masked error is another blind trial-and-error cycle imposed on future debug agents and maintainers.**

**Absolute statements are calibration parameters against training bias.** Like corrective lenses: nearsightedness is an overly convex lens, so concave lenses correct the bias, making the world appear sharp.

This also means: **the degree of absoluteness in rule files should be adjusted as model capabilities evolve.** If future models no longer tend to bypass type checks or swallow errors by default, these "absolute prohibitions" can be relaxed to "prefer to avoid" or even removed. Rule files aren't a constitution — they're calibration parameters for a specific model version.

But with discipline this strict, won't you get the military equivalent of "hold position, never retreat, total annihilation"? Yes. A "no swallowing errors" rule protects code quality 99% of the time — but when a non-critical metrics report failure crashes the entire request, the rule is too aggressive. The solution: **the thing sitting on my shoulders isn't decorative.** Military orders exist to automate 95% of routine decisions, letting human judgment focus on the 5% of exceptions. We have a meta-rule: **when strictly following a rule produces clearly unreasonable results, flag it for human decision rather than quietly working around the rule.** The grunt's job is to execute and report, not to "adapt flexibly" on its own initiative.

## Reverse Audit: Making AI Whip AI

The most effective maintenance method I've found is: **having Claude reverse-audit the rule files themselves.**

Ask directly "hey Claude, how are my rules?" and Claude will just praise you: "Very deep, very insightful, expert-level work." But if I rephrase:

> "Imagine you're a brand-new session's Claude, reading this rule file for the first time. List everything that confuses you: which rules conflict with each other? Which scenarios leave you unsure which rule to follow? Which instructions do you understand the intent of but don't know how to concretely execute?"

That's when it honestly tells me: this conflicts with that; in this scenario both rules apply but give opposite guidance; this rule — I understand what you want, but when facing actual code, I have three possible interpretations.

**This process requires repeated iteration.** My rule files have gone through dozens of revisions. After each revision, I have it audit again, finding new ambiguities. Many of these are things senior Scala engineers take for granted — conventions that don't need to be spoken. But for AI, if you don't write it down, it doesn't know. It knows what you *might* want (training data), but in a new session it can't guess which *specific* version you want, and falls back to the training bias default.

## The Real Barrier

Many people say "embracing AI" has no barrier to entry — just needs tokens.

**It actually has quite a barrier.**

Look at OpenClaw — all those vibe coding masters, even absorbed by OpenAI, and they still haven't produced a particularly good agents.md file. Why? Because **agents need extremely clear, specific guidance to get things done**, and writing such guidance requires two capabilities:

1. You must deeply understand what you want AI to do (domain expertise)
2. You must be able to identify ambiguities in your own expression (metacognitive ability)

This is also why agent coding keeps getting stronger at type gymnastics and reading compiler error hieroglyphics — because these things are **perfectly clear**, unambiguous symbolic reasoning that agents handle effortlessly.

Conversely, read AI's CoT and you'll see: **it frequently spends 2-3 paragraphs guessing the human instruction's true intent.** Then attempts to read several more files, discovers it guessed wrong, **spends another 2-3 paragraphs guessing**, ad infinitum. It's not stupid — the human instructions are just too ambiguous. Writing prompts doesn't require paying for a course (that's a tax on the gullible), but you need to be willing to iterate with Claude, refining your instructions back and forth. Nobody can do that for you.

---

# Four Layers of Constraints

The above covered "how to write rules clearly." But there's a prerequisite question: **not all constraints need to be rules** — some the compiler already handles, some can only rely on human judgment. Cramming everything into the rule file causes the token bloat and instruction conflicts we already discussed.

In practice, I divide constraints into four layers, forming a gradient from "fully automated" to "fully human-dependent":

**Layer 1: Compiler-enforced — no rules needed.** Type signatures, `sealed trait` exhaustiveness, opaque type anti-confusion — these are the compiler's job. Covered extensively in earlier sections. Principle: **if a constraint can be encoded into the type system, don't write it as a text rule.** The compiler never forgets to check; rule files will.

**Layer 2: Clear criteria for pattern selection — must be actionable rules.** Constraints the compiler can't enforce but that have clear if-then criteria. This layer is the rule file's main battlefield.

The Trusted/Untrusted dichotomy discussed earlier belongs here: the compiler can't distinguish "parsing a config file" from "parsing a user upload," but the rule can be written as "persisted data → throw, pre-persistence external data → return Either" — clear criteria, no ambiguity.

Another typical example is **trigger timing for gradual migration**. We wrote a rule:

> When a file is modified for any reason (even just fixing a typo), if a service in that file still uses `Either[String, T]`, you must migrate it to an ADT error enum while you're at it.

This rule solves: **when to repay technical debt.** Without it, AI defaults to minimal changes — asked to fix a bug, it changes only that one line, never touching technical debt. But dedicating a "refactor sprint" to repaying debt lacks urgency and test coverage.

"Fix it when you touch it" is an elegant balance: you're already QA-ing this module for this change, so the incremental testing cost of migration approaches zero. But this strategy is counter-intuitive for grunts — it must be explicitly stated. The rule also has a recursive effect: after migrating the service's error types, the route file that calls it fails to compile, so follow the compiler's guidance and fix the route too. **The rule's scope follows the compiler — no need for humans to worry about boundaries.**

**Layer 3: Cross-session process constraints — use the filesystem to compensate for memory loss.** Agents have no memory. Every new session is a blank slate. This means: **cross-session quality assurance can't rely on the agent's "awareness" — it must be encoded as persistable processes.**

**Code Smell Tracking** is a concrete approach we've developed in practice. While modifying file A, AI frequently reads files B, C, D in passing. It might notice D has an obvious code smell — say, an `Either[String, T]` not yet migrated to a domain error, or severely misleading naming. But if it fixes D now, scope explodes. A simple bug fix becomes a 10-file refactor.

My previous approach was having AI mention at the end of the current task: "by the way, file D has an issue." But when the next session starts, that remark vanishes — I can never recall what the code smell was.

So Claude and I established this rule:

```
Discover code smell in an unrelated file
  → Don't fix immediately (avoid scope creep)
  → Record in memory/code_smells.md (persistent file, max 10 entries, FIFO eviction)
  → Remind human at end of each task
  → Human decides whether to open a dedicated session to address it
```

**AI discovers and records; humans prioritize and trigger.** The filesystem serves as the agent's missing long-term memory. The 10-entry cap prevents infinite list bloat.

It's not a perfect solution, but it genuinely mitigates "continuous code quality degradation" through long-term memory.

**Layer 4: AI suggests + human decides — advisory rules.** Some constraints: AI can identify "this might need attention" but can't judge "is it worth doing." Rules at this layer aren't commands — they're **suggestions**.

**Runtime Assertion Checks (RAC)** are a typical advisory rule. We tell AI in the rule file: on the following critical paths, consider adding runtime assertions:

- Assert balance ≥ 0 after monetary operations
- Assert state machine transition legality (draft → processing → published, no reverse)
- Assert schema matches expected tenant before multi-tenant writes
- Assert vector dimensions match the model (768 for text, 1408 for video)

But the rule also states: **"suggest, not mandatory" — final decision rests with human code review.** Why not mandatory? Because assertions' value depends on business context: a state transition in an internal tool might not warrant an assertion, but one involving money absolutely must. AI can scan all code paths to find candidate locations (its advantage — humans can't check every state transition line by line), but "how severe are the consequences if this path fails" is a business judgment.

**Deployment impact analysis** also belongs to this layer. Code changes have two types of impact: compile-time impact caught by the type system (discussed earlier), but **deployment-time impact has no compiler to check**. A new environment variable in the code means the Kubernetes ConfigMap needs a new line, Secrets need configuration, maybe IAM permission bindings too. Code compiles, tests are green, push to production, service crashes on startup because of a missing environment variable. And the even more hopeless scenario: a fee calculation ratio environment variable defaults to `0` — doesn't crash without configuration, but silently runs with the wrong default for a week until the boss asks:
> "Why hasn't the fee account balance changed in the last week?"

AI has an advantage humans lack here: **it sees the complete diff.** Humans modifying code focus on business logic — deployment impact is "I'll deal with it later" and then forgotten. We require AI in the rule file to automatically output a deployment impact checklist at task end:

```
## Deploy Impact

- [ ] Add `NEW_API_KEY` to `linewise-deploy/overlays/dev/secrets.yaml`
- [ ] Add `NEW_API_KEY` to `linewise-deploy/overlays/testing/secrets.yaml`
- [ ] Add env ref in `linewise-deploy/overlays/dev/deployment-patch.yaml`
- [ ] Verify IAM binding for new service account scope
```

The four layers, top to bottom, with increasing human involvement:

| Layer              | Human role                    | Frequency        |
| ------------------ | ----------------------------- | ---------------- |
| Compiler-enforced  | Choose language & type system | One-time         |
| Actionable rules   | Make implicit knowledge explicit | Ongoing maintenance |
| Process constraints | Design AI's workflow         | Occasional tuning |
| Advisory rules     | Decide on AI's suggestions   | Every review      |

This is the outcome I'm after: **human brainpower is finite and precious.** The purpose of layering is to focus human attention on Layer 4 — where genuine business judgment is needed — while Layers 1-3 are handled automatically by the compiler and rules.

---

# The Bigger Picture

## The Ironic Ending

FP has been criticized for decades as "unreadable without a PhD." But in the AI collaboration model:

> **Humans carefully read signatures — which happens to be FP's most readable part.**
> **Humans skim implementations — which happens to be FP's most off-putting part.**

FP's cost (cognitive burden of implementation) falls on AI: AI doesn't care.
FP's benefit (explicit, verifiable type contracts) goes to humans: humans just need to confirm "yep, looks good, LGTM."

And AI doesn't just "not care" about FP's complexity — it actually **makes fewer mistakes** in the FP model. Like a calculator computing `1+1` and `69420+80085` in the same time, AI's per-line cost for type gymnastics vs plain assignment is roughly identical. But a project isn't one line — it's tens of thousands of lines accumulated over years. Mutable state + temporal reasoning means every additional line exponentially grows the state space AI needs to track; immutable + composition grows it linearly. Over tens of thousands of lines, the error rate gap is orders of magnitude. More critically, the type system provides **deterministic instant feedback** — compilation failure is failure, massively eliminating "looks right but explodes at runtime." Not completely: external systems, hardware calls, network timeouts are beyond the type system's reach. But within its domain (nulls, error paths, parameter type confusion), feedback is instant and certain. Dynamic language feedback loops are far longer: write → run tests → discover failure → guess which step's state went wrong → backtrack.

AI makes certain capabilities cheap: type gymnastics, symbolic reasoning, complex monad transformer stacks. **What can't be made cheap is what's truly precious: judging what a system should do, defining correct abstraction boundaries, deciding which constraints are worth encoding into types.** Calculators can't replace mathematicians; AI can't replace architects.

The FP community has waited decades for its "this time it'll catch on" moment. It seems the most powerful catalyst isn't a shift in human aesthetic taste, but AI's natural affinity for explicit type information. And all humans need to do is free their brainpower from "understanding `semiflatMap`" and spend it where it matters: **defining what the system should do, not worrying about how the system does it.**

## AI-native = ADHD-native

This section is personal, but I think it explains things that are hard to grasp from a purely technical angle.

I have ADHD. In past work, I constantly made small mistakes — swapping variable order, forgetting to update loop state, losing track in deep if-nesting, guessing `i+1` or `i-1` for array bounds by pure luck. My short-term working memory is terrible — like an agent with a limited context window: processing function A's logic, jumping to function B, and when I come back, half of A's context is gone. Jump to another task and back? Details have almost entirely evaporated.

So my gravitating entirely toward FP was practically inevitable. **Immutable data means I don't need to remember "what state is this variable in right now"; type signatures mean I don't need to remember "how can this function fail"; compiler instant feedback means when I forget something, it tells me immediately.** I use the type system to compensate for my short-term memory deficits, just like I have agents use signature contracts to compensate for context window limits.

But ADHD isn't just weaknesses. My long-term memory and episodic memory are strong — decisions made in a meeting months ago, the context behind the decision, why we chose this path instead of that one, I remember more accurately than the meeting notes.
During technical discussions, I frequently get flashes of insight — weird alternative approaches — which get shot down by the meeting moderator for being off-topic. But in agent collaboration, this becomes an advantage: it's like a trigger for reactive knowledge retrieval in an awakened agent.

Putting my cognitive profile alongside AI's:

|              | Me (ADHD human)                      | AI Agent                            |
| ------------ | ------------------------------------ | ----------------------------------- |
| Short-term memory | Poor, easily loses context      | Limited by context window           |
| Long-term memory  | Strong, rich episodic memory    | None (every session starts from zero) |
| Symbolic reasoning | Weak, prone to trivial errors  | Strong, but also makes mistakes     |
| State space reasoning | Very weak, mutable state tracking is a nightmare | Relatively weak, error rate rises with state explosion |
| Compiler feedback | Lifesaver, compensates for my symbolic reasoning deficits | Same lifesaver, corrects its reasoning errors |
| Architectural intuition | Strong, what to split, what to merge | Weak, tends toward local optima |
| Cross-domain association | Strong, but often suppressed in human teams | None, unless human prompts |

**Our weaknesses overlap heavily; our strengths complement perfectly.** What I'm bad at — concrete implementation, symbolic reasoning, state tracking: AI is better. What AI is bad at — architectural decisions, long-term memory, cross-domain association: I'm better. And our shared weakness — complex state space reasoning — if we can't beat it, we go around it.

This is why every design choice in this article points in the same direction: **let the compiler compensate for weaknesses it can (type system, exhaustiveness checking), let AI do what it's good at (implementation, symbolic reasoning), let me do what I'm good at (architecture, rules, cross-domain association).** My architectural designs must shift direction to accommodate our shared weaknesses — more decoupled, more isolated, semantics above all, top-level design oriented toward FP.

AI-native coding style is really the ADHD-native coding style I've been using all along. Not because ADHD is a good thing, but because **the compensatory mechanisms I built for cognitive deficits happen to also suit AI's strengths.** The topic of what role humans play in this division of labor, how they work, and which cognitive habits need changing — that's too big for this article and deserves its own piece.

## "Can't Read AI-Written Code?"

This is the most common objection. AI-written FP chain code — `EitherT`, `semiflatMap`, `bimap` — humans can't read it. What happens when there's a production incident?

**Oh right, as if you can read assembly.**

In today's software stack, from the Java/Scala you write to the machine code actually executing on the CPU, how many layers do you pass through that you can't read? JIT-compiled native code, OS system calls, hardware interrupt handlers — you've never felt unable to debug just because you "can't read those intermediate layers." Because you don't need to read them. You debug at your own abstraction layer.

In fact, in 2026, when senior engineers genuinely need to debug at the assembly level, they **throw the assembly at AI for an explanation.** AI translates assembly into plain language; the engineer reasons on top of the plain language.

FP abstract code works the same way: can't read the `EitherT` chain? Throw it at AI and have it explain in natural language — "this code first fetches the user, validates, then fetches the score; any step failing returns the corresponding HTTP error code." AI can both write this alien scripture and translate it into plain language.

Moreover, FP code's debug difficulty and depth are **far lower** than stateful imperative code:

- **No mutable state**: no need to track "this variable was modified at line 47, then again at line 123, which version does line 200 read?" Pure functions' output depends only on input — same input always yields same output.
- **Explicit error paths**: `Either[AppError, User]` tells you errors are only those few `AppError` cases. No need to guess "might some deep call throw a NullPointerException?"
- **Composability**: every function is an independently testable unit; bug localization scope is naturally small.

## Token Economics

In the "military trust" section I dropped a hot take: **trusting signatures means trusting comrades.** And this trust behavior saves token costs.

**Every act of distrust is a token expense, growing Fibonacci-style.** When an agent doesn't trust the signature, it needs to open `fetchUser`'s implementation to verify "does it really return `Left(NotFound)` when user is not found?" — reading one file. Then discovers `fetchUser` calls `queryDB` — needs to confirm `queryDB`'s error handling too, reading another file. Ten functions each verified once is ten extra file reads. Worse, consider the token billing model: file contents read back from each tool call become input tokens for the next round, and the output reasoning process gets billed as input after the next tool call. In other words, **every token ever generated adds to the price of every future call** — the more files read, the more context bloats, the more every subsequent step's token bill snowballs. Trusting signatures means the agent only needs to read the current file to do its work; distrusting signatures means every additional file read causes the remaining steps' token bills to inflate in lockstep.

Trust chains + scope isolation also open up bigger architectural possibilities:

**Coding agents can be smaller, cheaper, faster.** When scope is tight enough and modules are isolated thoroughly enough, a coding agent doesn't need a global view — it only needs to see the signatures of functions it's responsible for, the signatures of dependency interfaces, and relevant type definitions. **Solving within a given contract is all there is.** It doesn't even need the strongest model — when the task is constrained tightly enough, a mid-tier model with clear signatures and type constraints can do the job correctly. The more precise the contract, the lower the model capability requirement.

**Difficulties can be escalated rather than toughed out.** When a coding agent hits a problem it can't solve within its current scope — a poorly designed signature, a flawed type constraint, or ambiguous requirements — it doesn't need to "best effort" guess and force an implementation. The correct action is to **report the issue back to the orchestrator**, who adjusts the design or clarifies requirements, then assigns it to (possibly another) agent for execution.

**Global consistency is ensured by a dedicated review agent.** After multiple coding agents each finish work in their small scopes, a review agent with a larger context window checks the global changes for consistency — do interfaces align, do error types match, is naming uniform. This review agent doesn't need to understand every function's implementation details — it only needs to audit that the signature-level contracts are self-consistent.

This is my envisioned agent orchestration model:

```
Orchestrator (architect)
  → Decompose tasks, define signature contracts
  → Assign to multiple Coding Agents (soldiers)
     → Each agent solves within its small scope
     → Problems outside scope → escalate to Orchestrator
  → Review Agent (inspector)
     → Check global signature consistency
     → Doesn't read implementations, only contracts
```

---

# Outlook

## Is Code a Liability or an Asset?

There's a widely quoted saying in software: **Code is a liability, not an asset.** Every line of code is future maintenance, comprehension, and modification cost. When you first wrote the code, only you and God knew what it did; after six months in production, only God can still read it.

This is entirely true in traditional development. Technical debt grows exponentially — each layer of hack makes the next hack harder to understand, each "temporary solution" digs a pit for the next maintainer. Taking over a codebase with technical debt, whether adding features or fixing bugs, is an uphill battle. Custom software projects almost have to be maintained by the original team or a domain-specific outsourcing team. Bring in a new group, and just understanding "what does this thing even do" takes months.

But what if we could keep technical debt growing **linearly** instead of exponentially?

All the engineering discipline discussed in previous sections — type signatures as contracts, sealed trait exhaustive errors, opaque type anti-confusion, fix-it-when-you-touch-it gradual debt repayment — share a common goal: **keeping the code comprehensible to new maintainers (human or AI) at any point in time.**

If this goal is achieved, the nature of a codebase fundamentally flips:

**A codebase with strict discipline from day one makes adding features and fixing bugs no longer incredibly difficult.** Not just for me — even developers who aren't the original authors can, to a reasonable degree, add custom features on top of this code, because new agents easily understand what past agents left behind. Signatures are honest, types are precise, error paths are exhaustive — no implicit knowledge that requires "veterans passing it down by word of mouth."

Of course, **architecture-level adjustments still require the original author or a maintainer of equivalent capability and vision.** But for **feature-level development** — adding an API within the existing architecture, fixing a business bug, migrating a data format — the required person-months drop dramatically. Because these tasks are fundamentally "solving within given contracts," and honest signatures plus strict type systems express those "given contracts" crystal-clearly.

**The premise for a codebase transforming from liability to asset isn't "written well" but "maintained well." So can my Art of Whipping AI Grunts bring the cost of "continuous maintenance" to historically low levels?**

## The Next-Generation AI-native Language

Since I've already gone this far with the hot takes, a few more won't hurt: **the next-generation AI-native programming language might genuinely not need to consider human writing or reading experience.** Just like nobody hand-writes assembly today.

Could future programming languages bifurcate into two layers?

- **Contract layer**: pure signatures, contracts, intent expression — possibly more like a declarative specification language
- **Execution layer**: implementation language optimized for compilers and AI — since humans focus their energy on reviewing the contract layer, implementation readability drops dramatically in importance; human writing experience is no longer a design goal; information density and type precision are what matter

This is my science fiction. Today's Scala 3, Rust, and Haskell already have powerful type system expressiveness with implementations that increasingly look like alien hieroglyphics. The next-generation language just needs to: acknowledge that humans don't need to read implementations, then completely remove "human readability" from the implementation layer's design goals.

---

# Applicability Statement

This article has two premises: one about AI architecture, one about project types.

**AI architecture premise:** Today's mainstream transformer architecture — fixed context windows, no cross-session state, stateless inference starting from zero each conversation.

**Project type premise:** All practices discussed in this article apply to a specific class of software projects:

| Applicable                              | Not applicable                                |
| --------------------------------------- | --------------------------------------------- |
| Backend systems, CRUD-heavy business apps | Infrastructure, compilers, embedded, hardware drivers |
| General frontend UI applications        | OS kernels, real-time systems                 |
| Modules composed additively (feature stacking) | Tightly coupled modules (feature interleaving) |
| Mostly soft state, little hard state    | Mostly hard state, little soft state          |
| Data state persisted to external storage | State maintained in-memory in real-time       |

The distinguishing criterion is **the nature of state**. This article assumes the typical scenario: state ultimately persists to a database, in-memory state is ephemeral and reconstructable (soft state). In this scenario, immutable + functional composition has low cost and high benefit, as argued throughout.

But in hard-state-dominant domains — compiler AST transformations, embedded register operations, hardware driver interrupt handling — state itself is the core abstraction, immutable data structure overhead is unacceptable, and tight inter-module coupling is a physical constraint, not a design flaw. In these domains, many of this article's recommendations aren't just inapplicable — they're harmful.

**Language premise:** This article's rule file examples and engineering practices are based on Scala. Scala is multi-paradigm: it lets you write pure FP, imperative, OOP, or any mixture. This means **much of the rule file's constraints exist to pin the agent's behavior to a single Pure-FP paradigm**, preventing drift between multiple legitimate styles. If your project uses Haskell, a large portion of these constraints are unnecessary — the language itself already enforces them.

If this article were translated to Rust, it'd be significantly shorter. Rust's ownership system and borrow checker already eliminate most mutable state issues at compile time — no need for rule files to prohibit them. But even in Rust, I'd still write: **agents are forbidden from independently declaring global mutables (`static mut`, `lazy_static` + `Mutex`, etc.); local mutables (`let mut`) are forbidden from spanning more than 2 scope levels, and absolutely forbidden from escaping the function.** Similarly, I'd enforce agents using `Has<T>` traits for compile-time dependency injection — Rust's version of tagless final: service dependencies expressed through generic constraints `where Ctx: Has<UserRepo> + Has<AuthService>`, not passing a bunch of concrete types in function parameters. The signature-layer design principle doesn't change with the language — only the syntax differs.

And Rust's `let-else` + `?` has even lower reasoning cost for agents than Scala's cats gymnastics:

```rust
let Some(user) = user_svc.find(id).await else { return Err(DomainError::UserNotFound) };
let Some(avatar) = user.get_avatar().await else { return Err(DomainError::AvatarMissing) };
// ... processing logic
Ok(img_blob)
```

Each line is self-contained: input, check, failure path — all closed within the same line. The agent processing line 2 doesn't need to recall line 1's branch structure — exactly the **linear flow** (Style A) analyzed in the "Implementation-Level Error Handling" section, just with Rust combining early return guard and pattern matching into one with `let-else`. For agents, this has a shorter, more local, less error-prone reasoning path than `EitherT(...).subflatMap(...).semiflatMap(...)`.

What the language handles, leave to the language; what the language can't reach still needs rules to fill the gap — this principle is cross-language.

But not every scenario should chase the lowest writing cost. Whether Scala or Rust, I mandate AI use the Reactive Stream pattern. During the writing phase, reasoning about Reactive Streams might cost several times more tokens than an iterator + channel approach (in Rust, even tens or hundreds of times more — ownership, `&mut`, lifetimes, and other constraints might even force you to restructure data types finalized months ago). But this upfront investment pays off: Reactive Stream operators are themselves declarative behavior descriptions. When debugging, agents don't need to chase scattered state mutations across imperative code — they just look at the operator chain: messages being dropped? `.buffer(n, OverflowStrategy.dropHead)` is right there in black and white. Order scrambled? `.unorderedFlatMap(...)` is staring at you. Each operator is a self-explaining behavior declaration; the bug's cause is written in the operator's name. The imperative equivalent? `LinkedBlockingQueue`'s capacity limit is buried in the constructor, whether the queue blocks or drops when full depends on whether the caller uses `put()` or `offer()`, scattered in some corner of the producer code. Order issues are even more hidden: `ExecutorService.submit()`'s multithreaded scheduling makes consumption order a runtime-only observable behavior — nowhere in the code does it say "ordering is not guaranteed." The agent needs to trace queue initialization, producer logic, and thread pool configuration across files to locate the same bug. Today's extra writing tokens buy back massive reading and reasoning tokens for every future agent.

What does the AI architecture premise affect? Not everything.

**Architecture-independent conclusions — won't change with model evolution:**

- Signatures/contracts should be honest and complete (§1-§4). Regardless of reasoning architecture, explicit information beats implicit conventions. This is an information-theory judgment, not an assumption about specific model capabilities.
- The human-reviews-contracts, AI-writes-implementation division of labor (§3). This stems from the physical limits of human cognitive bandwidth, independent of AI architecture.
- Type systems and refinement types provide deterministic feedback. Compilers don't become less important because AI gets stronger.

**Architecture-dependent conclusions — will change as model capabilities evolve:**

- **Rules correcting training preferences** (§5's Grep vs LSP choice, error handling preferences, etc.). These rules fundamentally compensate for current models' training biases. As models continue evolving on existing architectures, these biases will shift — some bad habits may be corrected, new biases may emerge. **Rule files must be continuously maintained and fine-tuned alongside model capabilities — that itself is part of rule engineering.**
- **Cross-session process constraints** (§6's Code Smell Tracking, memory files, etc.). These mechanisms exist entirely to compensate for stateless inference's deficiencies.

We don't even need to wait for "perfect memory." Even one small step — like RWKV-style architectures with persistent state — if inference capability approaches current transformer levels, the game changes.

Imagine this workflow: you spend weeks collaborating with an agent, and it gradually accumulates understanding of the project's coding style, architectural decisions, and module boundaries in its persistent state. When you need to parallelize multiple tasks, **fork multiple sessions from that state** — each fork inherits the same project knowledge, independently handling code review, refactoring, or bug fixes, without each session starting from zero reading CLAUDE.md and memory files.

This is fundamentally different from the current model. Right now, every new session is a **novice agent + text-based rule files**. You must textualize all implicit knowledge — "this project uses tagless final," "NoOp implementations for data-related services must return failure," "persisted data is trusted" — write it all into rule files, then pray the agent correctly interprets them within a limited context window. Rule files are essentially simulating long-term memory with text — it works, but clumsily, with a token budget ceiling.

A persistent state that has accumulated project understanding is like an engineer who's been on the team for months: no need to re-read the coding standard every morning, no need to write "why we chose this architecture" as a document to remember it. **You no longer need to textualize every rule, because the rules are already internalized in the state.**

When that day comes, most of this article's second category of conclusions — the precise wording of rule files, cross-session memory mechanisms, Code Smell Tracking's filesystem workaround — can be drastically simplified or dismantled entirely. Rule engineering won't disappear, but it devolves from "meticulously textualizing everything" to "occasional course corrections" — a completely different magnitude of effort.

But until that day arrives, the scaffolding is still essential.

---

# Appendices

## Appendix 1: AI's Toolchain — Grep, LSP, and Disambiguation

Even with Metals MCP (Language Server Protocol tooling) connected, AI still prefers to use regex search and replace throughout refactoring — Grep + regex is the most well-worn path in its training data.

But Grep has clear capability boundaries. Through repeated experimentation, we've mapped out a clear division of labor:

**Use Metals (compiler resolution) when the question is "what did the compiler resolve this to?"**

| Scenario                                                                | Why Grep fails                                                                     |
| ----------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Given/implicit resolution: "which `given Transactor[IO]` is in scope here?" | Grep searching `given Transactor` returns 10+ candidates; can't determine which the compiler selected |
| Extension method: "who defines `.pure[F]`?"                              | `def pure` is in the cats source, but Grep can't tell you which extension applies to your specific type |
| Opaque type unwrapping: "what's `ProjectId`'s underlying type?"         | Grep finds `opaque type ProjectId = UUID`, but chained calls require cross-file tracing |
| Overload resolution: "which `apply` is being called here?"              | Grep finds all overloads; requires manual parameter-type matching                   |
| Type alias + inheritance: "does `ConnectionIO` extend `Sync`?"          | Requires tracing `type ConnectionIO = Free[...]` → Free → capability hierarchy, multiple hops |
| Wildcard imports: "what does `import doobie.implicits.*` bring in?"     | Grep can't resolve it; requires reading the entire doobie package object             |

**Use Grep (text search) when the question is "where does this string appear?"**

- String literals, SQL column names, config keys, HOCON values
- Comments, TODOs, error messages
- Cross-language files (YAML, SQL migrations, Dockerfile)

One sentence: **"How did the compiler parse it?" → Metals. "Where is this text?" → Grep.**

### FQN Limitations and Proper LSP Usage

I used to constantly correct AI for writing fully qualified names (`org.springframework.http.HttpHeaders`) — felt too verbose. Later I realized FQN genuinely eliminates ambiguity. AI sees `HttpHeaders` and doesn't know if it's `org.springframework.http.HttpHeaders`, `io.netty.handler.codec.http.HttpHeaders`, or `java.net.http.HttpHeaders`.

Can we go further and use SCIP (SemanticDB-based code indexing) to automatically annotate source files with FQNs? I had Claude evaluate this approach:

> FQN is indeed useful for me. When I see `val vec = Pgvector(chunk.embedding)`, I don't know whether `Pgvector` comes from `doobie.postgres`, `o.linewise.core.database.DoobieInstances`, or somewhere else. FQN instantly eliminates this ambiguity. But I already have a better tool.

| Need                                     | SCIP snapshot                                | Metals LSP                        |
| ---------------------------------------- | -------------------------------------------- | --------------------------------- |
| "What is PgVector?"                      | Read 3x-bloated annotated file               | One `inspect` call, precise type  |
| "Who calls resolveAuth?"                 | Grep the snapshot (equivalent to Grep source) | `get-usages`, semantic-level, not text-level |
| "What type does this expression return?" | Not in snapshot (SemanticDB doesn't contain sub-expression inferred types) | `inspect` returns it directly |
| "All implementations of PermissionService?" | Grep FQN pattern                           | `typed-glob-search`               |

SCIP snapshot costs: **3x token bloat** (150-line file becomes 450 lines), **instantly stale** (any edit invalidates it), **doesn't cover the real pain points** (debug/refactoring bottlenecks are implicit/given resolution chains — SemanticDB doesn't capture these; TASTy does).

Conclusion: **give the agent LSP tools and let it query on-demand when it hits ambiguity**, rather than burdening every line of code with redundant fully qualified paths.

## Appendix 2: Inter-Model Collaboration and Knowledge Transfer

**Code written by advanced models can "teach" ordinary models.** High-quality code and skills written by top-tier models (like Opus) can effectively guide weaker models through development work.

All major models' training data contains large amounts of high-quality open-source code — the knowledge itself exists. The real difference comes down to two things:

1. **Weight allocation** — different models give different weights to the same knowledge, causing some to naturally produce high-abstraction code while others default to more "mediocre" solutions
2. **Side effects of human alignment** — this directly depends on the AI trainers' cognitive level. During training, models generate "wild ideas" — unconventional but potentially extremely effective strategies. If trainers lack the cognitive ability to recognize these wild ideas' value, see them diverge from the mainstream, and immediately penalize them, these high-value strategies get suppressed in the model. **People with poor cognitive ability can't train good AI.**

Practical tip: **use an advanced model to "activate" this knowledge in-context ahead of time** — write it as skills, example code, or rules in CLAUDE.md — then when ordinary models work in that context, they follow the rails already laid down instead of retreating to their default "safe" style.

**Multi-model collaboration? Same-tier peer review works better.** Some try having multiple model vendors review design documents — Opus, Gemini, GPT as three "experts" discussing and voting. In practice, **models with too large a cognitive gap sitting at the same table don't produce effective discussion.** Two college professors discussing a research proposal with a grade schooler in the middle — the child won't provide a "different perspective," just drag down the floor of the discussion.

A more effective approach: **same-tier models reviewing each other, but with different assigned stances.** For example, two Opus instances — one playing "aggressive refactor advocate," the other "stability-first conservative" — they have the capacity to understand each other's arguments and mount substantive rebuttals. Discussions between cognitively mismatched models only degenerate to "the weakest model's comprehension level."

This is fundamentally the same theme as this entire article: **if the tools you're using can handle higher abstraction levels, don't downgrade to accommodate the weakest link.** This applies to code style, and it applies to model collaboration.
