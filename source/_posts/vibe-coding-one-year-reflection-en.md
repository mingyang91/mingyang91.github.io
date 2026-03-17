---
title: "Ming's Spell Compendium #1 -- One Year of Vibe Coding: A Cold Hard Look"
date: 2026-02-06 13:44:21
tags:
  - AI
  - Vibe Coding
  - Agent
  - Programming
  - Translation
---

> *This is a cultural adaptation — not a literal translation — of the [original Chinese article](/2026/02/06/vibe-coding-one-year-reflection/). Some Chinese cultural references have been swapped for Western equivalents that hit the same emotional note.*

# Foreword

Over the past year I've burned through more than $10,000 in API tokens across Google, Anthropic, and OpenAI. So everything in this article is based on hands-on experience with the strongest models available — Opus 4.6, Codex-5.3-xhigh, Gemini 3 Pro — used without budget constraints.

Those tokens were spread across four categories of projects: embedded kernel drivers, backend architecture, DevOps, and frontend UI. The performance gap between domains is absurd — $20 worth of tokens can vibe-code a passable React dashboard with minimal human guidance, but $2k or even $20k worth of tokens still can't get an agent to produce a working kernel driver on real hardware. The conclusions below are drawn from this cross-domain comparison.

# The Phenomenon: Agent's Crisis of Trust

It's like a late-night infomercial host waving his *Quantum AI Bio-Magnetic Resonance Healing Device™* at the camera, telling you this machine — originally $200,000, but TODAY ONLY $88,000 — will cure your chronic back pain, high blood pressure, diabetes, reverse your arterial plaque buildup, coronary heart disease, and erectile dysfunction.

Agent programming is currently in that exact state.

The agent showers you with emoji celebrating the fact that those 80,000 lines of slop it just generated passed all test cases, and assures you it's ready for production. Do you believe it?

Say you're a project lead, and your most reliable teammate delivers 80% of tasks on time and at high quality. When they guarantee something will ship next week, you can reasonably trust it'll be done by the week after at the latest. But when an *agent* guarantees the code is production-ready right now — do you believe it?

Meanwhile, at this very moment, an army of influencers, course peddlers, and self-appointed "AI Godfathers" are separating suckers from their money. The curriculum basically boils down to: here's how to prompt (tools/skills, same wine in different bottles), then spin up a bunch of agents to work in parallel.

## A Real Case Study

An agent's blind confidence doesn't just mislead the user — it misleads the agent itself.

I once gave an agent this task: integrate GCP Transcoding into the current Kotlin project. I provided the product page and documentation as references and told it to start planning. The agent produced the following plan:

1. After reading the docs, discovered the service only provides a Java SDK, and the current project uses a different JVM language without native support
2. Per the RESTful API docs, manually integrate using ktor-client based on documented field definitions
3. Write the code and run tests

Did you spot the problem in this plan?

If you've ever done this kind of work the old-fashioned way — artisanal hand-crafted coding — you know that manually implementing a RESTful API is never as simple as it sounds. Even covering just the basic Transcoding capabilities involves 5–10 endpoints. Each endpoint's request/response has dozens or even hundreds of nested field definitions, and the agent makes frequent mistakes when dealing with this kind of long-context task.

If instead the agent had chosen to write a thin wrapper around the Java SDK (which Google generates from protobuf anyway), the feature could have been stable and shipped within half a day to a day.

But if you let the agent go down the RESTful path, it'll sink into a debugging swamp — because when AI hallucination causes it to get an optional field name wrong (casing, camelCase, underscores), the program won't throw an error right away. How long until you discover the implementation is wrong? When customers complain after it hits production?

To be fair, agents aren't making zero progress. For example, complex cross-layer debugging — low-probability OS deadlocks, rendering glitches, kernel panics, issues where the call chain is long and spans multiple layers — was completely useless a year ago, but now it's actually net-positive. It can't do full end-to-end root cause analysis, but having the agent draft an effective short-scope investigation plan works surprisingly well. That said, this still requires human leadership — you give it direction, and it executes better and better; but let it choose its own direction, and it'll drive you straight into a ditch.

**Why can't we trust agents?** After a year of practice, I believe the root cause is: we lack effective means of verification.

# The Cause: Total Failure of Verification Methods

## Code Review Has Failed

