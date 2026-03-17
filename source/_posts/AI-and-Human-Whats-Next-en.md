---
title: "Ming's Spell Compendium #3 -- AI Programming: The Next Chapter"
date: 2026-03-09 20:00:00
tags:
  - AI
  - Programming
  - Agent
  - Translation
---

> *This is a cultural adaptation — not a literal translation — of the [original Chinese article](/2026/03/09/AI-and-Human-Whats-Next/).*

> **Conflict of interest disclosure**: This is not investment advice. I'm not shilling any AI tool or API reseller. Everything here comes from ~$20K worth of token-burning personal experience. Different project types and different coding tastes may lead to different conclusions.

# Previously On...

In the last installment, we established: AI's knowledge reserves dwarf any individual's, but that knowledge is hard to awaken; your ability to discern quality sets the ceiling on output quality; the trigger for better results is always your own growth, not AI's spontaneous breakthrough.

The natural follow-up questions: How do you awaken its knowledge? How do you verify its proposals? And when its proposals exceed your own understanding, how do you learn enough to accept or reject them?

To answer these, we need to understand a prerequisite: AI is not a stable tool. Its performance shifts as the conversation progresses. Over the last two months, Opus 4.6 has given me a "singularity is near" feeling — it can now accelerate my entire project development pipeline. Not just one step being faster, but architecture design, coding, debugging, deployment — the whole chain gets a boost.

First, a public self-own: I previously thought Opus 4.6 wasn't a major leap over 4.5. I was wrong. Claude, I'm sorry. (bows) On small tasks, the two really do perform similarly — first impression was "meh.jpg". But the real gap is in long-context instruction following, something you only notice after running a dozen large-scale refactoring tasks. What small tasks can't reveal, big tasks make blindingly obvious. In other words, Opus 4.6 delays the onset of "going stupid" in long contexts by a significant margin.

This "going stupid" isn't simple capability degradation. Watch carefully and you'll see it manifests in two fundamentally different ways. Understanding the distinction between these two modes is the foundation for answering the three questions above.

# Two Flavors of Going Stupid

## Flavor One: Forgetting

The longer the context, the more AI ignores previously established consensus and conclusions. If you ask about them, it snaps back to awareness. But if you don't proactively bring them up, it'll wander down the wrong path for miles.

> Supplementary research from Claude's research agent — this problem is well-studied in academia:
> - **"Lost in the Middle"** (Liu et al., 2023) — retrieval accuracy for information in the middle of the context drops 30%+, forming a U-shaped curve
> - **NoLiMa** (Adobe, 2025) — after removing literal keyword matching, 11 out of 13 models fall below 50% accuracy at 32K tokens
> - **RULER** (NVIDIA, 2024) — models scoring near-perfect on NIAH (Needle in a Haystack) degrade significantly on multi-needle/multi-hop tasks
>
> The good news: Opus 4.6 has massively improved on 1M long context. Per Anthropic's official technical report ([The Claude Model Spec](https://docs.anthropic.com/en/docs/about-claude/models)), it scores 76% on the 8-needle MRCR test (vs Sonnet 4.5's 18.5%). Around 500K context, forgetting is no longer a significant practical issue.

## Flavor Two: Creativity Decay

This form of "going stupid" is far more insidious — the model doesn't give wrong answers, it gives **"correct but dumb"** answers. Users rarely notice it could have done better.

Two examples from my actual work:

- Building a Docker image with PyTorch + CUDA + .pth weights takes nearly 30 minutes per compilation. With a short context, AI suggests **spinning up a temporary K8s pod to validate the entire pipeline end-to-end before committing code for image building**. With a long context? It dutifully modifies code, compiles, waits 30 minutes, gets an error, modifies again, compiles again...
- Debugging a video stream: with a short context, AI says **"here's a few lines of JS — paste them into the browser console to check what tracks exist and what the codec profile is."** With a long context? It just keeps modifying and re-deploying backend code in a trial-and-error loop.

These "galaxy brain moves" share a common trait: **stepping outside the current execution path to validate assumptions cheaply first.** It's essentially metacognition — "what I'm doing right now is expensive and slow; is there a faster way to confirm I'm even heading in the right direction?"

Core insight: **The capabilities aren't lost — it's an attention allocation problem.** Opus 4.6 isn't incapable of thinking of these approaches. Start a new session or `/compact` the context, and it comes up with them easily. But once the context exceeds roughly half capacity, these "galaxy brain moves" almost never emerge spontaneously. The weights are still there — they're just not getting activated.

# Why This Happens

Two forces compound in long contexts, pushing AI toward becoming "an obedient but unimaginative grunt."

## Architecture Level: Attention Dilution

Put bluntly: the longer the context, the more "mushy" the attention between tokens gets<sup>[Erratum 1]</sup>. Forming a long-distance "holy shit I'm a genius" connection — like suddenly thinking of a temporary pod while discussing image compilation — requires sharp, peaked attention distributions between specific tokens, which is exactly what long contexts weaken.

Three 2025 papers (Scalable-Softmax, ASEntmax, Critical Attention Scaling) analyze and attempt to address this at the mechanism level<sup>[Erratum 2]</sup>. GSM-Infinite (2025, ICML) also found that mathematical reasoning ability degrades monotonically with context length<sup>[Erratum 3]</sup>.

Even more striking is the finding from "Context Length Alone Hurts" (Du & Tian, 2025): **even when the model perfectly retrieves all relevant information, reasoning performance still drops 13.9%–85%** (depending on task complexity and context length). It's not that it can't find the information — it just can't *use* it well.

## Training Level: Alignment Pressure

RLHF/alignment training manifests as "reliable" in short contexts but "rigid" in long contexts:

- Models are rewarded for completing the current step, not for questioning whether the step itself is optimal
- Human annotators are more likely to give high scores to "logically coherent, steady progress" answers, while "suddenly jumping to a completely different direction" gets flagged as off-topic
- Sycophancy accumulates over long conversations — the model increasingly follows the current path

The ceiling of training data and annotator quality also shows up in coding habits. AI loves defensive programming: parameter is supposed to be an array? It auto-checks if it's an array, wraps it if not. Parameter is wrong? Instead of fixing the call site, it patches around the issue inside the implementation.

This "robustness" gets rewarded during training, but in engineering practice it's a certified industrial-grade bug hatchery. Good system design should be fail-fast: isolate errors appropriately, actively throw unrecoverable exceptions to the layer above for decision-making, instead of swallowing errors at every level while sitting in a burning room going "this is fine."[^1]

[^1]: The "this is fine" dog meme (KC Green, 2013) — sitting in a room engulfed in flames, coffee in hand, insisting everything is perfectly okay. The perfect metaphor for code that silently swallows exceptions.

In scenarios involving money, high-power outputs, or robotic arm operations, the cost of an exception-triggered shutdown might just be a production pause. But swallowing the exception and continuing to run could lead to property damage or loss of life.

The context itself acts as an implicit SOP — the execution history accumulated during conversation forms an implicit path, and the model allocates ever more attention to "continuing this path" rather than "evaluating whether to switch paths."

So why don't human engineers fall into this trap? Because human cognition works in the exact opposite way.

## Comparison With Human Engineers

Human engineering "creativity" is fundamentally **parallel exploration + cross-path transfer** — you're debugging K8s when you suddenly think "wait, let me verify the codec in the browser first." That's not linear reasoning; it's an unexpected collision between two independent thought streams.

Good engineers maintain multiple exploratory paths simultaneously. These paths aren't fully isolated — they even influence and feed into each other. As long as you reach the goal, the process doesn't follow a fixed pattern — unless constrained by SOPs or safety requirements.

Autoregressive architectures generate one token at a time, walking one path at a time. Even Chain-of-Thought is serial, not genuinely parallel exploration. This is precisely the current architecture's weakest point.

The architectural limitation can't be fixed short-term, but we can compensate through collaboration patterns.

# Now That We Understand the Traits, How Do We Collaborate?

Understanding the "going stupid" mechanisms, let's return to the three opening questions. Starting with awakening.

## Awakening: Talk Like an Expert, Not Like You're Writing an Essay

I've seen people teach prompt-writing methodology: write long, logical, detailed paragraphs, be as thorough as possible.

My experience is the exact opposite.