> Common take: "In a way, AI hasn't really replaced programmers — it's just a new high-level tool. As the person responsible for production code, you still need to understand what it does."

I'd argue this is nearly impossible in practice.

In our internal code reviews, most of the time we were really just reviewing code *style*. The author would walk through the design, we'd give it a once-over, and that was that. This used to work because:

- PRs with sloppy code style also had messy designs, poor performance, and no extensibility
- PRs with clean code style had clear designs, thoughtful performance considerations, and even if there were bottlenecks, they were easy to fix

**But this correlation doesn't exist in the agent coding era — in fact, it's inverted.**

An agent can generate beautifully commented, stylistically flawless — garbage code — in under a minute. When I eyeball it, I regularly get lulled into a false sense of security by that first layer of polish. The thing is, this garbage is hard to catch during review; it usually takes a production incident and a deep investigation to discover it's "chocolate-flavored crap."

Trust me — Opus, Codex-xhigh, those models you can't afford? I've cranked every setting to max and mashed the gas. Same problem.

I also tried having AI review *my* designs. The sycophantic tone is something else — I fed GPT-4o a design I *knew* was flawed, and back came "enterprise-level," "future-proof," "scalable," just blowing smoke up my ass nonstop. I later changed the prompt to make it roleplay as "that insufferable coworker" who criticizes everything, and it got slightly better. But the end result was still underwhelming — AI sees coherent, professional-sounding text and drops its guard, giving high marks even when the content is dead wrong.

## Testing Has Failed

Don't even get me started on testing. Test cases are now also vibe-coded by the agent — it's both the player and the referee, whatever it says goes. It's scammed me more than once. Thousands of lines of getter/setter tests, all green, "ready for production, boss!"

Like the GCP Transcoding example: the agent misspelled an optional field name, and the tests still passed — because the tests were also written by the same agent. Consistently wrong = "correct."

Some people suggest: have different agents specialize — one writes code, another writes tests. I've tried it. It's marginally better than self-testing; obvious bugs do get caught. But these agents share the same training data and systematic biases — their blind spots overlap almost completely. Unlike two human developers — one from an embedded systems background, one from web dev — whose knowledge structures and cognitive blind spots actually complement each other. Two agents, no matter how you split the roles, are fundamentally classmates from the same bootcamp. You've solved the "same person writes and grades the exam" problem, but not the "every exam writer graduated from the same program" problem.

And AI reviewing itself has steeply diminishing returns. If the first review agent missed an issue, the second and third reviews will almost certainly miss it too — unless you can feed them additional error information.

## Comparison with Traditional Industry

At this point someone might ask: don't other industries face this problem after being augmented by machines and automation?

Let me use CNC machining as an analogy:

A CNC machine is more precise than I am, but after it produces a part, we can perform objective physical measurement — grab some calipers, check whether the tolerance is within ±0.01mm. Crystal clear. Even if I couldn't hand-machine a part to that precision, I can still *evaluate* whether the CNC machine and its output meet the standard.

**That's the state of traditional manufacturing after machine augmentation: machines are precise, quality is consistent and stable, and humans can still evaluate the output.**

So what should the ideal state look like for software development after the Agent revolution? The agent delivers code that genuinely covers the requirements, includes basic security protections, and is easier to maintain long-term (even if we only consider agent-maintainability, not human readability), with better performance and lower resource consumption.

But software doesn't just need to satisfy the current requirements doc — it also needs to account for basic security. A feature-complete project riddled with security holes is still failing.

And right now, we can't evaluate whether agents have reached that state. For just the baseline requirement of "feature implementation," agents still can't operate without human guidance and test verification — let alone security, maintainability, and performance.

The problem is: our mainstream verification methods — human review and automated testing — can both be "contaminated" by the agent. It can write stylistically perfect but logically toxic code, and it can write tests that perfectly match the flawed code. What we need is a set of calipers the agent can't tamper with — objective, deterministic verification that doesn't rely on the agent's own judgment.

A CNC machine that achieves great precision on plastic and aluminum parts doesn't necessarily maintain that precision on titanium or stainless steel. The latter tests overall rigidity and the thermal expansion compensation requirements as workpiece mass increases.

Same principle: code that passes a couple of mouse clicks in local testing will, with high probability, blow up spectacularly in production.