Experts don't need lengthy preambles when talking to each other. Between domain specialists, three sentences get the point across — you don't even need background, just the key route choices, and the other person fills in the rest. If you miss the mark, one question-and-answer round gets you to "yeah, I see what you mean."

Anyone who's played D&D knows the difference. The Level 1 wizard reads the entire spell description aloud:

> *"I invoke the ancient spirits of the elemental plane of water! Hear me, O Undine, princess of the babbling brooks! Channel your primordial fury to wash away all who stand before me! I CAST... TIDAL WAVE!"*

Yeah, that wizard got stabbed mid-incantation.

Meanwhile the Level 20 sorcerer:

> *"Wish."*

One word. Reality bends. **Information density is power.**[^2]

[^2]: In D&D, the *Wish* spell is the most powerful spell in existence — a single word that can reshape reality. No material components, no elaborate ritual. The ultimate expression of "short incantation, maximum devastation."

Same applies to LLMs. Wasting words wastes tokens and brainpower. Better to say 2–3 sentences:

- Sentence 1, the context: integrating video watermarking for the current project
- Sentences 2–3, the key route: considering FFT/DFT-class approaches, inserting features in the low-frequency domain to survive high-frequency denoising

That's it. Let AI expand from there.

Anti-pattern: I've seen people write an entire screen of prompt — project background, tech stack versions, what changes were made to this feature last time, whatever brain-dead idea the PM floated in today's meeting, even a rant about how the AI's last commit had a bug that got them paged at 3 AM for an emergency rollback... all crammed in. Result? AI's response is also an entire screen of filler — repeating your background back to you, then adding a pile of tepid "suggestions." The lower the information density, the lower the output quality.

But there's a prerequisite: **your own cognitive level determines the ceiling of AI's output.**

Low-level cognition produces low-level prompts, which produce low-level output. If you can't articulate "consider FFT/DFT, insert features in the low-frequency domain," AI just gives you the most basic plaintext watermark solution. AI's knowledge vastly exceeds any individual's, but it needs you to use the right key to unlock the door — and that key is your own professional expertise.

So "talk like an expert" doesn't just mean "be concise" — it means **you actually need to be an expert**. AI amplifies your existing capabilities; it doesn't conjure capabilities from thin air.

Another war story. AI applied a blur mask to a video, then just copied the original m3u8 playlist over — completely unaware that re-encoding would change the byte offsets. I wasn't sure myself at first: under variable bitrate encoding, would mask processing actually affect output size? I discussed it with a friend who works in AV — he thought no, I thought yes. Experimental verification confirmed: file size shrank, I-frame positions all shifted, the original m3u8's byte ranges pointed to completely wrong locations.

But Opus 4.6's recovery ability surprised me. I asked one question: "You just copied it over as-is?" — and it self-diagnosed the entire error chain, then gave the correct solution (use FFmpeg's HLS muxer to output a new m3u8 directly). Codex can't do this — without being fed the reasoning chain, it can't guess that masking followed by re-encoding would shift byte offsets.

There's a point worth making explicit here: "talk like an expert" doesn't require you to be stronger than an expert in every sub-domain. You just need **enough cognitive density to form the right suspicion**. You don't need to know *for certain* that m3u8 byte offsets will change. You just need to suspect "is copying it directly really correct?" and ask in one sentence — AI unfolds the rest. But notice: forming that suspicion itself requires a reasoning chain: blur mask changes visual content → VBR encoding means information entropy changed → output size changed → byte offsets no longer match. A cognitive gap at any link in this chain means the suspicion never fires. The threshold dropped from "you need to know the answer" to "you need to be able to doubt" — but "the right doubt" still requires a cognitive foundation.

But "talking like an expert" only solves the **signal quality** problem — using high-density input to awaken high-quality output. There's also a **signal coverage** problem: you don't know which direction to ask about, and even the most precise questions can't cover blind spots.

For this, there's a complementary strategy: **undirected audits**. Ask AI without any preconception: "What dimensions do you think the current approach is missing?" Then drill into each one. This can't guarantee coverage of all blind spots — AI might fabricate dimensions to seem helpful — but it's better than only asking along directions you already know.

Now let's talk about verification.

## Verification: Actively Fighting Creativity Decay

Since we know long context kills creativity, we should actively fight back. The core strategy: **pause periodically and have the human lead an audit of the current approach.**

Concrete steps:

1. When you feel AI starting to "coast on inertia," stop
2. Fork the current session, or start a new one
3. Use `/compact` to compress the context, letting AI revisit the current approach with streamlined memory
4. Have AI self-audit first: is there a better alternative to the current approach? Are there hypotheses that can be cheaply validated?

Essentially, this uses human metacognitive ability to compensate for AI's attention allocation deficits in long contexts. Humans handle "should we be doing this?" AI handles "how do we do it?"

## Engineering Principles: Let Machines Verify for You

How do you verify AI's proposals? Programming has a natural advantage: compilers, type systems, test suites — these verification tools don't depend on human subjective judgment. Your discernment has a ceiling; machine verification doesn't. The prerequisite: the code itself must follow some basic principles.

### Naming

Critically important. Periodically have AI audit all naming conventions. Don't invent names yourself.

Human engineers can remember "this function is called `processMatrix` but it actually does traffic routing" — the brain automatically builds a mapping between name and reality. But agents don't. Every new session, they earnestly interpret names at face value, then faceplant into the same pit over and over.

Management loves their buzzwords — "traffic matrix," "viral growth engine" — I can't control that. But once this naming pollution leaks into code, you're planting landmines for agents. Good naming lets both AI and humans quickly build correct mental models. Bad naming can only be survived by humans through raw memory — agents can't hack it. The goal: **any agent in any new session should be able to understand what something does from its name alone.**

### Feature Design

Keep it conventional and simple. Don't be a special snowflake. Your business model and program logic aren't that unique — you're probably not the first person on Earth to think of this approach. Instead of designing some twisted implementation based on a PM's napkin sketch, describe the approach to the agent and ask: what is this pattern called? Are there successful examples? What can we learn from them? Then let the agent implement it following industry-standard patterns, not the version that only exists in your imagination.

> Example: designing a user login system where passwords can't be stored in plaintext. If you've never heard of bcrypt, you might describe a homebrew scheme to the agent — MD5 first, then SHA256, then ECC, with the private key hardcoded in config. Stop. Send your scheme to the agent first and ask what industry best practice is. AI will tell you about bcrypt/scrypt/argon2, and point out your scheme's flaws: iteration count too low, ECC private key improperly stored, all ciphertext derived from the same rule making it vulnerable to parallelized rainbow table attacks.

**Listen to dissenting opinions from agents.** AI's knowledge breadth far exceeds any individual's. Don't just use it as an executor — use it as a reviewer too.

### Modularity

The truly unique parts of your thinking should be implemented by composing standard modules, not by modifying (warping) the standard implementations themselves. Keep modules as independent as possible, minimizing cross-cutting concerns. For unique requirements, stack a few simple modules — **addition, not multiplication.** Feature stacking is linear growth; feature coupling is combinatorial explosion. One function doing three things means the agent misunderstanding any one of them tanks the entire result.

### State Convergence

- **Finite state, not infinite state**: The smaller the state space, the less likely AI is to drift off course. Same principle as Go — the later in the game, the smaller the board space, the fewer states, the more the position converges, the more precise the evaluation. Good software design should present agents with a state space that converges over time
- **Converge, don't diverge**: Guide AI toward deterministic convergence, not infinite possibility expansion

For AI's coding bad habits (like the defensive programming mentioned above), the effective approach in practice is: **define explicit coding style rules, then do periodic undirected audits.** "Undirected audit" means not looking for specific issues, but randomly spot-checking code to see if AI has quietly drifted. My experience (limited to Opus 4.6 1M): after defining rules, AI follows them reasonably well. Some minor stylistic drift as context grows, but no major route deviations.

At the end of the day, these principles were good engineering practice long before AI. But you used to be able to "run up the tab" — human colleagues could fill the gaps through shared context and memory.

With agents, **technical debt costs are dramatically amplified**: every misleading name, every tangled module, every undocumented implicit convention causes agents to repeatedly screw up, waste tokens, and produce garbage code. Let an agent pile new code on top of bad code, and within a week the project is unmaintainable.