**Traditional industry: machines are precise, quality is stable, humans can evaluate. Software industry: agents are fast, coverage is broad, but humans can't reliably evaluate. That's the problem — where are the calipers?**

# The Solution: Let the Compiler Be Your Gatekeeper

Since human evaluation (code review) and automated testing are both unreliable, we need another evaluation method — one that is objective, verifiable, and doesn't depend on the agent's own judgment.

My position runs counter to mainstream AI coding philosophy:

**In the agent coding era, we need *stronger* types, *stricter* verifiable languages — not letting agents run wild with Python, JS, Java, Go, and let's not forget AnyScript.**

Why?

AI piles up slop at such velocity — forget tens of thousands of lines, I'm already too lazy to read line-by-line past 100 lines. But reading type signatures and pre/post-conditions is dramatically faster than reading logic code. And these things can only be provided by Rust, Scala, Haskell, or even formal methods.

I was already writing code this way before agents existed — once your codebase gets large enough, compiler checks are more reliable than eyeballing it. Now that agent coding has become mainstream, I've found that holding agents to this standard is one of the more effective ways to control output quality — only to a degree, of course, but at least better than nothing.

Back to the GCP Transcoding example: if the agent were using a strongly-typed language, misspelled field names would at least get caught by the type system at compile time. But with RESTful + weak typing, errors are silent until it's too late.

But this is only the first line of defense. Strong typing catches type mismatches, null pointer issues, Rust's lifetime errors — these are "syntax-level" problems. The compiler can tell you "this code doesn't compile," but it can't tell you "this code is logically wrong."

## Second Line of Defense: Let z3 Prove It For You

The next level is formal-methods-grade verification — using refinement types or tools like OpenJML to encode business constraints directly into the type system.

A concrete example: have the agent write a sort function. Traditional strong typing ensures the input/output types are correct — takes an array, returns an array. But it can't ensure the returned array is actually sorted. With refinement types, you can write this directly in the function signature:

```
ensures(forall i, j : i < j → arr[i] ≤ arr[j])
```

This pre/post-condition is your "quality tolerance standard." The z3 solver will mathematically *prove* whether the agent's hundred-line sort implementation actually satisfies this constraint for all possible inputs. Proof passes = passes. Proof fails = fails. There's no room for the agent to bluff its way through by insisting "looks fine to me."

**The key insight: humans only need to review this one line of spec to verify it expresses the intended semantics — no need to read hundreds of lines of implementation.** This is the set of calipers the agent can't tamper with.

## Practical Results

First line of defense — credit where it's due. The latest top-tier models can usually pass compilation, unless you're even more obsessed with type-level gymnastics than I am.

In the past, agents hitting Rust lifetime errors or functional type puzzles would loop for dozens of rounds or spiral into infinite retries until context blew up. Formal methods have a steep learning curve to begin with — even the human brain has to maintain continuous abstract symbolic reasoning. I once believed AI would never learn to solve type-level puzzles.

But things have changed. Pure-FP Scala, tagless final — Opus 4.5 and Codex-xhigh follow the patterns quite well, and passing compilation is basically automatic now. Functional type gymnastics produce error messages that are dozens or hundreds of lines of type-theoretic hieroglyphics, and agents can now read and fix these without much trouble.

The crucial point: agents aren't solving type puzzles by cheating (slapping `asInstanceOf` or `any` everywhere). They genuinely fill in the gaps through iterative attempts. This isn't circumvention — it gives me real confidence that AI might actually be able to write code that passes FM checks. If that happens, code correctness gets a formal guarantee, which is far more comprehensive and reliable than unit test coverage.

But the second line of defense is still another world entirely. FM-grade verification errors — z3 solver failures, refinement type constraint violations — agents still struggle badly with these. Though the breakthrough on the first line makes me believe this path has potential.

## Limitations

Of course, this approach has its limits.

In practice, formal methods toolchains and ecosystems are still barren — most only support a very limited subset of a single language. Many engineering patterns and syntax that are bread-and-butter in production code are unsound or unproven in FM land. And that's before we get to the infinite loops and unprovable proofs — one wrong move and the z3 solver is searching a possibility space larger than the observable universe, still grinding away when the heat death arrives.

Strong types and FM solve *some* problems, but not all.

# The Deeper Dilemma: Plan vs. Execute

Even with strong types + FM as evaluation tools, there's a deeper problem: the agent's understanding and execution of plans.

The GCP Transcoding example already exposed this: the agent chose to manually implement RESTful instead of wrapping the Java SDK. This wasn't a coding error — it was **a strategic error**. The compiler can tell you if there's a syntax error; z3 can prove whether your implementation meets the spec; but neither can tell you whether you should be walking this path at all.

A more extreme example: give an agent a complex task — design a rocket engine. The plan calls for a full-flow staged combustion cycle; the approach specifies a coaxial design.

**If the agent doesn't follow the plan:** it might wander off into a gas-generator cycle. The compiler can tell you the code compiles, but it can't tell you whether this is the rocket engine you asked for.

**If the agent follows the plan *too* faithfully:** it actually builds the coaxial design, and then you hit an even bigger problem in production — the dynamic sealing system fails, oxidizer and fuel leak into each other through the turbine shaft, and one of the preburners is about to have a very bad day. The compiler can guarantee type correctness, z3 can guarantee the implementation matches the spec, but neither can guarantee the spec itself is a sound design.

The current plan/edit mode toggle is just a stopgap — an admission that we don't have a better answer yet. This problem is harder than "missing evaluation tools" because it involves understanding requirements and design, not just code quality.

# Peak on First Contact

Agent programming has a striking characteristic: **it peaks on first contact.**

Hand an agent a brand-new CRUD project or a React admin panel, and its first attempt genuinely impresses — clean, well-structured, thoughtfully commented with error handling baked in.

But as the project matures, the unspoken, undocumented, implicitly-understood hidden context keeps growing. Which field is deprecated but never deleted, which API has a historical quirk, which modules have a subtle dependency — the veterans know all this by heart, but nobody ever wrote it down.

And agents can't handle infinite context. They can only selectively forget through compression and summarization. What gets dropped might be the lessons from failed attempts, or it might be critical data structure offsets, register addresses, or enum definitions.

This isn't a feeling. In practice, when context window usage hits ~30% the agent is already noticeably dumber, and at ~50% it's performing worse than the base model. Even when critical details are still technically in-context, the agent will look right through them.

Every time you start a new session, you're facing an almost brand-new "employee" — one that seems to have inherited compressed context (claude.md / agents.md) but knows none of the details. You have to re-explain everything: "No, I know the docs say to pass this parameter, but in practice we never actually send it…"

For CRUD, Spring, and React — highly repetitive tasks — this barely registers as a pain point. It's basically the same thing every time; forgotten, so what.

But for embedded systems development, any forgotten detail gets filled in by the agent's wildly creative hallucinations. Register address wrong? Interrupt priority misconfigured? DMA channel conflict? Minor case: system crash. Major case: permanently fried hardware. This isn't a "fix the bug and redeploy" situation.

Worse still, kernels are riddled with register addresses and flag constants, and these are critical when we're inspecting memory. Once the AI compresses away these details from its context, its next decision could be a completely wrong-direction red herring — not "insufficiently good," but "fundamentally wrong." This is why in these scenarios, I'd rather endure the cognitive degradation from long context than ever let the agent compress. This information genuinely cannot be lost.

And debugging isn't a linear process. We're often holding multiple hypotheses simultaneously, validating each in turn. Path A hits a wall, so we switch to Path B — but that doesn't mean Path A was a dead end. Maybe our understanding just wasn't sufficient at the time. After accumulating new insights on Path B, looking back, that earlier attempt on Path A doesn't seem hopeless after all. So I return to Path A — but the AI? You'll probably be facing a fresh-faced newbie with zero knowledge of everything we previously explored on Path A. Human debugging experience accumulates in spirals; agent memory is one-shot.

# In the Agent Era, Do You Still Need to Learn CS Fundamentals?

Since evaluating agent output is the core challenge, developer fundamentals are obviously still essential. Without them, what are you going to use to evaluate the code, modules, and architectural designs that agents generate? A developer without evaluation capabilities is no different from the retirees getting fleeced at the infomercial gadget store.

So how should you learn?

Open LeetCode, haven't even finished reading the problem, and Copilot has already autocompleted the solution. Hit Submit & Run — top 1%. Is that it?