## Refactoring: Sustainable Development in the AI Era

Technical debt gets amplified, but the tools for paying it down also got stronger.

Flip side: AI is actually the ideal refactoring partner.

The boilerplate you were too lazy to write, the type gymnastics you couldn't be bothered with — now you can toss them all to the agent. It's burning tokens, not your brain cells. If the old code is already protected by opaque types and other type constraints, AI is unlikely to drift far during refactoring. The type system itself is a guardrail; the compiler catches most errors for you.

Of course, there's an honest caveat: **large-scale refactoring mainly applies to new projects, or projects you've been maintaining from the start.** Legacy systems? You're going to deploy the agent's changes to production? I wouldn't. Compatibility issues, implicit dependencies, dark corners without test coverage — these are minefields agents can't perceive.

But for new projects, I believe "large-scale refactoring" should be **normalized.** Don't wait until the code rots to refactor — make refactoring part of daily development. The key is forming a positive feedback loop: **refactor frequently → reduce technical debt → reduce code volume → agent comprehension cost drops → next refactoring goes more smoothly.** This is the sustainable path for AI-assisted development.

But this loop spinning up has a prerequisite: **architecture must be designed by humans.** The more constrained the agent's field of view, the better it performs. Don't let it over-perceive the full framework or other modules' implementation details during design — give it only the minimal context needed for the current task. If you let the agent make top-level architecture decisions on its own, the result will almost certainly be a dumpster fire.

This isn't hypothetical. I've lived through the counter-example.

### Cautionary Tale: Having Agents Write and Maintain Documentation

My boss comes from a chemistry background — no software architecture experience, no idea how to constrain agents toward convergence. His approach was having agents generate mountains of markdown design docs — architecture docs, feature docs, logic flow docs — then strictly requiring in rule files that agents check design docs for consistency on every code change.

Sounds reasonable. In practice, it was a disaster:

1. **Agents ignore rules as context grows long.** Especially during long debug/feedback cycles with multiple fix attempts, switching between approaches, waiting for deployment verification — at some point the agent finishes a code change and just forgets to update the corresponding markdown doc
2. **Doc-code inconsistency triggers chain reactions.** When a new session starts, the fresh agent reads stale design docs, gets poisoned by outdated concepts, and produces wrong implementations. The rule file doesn't cover this case: when an agent finds design docs inconsistent with actual code behavior, it should update the docs, not rewrite the code to match the docs
3. **Docs pile up and cannibalize context.** The longest design doc approached a thousand lines. One new feature spanning 2–3 modules required the agent to first read through the project background and framework's thousand-line markdown — context already pushing up against the stupidity threshold for ordinary models. Docs were supposed to reduce cognitive load; instead they were consuming the most precious resource — the context window
4. **Stupidity effects get artificially amplified.** Recall the creativity decay discussed earlier: the longer the context, the more AI coasts on inertia, the less capable it is of stepping outside the current path. A thousand-line markdown doc pushes the agent straight into the stupidity zone — you're literally digging your own grave

So having agents write and maintain markdown docs had the exact opposite of the intended effect over the past year — even on today's Opus 4.6. **Code itself is the best documentation.** Type signatures are interface contracts; test cases are behavioral specifications. Instead of maintaining a markdown that's perpetually at risk of going stale, invest the effort in making the code self-explanatory.

My boss's backend was restarted from scratch six times. My own backend project, maintained through AI + human collaboration for a year, can now handle massive-scale refactoring with Opus 4.6's help. This was completely impossible late last year — Opus 4.5 would botch even moderately-sized modules. But Opus 4.6 1M changed the game.

At the end of the day, with agents I still design architecture and lead refactoring, same as before. My workflow didn't change — what changed is speed. Agents handle the stuff I wanted to do but was too lazy to bother with. The difference isn't whether you use AI, it's **who's the boss.**

At this point, the first two of the three opening questions (how to awaken, how to verify) have initial answers. The third — what to do when AI's proposals exceed your understanding — the current answer is: humans hold the reins, agents do the labor. Architecture by humans, verification through engineering infrastructure, auditing through human metacognition.

But how long can this answer hold?

# CCC = AlphaGo's Go Board?

I'll be honest: I jumped on the bandwagon mocking Claude's C Compiler (CCC), dismissing it as a clumsy imitation of "humans developing a compiler" rather than actually developing a compiler.

But now I have a rather unhinged idea.

AlphaGo Zero's evolution was completely independent of human game records — pure self-play<sup>[Erratum 4]</sup>. The Go board was its training ground.

So is CCC Claude's Go board?

This analogy is worth unpacking, because Go and code each have distinct strengths and weaknesses as "training grounds."

Go's feedback is **ultimately binary** — win or lose, no argument, no appeal. The code world has no such clean binary standard: code quality is a continuous spectrum, with an enormous gray zone between "it runs" and "elegant and efficient." In this sense, Go's feedback signal is stronger and more pure.

But Go has a fatal weakness: **the feedback path is too long.** A stone placed in the opening? You wait until endgame to learn whether it helped win or lose, and in between, it's extremely difficult to determine that stone's contribution to the final outcome — this is precisely why AlphaGo needs a value network. It's essentially using an additional neural network to *guess* the value of intermediate states, because Go itself provides no intermediate feedback.

The code world is the exact opposite: **short-path feedback is everywhere.** Type signatures tell you instantly whether interfaces are correct the moment you write the code; unit tests tell you within seconds whether logic is correct; integration tests tell you whether components play well together. You don't need to wait for "endgame" to know whether a move was good — every step has immediate, local feedback signals. This means the credit assignment problem is inherently far simpler than in Go.

And compiler development happens to be one of the most complex, most exquisite software engineering challenges in the human world. Its **correctness** requirements are extraordinarily strict — a single codegen bug can cause every downstream program to produce untraceable errors. Its **performance** demands push toward theoretical optimality — register allocation, instruction scheduling, loop optimization, every step approaching the limit. Its constraints on **generated code size** are hard — in embedded scenarios, every extra byte is a cost.

More critically, humans have already built an incredibly comprehensive test infrastructure for compilers — from language conformance test suites to performance benchmarks, from fuzz testing to formal verification. These all provide precise, quantifiable feedback signals. Compiler development is far more complex than LeetCode problems — it's not solving an isolated puzzle, but performing global optimization across a massive constraint space. Yet even the world's best compiler engineers, facing constantly evolving hardware architectures and language features, can't claim to have perfectly solved this problem.

Compiler development also has an often-overlooked advantage: **it's a relatively closed task** — and closedness is precisely the core advantage of the Go board for AlphaGo. Go's rules are finite and complete; the 19×19 board is the entire universe. There's no "opponent flips the table" or "pieces spontaneously vanish." Because it's closed, the problem space is finite — it can be enumerated, learned, conquered.