My take: since we have AI now, of course you can't stay at yesterday's difficulty level. Crank it up. **Crank it up until AI taps out.**

Don't worry — you won't miss any fundamentals. Once the difficulty is high enough, AI hallucinations multiply, and you'll have to fill in every gap yourself. The AI will actively mislead you along the way — but that's precisely the learning opportunity.

Say you want to implement a red-black tree, B-tree, or AVL tree. Crank it up: add formal verification, throw in generics support. Relax — the current strongest models can't do it either.

Hallucinations actually *help* you learn — because they contain common misconceptions. The process of verifying and correcting hallucinations deepens your understanding of the material.

Of course, not everyone needs to jump straight to formal verification. A more practical first step: learn to write specs instead of implementations. Before letting the agent start, write out the pre/post-conditions for the feature in plain English — what conditions the input must satisfy, what constraints the output must meet, which edge cases must be covered. Then use that spec as the agent's acceptance criteria, instead of tossing in a one-liner wish and hoping for the best.

From plain-English specs to property-based tests to refinement types — you can walk this path gradually. But the core competency is the same: **accurately describing what you want.** This is itself a manifestation of CS fundamentals, and it's the single most irreplaceable human capability in the agent era.

# Conclusion

AI frameworks, models, tools, and methodologies are popping up left and right, changing by the day. But at the end of the day, they're all just patches and add-ons for the model.

When humans work through a complete workflow, they don't need to decompose themselves into multiple "sub-agents" to collaborate — because humans genuinely have memory and genuinely learn. The longer you work, the more you grow, the more skilled you become. The hidden context in a project, the pitfalls you've stepped on, the unwritten rules — they all sediment into experience.

Agents are the opposite. The longer the context, the steeper the cognitive decline. Even when details are still technically in context, agents increasingly ignore them, hallucinating things that "look reasonable" to fill in the gaps.

The core problem hasn't changed: we still lack reliable means to evaluate agent output. Strong typing is a partial first-layer solution, FM verification is a partial second-layer solution — but they're both only *partial* solutions.

Skip one day of learning, you'll miss a lot. Skip a whole year, and somehow you haven't missed much at all.

Frameworks and tools iterate and churn, flavor-of-the-month hype cycles come and go, but their marketing far outstrips their actual capability and value. CS fundamentals are the time-tested hard currency. Rather than chasing the next hot framework or tool, invest your energy in strengthening your ability to *evaluate agent output* — that's the truly scarce resource in the agent era.

# Addendum: Kernel NIC Driver Development War Story

After this article was published, readers asked about AI's actual capabilities with cross-layer complex problems. Here's a complete case study.

I once gave a talk at Tsinghua University's open-source OS community, sharing my experience developing a kernel NIC (network interface card) driver with AI assistance. The models at the time were Claude 3.7 through 4.0, and the result was net-negative — 90% of the information was hallucinated misguidance. The AI conflated behaviors from dwmac versions 2.x through 5.x, dragged in Qualcomm and Intel chip code, and don't even get me started on PHY chip registers and C22/C45 protocol details.

Training data for this domain is relatively siloed — vendor documentation is locked behind NDAs and member registrations. The total number of people worldwide who've done end-to-end work on this specific chip is probably under 100. AI has no clean reference material to draw from. The kernel repository has 10–20 years of history, thousands of commits, hundreds of thousands of lines of code, plus a mountain of vendor-specific and architecture-specific workarounds — all of which is noise to the AI.

At first, I was the outsider, and the collaboration model was **AI calls the shots, I do the grunt work** — I'd execute whatever approach the AI suggested and report back with error data. But as I learned more and realized the AI was feeding me nonsense, the roles flipped: **I chart the reverse-engineering path, AI executes** — tirelessly running bit-level comparison experiments over and over. The final conclusions and next-step decisions were co-produced by human + AI, not by letting AI make big autonomous leaps.

This case study actually validates several earlier points: AI hallucination is especially severe in domains with sparse training data; losing register-level details from long context is catastrophic; and the spiral nature of debugging is something current agent architectures simply cannot handle. But in reverse — once the human takes the wheel, AI as a tireless executor doing bit-level repetitive comparison work is genuinely a huge help.

---

Originally published on [Zhihu](https://zhuanlan.zhihu.com/p/2003390589538956495)