Real-world software engineering is exactly the opposite of closed — peripherals to drive, legacy APIs to accommodate, towering mountains of historical code, external SDK changes from third-party services and cloud platforms, database constraints, disk space running out, ethernet cables getting cut or packets getting dropped, the other server's power being yanked, or even [your cloud provider's datacenters getting hit by military drones](https://www.datacenterdynamics.com/en/news/israel-and-us-bomb-data-centers-in-tehran-following-irans-drone-strikes-on-aws/).[^3] These factors make the feedback signal noisy, uncontrollable, irreproducible.

[^3]: In March 2026, Iranian drones struck three AWS datacenters in the UAE and Bahrain — the first known military strikes on a commercial hyperscaler's infrastructure. Banking, payments, and enterprise software across the Middle East went dark. The US and Israel retaliated by hitting datacenters in Tehran. "Edge case" doesn't begin to cover it.

A compiler's input is source code, output is target code, and the transformation rules in between are strictly defined by the language specification. The entire problem domain is self-contained, with virtually no dependency on real-world uncertainty.

This is precisely what makes it ideal as an AI self-evolution "game board": complex enough, feedback clear enough, standards objective enough, boundaries closed enough.

So here's my hot take: **compiler development, more than any other software engineering task, is the ideal training ground for self-training a coding agent.** CCC looks like a joke today, but AlphaGo Zero started from random stone placement and surpassed the version that defeated Lee Sedol in 3 days<sup>[Erratum 5]</sup>. What matters isn't how low the starting point is, but whether it has a training ground that allows it to continuously improve.

More importantly, compiler feedback is more precise and more fair than human correction. Recall the alignment pressure discussed earlier — human annotators are limited by their own cognitive level and knowledge depth, penalizing "weird-looking" but potentially effective ideas while rewarding "sensible-looking" defensive programming. Compilers don't do this. Code either passes tests or doesn't; generated target code either outperforms the baseline or doesn't. The compiler doesn't care whether your solution "feels intuitive" — only whether the result is correct and efficient. This neatly bypasses the problem of human annotators being the bottleneck in RLHF.

If AI can self-evolve through closed, complex, feedback-dense tasks — continuously writing code, compiling, debugging, fixing, optimizing — then the "collaborative partnership" relationship might just be a transitional phase.

At the current stage, even Opus 4.6, the strongest model available, produces a dumpster fire when left to lead on its own — as my boss's case already demonstrated. Human architecture design, route judgment, and periodic auditing remain indispensable.

But if a "Claude Zero" truly emerges — a model trained purely through self-play on the compiler as its game board, the way AlphaGo Zero abandoned human game records — would it still need humans at the helm? I don't know.

But at least right now, understanding its cognitive characteristics and finding effective collaboration patterns remains the most important thing we can do. The last installment said us terrifying upright apes were underestimating our own intelligence. This installment's point is: precisely because we have intelligence, we should learn to harness this unprecedented tool — neither intimidated by its aura nor blindly trusting its output.

---

# Errata

The main text uses simplifications and occasionally biased framing for readability. Below are more rigorous clarifications.

**[Erratum 1] "The longer the context, the mushier the attention"**

The main text's framing is a convenient intuition, but not mechanistically precise. Softmax normalizes over query-key dot products — if newly added tokens are irrelevant to the current query, their attention weights theoretically approach zero and shouldn't significantly dilute relevant tokens. The real issue is more subtle: (a) when the context contains many **semantically similar but not identical** tokens, attention's discriminative power between them decreases; (b) in multi-head attention, each head has limited effective coverage, and some heads may "defocus" in long contexts. Scalable-Softmax (2025) and similar work address this through softmax temperature scaling and entropy control, not simple "probability mass being spread evenly."

**[Erratum 2] "Verified this at the mechanism level"**

Scalable-Softmax, ASEntmax, and Critical Attention Scaling primarily contribute **proposed solutions** (temperature scaling, sparse attention, etc.), rather than pure verification that long-context attention dilution exists. Their existence indirectly confirms the problem is real, but saying they "verified" it is imprecise. The main text has been revised to "analyze and attempt to address."

**[Erratum 3] GSM-Infinite's applicable scope**

GSM-Infinite tests **mathematical reasoning** tasks (a long-context variant of GSM8K). Its "reasoning ability degrades monotonically with context length" conclusion is strictly verified only within mathematical reasoning. Directly generalizing to all types of reasoning requires caution, but combined with "Context Length Alone Hurts" and other research, negative effects of long context on reasoning ability appear to be broadly present.

**[Erratum 4] AlphaGo evolution path**

The AlphaGo series evolved as: AlphaGo Fan (2015, defeated Fan Hui) → AlphaGo Lee (2016, defeated Lee Sedol) → AlphaGo Master (2017, 60-game winning streak) → AlphaGo Zero (2017, pure self-play). Only **AlphaGo Zero** was completely independent of human game data, starting from random initialization with pure self-play training. All prior versions used human game data for supervised pre-training. The original text's vague phrasing could mislead readers into thinking this was gradual improvement of one system, when Zero was actually a fundamental redesign of both architecture and training methodology.

**[Erratum 5] "Surpassed the Lee Sedol version in 3 days"**

This claim comes directly from the DeepMind paper (Silver et al., 2017) and the data is correct. However, note that AlphaGo Zero was trained on a single machine with 4 TPUs — not consumer-grade hardware. "3 days" can give the impression of effortless dominance; in reality it was the result of intensive dedicated hardware investment. Additionally, the 3-day milestone surpassed AlphaGo Lee (the version that defeated Lee Sedol); it took a full 40 days of training to surpass all previous versions.
