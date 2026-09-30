---
title: "Ming's Spell Compendium #6 -- A Generalized Curry–Howard Proof Searcher and Program Synthesizer (Crackpotizen Edition)"
date: "2026-08-20T16:18:37+08:00"
tags:
  - AI
  - Programming
  - Functional Programming
  - Translation
url: /2026/08/20/generalized-curry-howard-proof-search-and-program-synthesizer-en/
---

“Crackpotizen” combines “crackpot” and “citizen”: formal methods for the rest of us.

> *This is a cultural adaptation, not a literal translation, of the [original Chinese article]({{< relref "/posts/generalized-curry-howard-proof-search-and-program-synthesizer.md" >}}). The running “crackpot” joke plays on **minke** (民科), usually dismissive slang for an amateur theorist, and on the author's name, Ming.*

> **Previously on...** [Ming's Spell Compendium #5 -- Promise You Won't Freak Out (Chinese)]({{< relref "/posts/cyber-moneyball.md" >}})

It's been more than five months since the last installment, and the ways people use AI have changed beyond recognition. Think back to the first half of the year. Every self-appointed AI prophet was announcing that software development was a solved problem, that we could fire 99% of programmers, that we had entered the age of the lights-out software factory. Tech conferences might as well have retired every other topic. Senior architects from big tech were touring the world with presentations about how much more their teams shipped with AI and how much shorter their deadlines had become. Some even held up soaring commit counts and lines of code as proof of productivity. Apparently more code is always better. But in the second half of the year, the fever has started to break. Even the most devoted AI revival meeting in my group chats has gone quiet.

The expensive tokens have been burned. The codebase has multiplied in size. Every developer makes dozens of commits a day. Yet the team ships no more functionality, and quality is going downhill faster and faster. The money saved by firing developers and disbanding teams has even far exceeded the API token bill.[^1]

Meanwhile, the underlying models get smarter by the week. Benchmark questions can barely keep up, and the model labs have started taking on the Millennium Prize Problems. Unless someone updates the questions and the evaluation methods, we may run out of unsolved exam papers before the year is over.[^2]

On one side, coding agents keep setting records. AGI has arrived. Again. And again. The back-to-back “nuclear” breakthroughs have blasted me into my chair so hard I can no longer move. Lab C has just pushed the known lower bound on the proportion of Riemann zeta zeros on the critical line to 67.2%; Lab O has cracked Navier–Stokes. On the other side, projects maintained by AI over the long haul keep turning to shit. More code, more regressions. The intelligence that works miracles on century-old mathematical problems seems to do surprisingly little for the upkeep of ordinary application software. What, is a CRUD app harder than the Riemann hypothesis? Scatter some grain over a keyboard and a chicken could write one.

![A still from The Mandalorian captioned: “I have spoken.”](/images/mandalorian-i-have-spoken-en.webp)

*“I have spoken.” Still from [The Mandalorian, via StarWars.com](https://www.starwars.com/news/20-favorite-quotes-the-mandalorian-season-one).*

So here's my outrageous claim: AI has become much better at doing research, but it has not become much better at building complex systems.

# 1. So Far, Only the Crackpot Has Noticed[^3]

![A Spider-Man (2002) still captioned: “I'm something of a scientist myself.”](/images/spiderman-scientist-en.webp)

*Formal methods are becoming accessible to ordinary developers. Still from [Spider-Man (2002)](https://en.meming.world/wiki/You_know,_I%27m_something_of_a_scientist_myself).*

Formal methods used to live behind glass, reserved for the hearts of critical systems, aerospace, and similarly rarefied work.

I have never learned Lean. I have never written a line of it myself. Even now, I haven't read a single line of an introductory book, tutorial, or manual. Our decidedly makeshift backend team has four developers, including me. Three months ago, the other three hadn't even heard of Lean. As of publication, this Lean 4 backend has been running in production and receiving regular updates for about three months, without downtime. Formal methods no longer have to stay inside compilers, kernels, and spacecraft. They can work in application software whose requirements change with the wind.

AI has brought formal methods within reach of ordinary working programmers. You no longer need the keys to the ivory tower.

I imagined this in the first installment at the beginning of the year: use formal verification to check the logic AI produces. Back then, AI still struggled to write formal code and get its proofs through. I also naively underestimated how fast it would improve. I thought it would take much longer before AI could do useful work here.

In the fourth installment, I called the use of preconditions, postconditions, and invariants to constrain functions “Level 3.” But what we could reliably put into practice was still Level 2: types, explicit domain errors, and boundaries around side effects.

The fifth went a step further. Humans would review the specification; AI would implement it. We would extract a clean core and cover it with formal proofs, while leaving the messy parts to integration tests and property-based testing (PBT).

Over the past few months, I have tried all those proposed combinations of AI and formal methods in production business systems. I changed course four times. The proofs I ended up with look very different from the Level 3 I imagined in the fourth article. To be honest, it seemed pretty simple when I first proposed it:

1. AI can write code in a formal language.
2. That language is Turing-complete.
3. You can develop application software in a Turing-complete language.

Therefore, by the power of a wonderfully naive syllogism: AI can develop application software in a formal language.

It would work just like SMT-based verification: write each function's requirements as preconditions and postconditions.

What I actually built looks rather different from that fantasy. But the detour brought some unexpected benefits.

# 2. Nobody Remembers What It Was Supposed to Do

A fictional story.

## The FDE Department

> **Lead:** Ming! Ming! Mr. Zhao's clients can't log in! Find out what's going on!
>
> **Ming:** ...Let me check...
>
> **Lead:** Restore access first! Investigate later! Zhao and the boss are still at the client's office. We cannot afford another problem!
>
> **Ming:** These accounts hadn't completed identity verification, and their free trial allowances had expired. The cleanup job deleted them last night.
>
> **Lead:** What? Why? Aren't they Zhao's enterprise clients?
>
> **Ming:** Product added identity verification last month.  
> We had fewer than 3,000 accounts registered by actual people. The other 400,000-plus were bots farming signup bonuses.  
> At last week's standup, the boss said every account had to complete identity verification, and any account that didn't had to be shut down.  
> He also said...
>
> **Lead:** Oh, come on! Do you developers ever stop and think? Obviously the boss meant individual users. How could you delete enterprise users? Restore them. Now.
>
> **Ming:** ...

> Ming maintains the company's SaaS product. Before the AI coding frenzy swept through the company, the project had fewer than 20,000 lines of code.  
> A few months later, it has 900,000. The architecture defies description. The details defy looking at.  
> More and more code, fewer and fewer people to maintain it. The frontend and QA teams are gone. Management rubber-stamps Skynet's slop plans. The remaining developers follow orders and slowly lose their minds.

## The Next Day's Blameless Postmortem, Now with Blame

> **Mr. Zhao:** *(Opens with the carefully casual tone of someone about to stick a knife into engineering.)*  
> Yesterday, the boss and I were at the client's office to demo the custom features. It had taken ages to get time with their group's VP.  
> We were hoping to sign next quarter's contract while we were there. I'd just finished assuring everyone that our engineers were excellent and the platform was rock solid.  
> Then two of their people couldn't log in. I was sweating bullets.  
> Luckily, the boss saved the day. He told me to switch to the superadmin account so we could keep the demo going, and that was how...
>
> **Lead:** *(Has been twitching intermittently since the previous meeting ended.)*
>
> **Boss:** *(Turns to engineering. Speaks very slowly.)* This is not a witch hunt. We're not here to assign blame. What's happened has happened. The question is how we stop it happening again.  
> I gave this week's group chat to an AI. A free one. Even that could spot these problems. *(Glances at Lead.)* Engineering needs to reflect on why you didn't catch them beforehand.
>
> **Ming:** *(And you complain about our token spending? Anyone can be a genius after the outage. Where was your AI's warning before it happened?)*
>
> **Lead:** Ming, you developed the account cleanup module last week. Explain this bug.
>
> **Ming:** It isn't a bug. That's what the requirements said. The meeting notes and change document were posted in the team chat. You and Product both approved them.
>
> **Lead:** Yes, we approved them. Did you flag the technical risks in advance?  
> You can't just point at the requirements after something goes wrong.  
> I expect you to exercise your own judgment.  
> If engineering won't think, it'll be the next department AI replaces.
>
> **Ming:** *(There it is. He's finally found someone to take it out on.)*
>
> **Ming:** The requirement was urgent and the deadline was too tight. There wasn't time for a thorough investigation.
>
> **Boss:** Feel the empowerment. Embrace AI. I've been saying this all year, and engineering still hasn't taken it seriously. Didn't we buy an enterprise knowledge base? AI puts all the meeting notes and requirements in there automatically. If Ming doesn't have time to investigate, why not have AI do it? Look at Product. Since they embraced AI, three people do what used to take eleven. Engineering needs to keep up.
>
> **Ming:** *(Oh, I've felt the empowerment. I've certainly felt the increased production rate of bullshit requirements. Product drops at least ten mutually contradictory, ten-thousand-word specs on me every day. I can only hope our gracious AI overlords let the whole company share in the resulting, equally empowered production outages.)*
>
> **Boss:** Those articles I shared in the group the other day, about AI workflows at one-person companies? You all need to study them. One person runs a few AIs. Product, engineering, operations, every role is covered. The AIs coordinate among themselves and deliver a whole system in three days. I posted the articles. Has engineering actually read them? AI is evolving so quickly. We need to cooperate with it, not hold it back.
>
> **Ming:** *(So we've rebuilt the entire imperial bureaucracy out of chatbots? If the boss loves AI role-play this much, we should pivot to murder-mystery parties. And printing “Forward Deployed Engineer” on my badge won't make delivery any faster or the software any better.)*
>
> **Boss:** Tokens are free now. There's a little box the size of your palm that runs any model. The company still reimburses engineering 500 yuan a month for AI subscriptions...  
> Those big computers you have should be able to run at least two models.
>
> **Ming:** *(Would you listen to yourself? A DGX Spark starts at 30,000 yuan. You gave us black plastic bricks for laptops. Do you think compute scales with the size of the case?)*
>
> *...An indeterminate amount of time passes somewhere far from the agenda...*
>
> **Lead:** Back to the incident. Ming, walk us through exactly what happened.
>
> **Ming:** At last Tuesday's standup, the boss urgently requested that personal accounts complete identity verification to keep using the platform. So on Wednesday we deployed a module that deletes unverified, unsubscribed accounts at midnight every day.
>
> **Lead:** If it only applies to individuals, why did it delete enterprise accounts?
>
> **Ming:** It didn't delete enterprise accounts. It deleted the individual accounts inside them.  
> The spec says, “Every actual user account is a personal account.” That definition came from you.
>
> **Lead:** But the account was linked to an enterprise.
>
> **Lead:** And what do you mean their subscriptions expired? Why would enterprise members have their own subscriptions?
>
> **Ming:** I pulled up the February spec. Every new account got a month of Pro, then dropped to Free.
>
> **Ming:** “Enterprise” is what you call it in conversation. The system distinguishes Team, Enterprise, and International Enterprise.  
> Leaving International Enterprise aside, nobody has ever actually used the Enterprise tier.  
> This incident affected Zhao's client. For historical reasons, three of their departments have three separate Team subscriptions. Only HR was hit, because its members had joined through external-collaborator invitations and all used number-based QQ email addresses.
>
> **Lead:** But they were invited. How did they become registered users?
>
> **Ming:** It still goes through the signup endpoint. The spec says they have to enter their name and department after accepting the invitation. You submitted that merge request yourself.
>
> **Lead:** *(...)* If all of this was in the spec, why didn't you flag the risks earlier?
>
> **Ming:** *(If you know today that a stock has shot up, why didn't you put everything into it yesterday?)*  
> It took ten subagents two hours to uncover these problems for this postmortem, and there may be more we haven't found.  
> It's easy to trace a failure after it happens. Beforehand, even AI struggles to see that these requirements conflict.
>
> **Boss:** Discuss the technical details separately afterward. Before this meeting ends, I want a process that ensures this never happens again.
>
> **Ming:** *(Postmortem, postmortem. When does management get one?)*
>
> **Lead:** Here's what we'll do. For every requirement change, two agents will independently design solutions and cross-check each other. Then we'll pick the better one.  
> Before each deployment, AI will list the affected areas and click through every feature. Engineering and Product will do acceptance together...  
> Any other suggestions? Ming, let's hear yours too.
>
> **Ming:** *(Take your time and get crap. Rush it and get a steaming pile. You've handed everything from design to acceptance to AI. Clearly you're taking this very seriously.)*
>
> **Ming:** That will make the AI slower. With that process, we won't ship even in three days. Our deadlines are too tight. We need more time first, so we can investigate properly.
>
> **Lead:** The deadlines... *(Glances at the boss, voice wavering.)* ...Well...
>
> **Boss:** Your call.
>
> **Lead:** Right. Then... we'll give low-priority tasks one extra... half a day. Half a day. More time for AI to test. Urgent tasks stay as they are. Does... that... work? *(Looks at the boss.)*
>
> **Boss:** I only care about results.
>
> **Ming:** *(Keep acting. Bravo. Every requirement is either important or very important. Every deadline is either urgent or extremely urgent. As if you don't know.)*
>
> **Ming:** It's not that we didn't test. AI even wrote tests to “ensure these external-collaborator accounts are deleted.”  
> As for which clients were affected and how many such accounts existed, AI couldn't know without querying the production database.
>
> **Boss:** *(Generating a brilliant idea... complete.)* Then let's stop writing to a database. Write everything straight into the knowledge base. Whenever something changes, AI can read the knowledge base and make the decision with all the information.
>
> **Ming:** *(Behold: the ancient Greek god of terrible ideas.)*
>
> **Lead:** Brilliant, boss. Other teams are still breaking down information silos. We skip straight to a knowledge base as the single source of truth, an SSOT...
>
> **Ming:** *(And his companion, the ancient Greek god of kissing ass.)*

The system's old assumptions lie scattered through documents and the knowledge base, while new designs keep overturning old ones. Reconstructing the system's current behavior from that prose is already difficult for AI. It can miss things or misread them. More importantly, documentation is documentation and implementation is implementation. No law of nature requires them to agree. Synchronization is temporary. Drift is forever.

# 3. Give the Context Window Less to Carry

It's not that nobody wrote down the software's core assumptions. It's that nobody kept sorting, checking, and consolidating them into an account of the current system. Which rules still apply? Which have been retired?

I'm sure the information exists somewhere: chat logs, meeting notes, product requirements documents, Git history, code comments, tests, and the code as it currently runs. But it comes mixed with obsolete information, irrelevant arguments, imprecise wording, contorted architecture, and all the rest of our technical debt. Are we really going to make AI read the relevant history and deduce the current rules afresh every time?

Which rules do we keep? Which are obsolete? Which need someone to confirm them again? What code belongs to the obsolete rules? Someone has to untangle all this and remove both the dead rules and the code that serves them. Very few humans or AIs dare.

Before formalization, AI generated 99% of my project's code. Every time something broke and I went digging, I found terrible old designs left by different sessions. Some had added features; others had fixed bugs. Over time, they had become contradictory control flows, waiting for one unlucky data object to collect the right combination of conditions and set off the mine.

Can't tests catch these conflicts? Not easily. Most slip past them. Tests generally cover some of the branches that existed when they were written, not the branches someone will add later. If maintenance changes a lower-level function, such as an AOP hook, a logging helper, or a fixture helper, will AI recursively trace every affected caller and fill in the missing test coverage for all of them?

Old and new behavior no longer agree. A new feature breaks an earlier assumption, perhaps a crucial one, but AI doesn't notice and the humans no longer remember it. My first version really didn't have many requirements. Later, I added conditions and changed direction. Meanwhile, AI inevitably added its own extras: frameworks, middleware, databases, components. A lot of extras. After enough iterations, I could no longer tell which pieces reflected my requirements and which were AI's embellishments. Whether any given implementation still served my current requirements, now revised eight hundred times, was anyone's guess.

## Why Does My AI Keep Getting Slower?

* Why is AI trying to fix a bug in a C module with over a hundred thousand lines, when this is just a static news site? Because the C module implements vector search as a semantic-search extension for SQLite.
* Why are we adding semantic search to SQLite? Because SQLite is the project's database.
* Why did we choose SQLite? Because the project started as a local personal notebook.

The next AI sees how much has already been invested and naturally keeps grinding down the same twisted road. A local optimum. A taller mountain of shit.

This isn't a real incident, of course. I chose the example because a programmer can see what's wrong with it. But when AI works in a field beyond your own expertise, can you be sure it hasn't taken a similar detour? Does that incomprehensible code still serve what you want now?

When the core assumptions are expressed as formal theorems, a machine can check them rigorously against the code they describe. Natural-language prose cannot offer that connection.

My approach is to select properties worth protecting over time, turn them into formal propositions, and make the relevant implementations carry the proof obligations. A later change cannot merely satisfy the latest request. It must also preserve the constraints we have already decided to keep.

AI no longer has to infer the intended current behavior from prose or excavate it from a mountain of code.

Formal methods cannot negotiate a better deadline for Ming. They cannot decide which users the boss should require to verify their identities. What they can preserve are business rules that have been agreed on and must remain true after later changes.

For example, a personal subscription expiring does not mean access granted by an organization also expires. When someone later asks to “clean up unverified, unsubscribed accounts,” an agent has a clearer reason to ask: does “unsubscribed” mean no personal subscription, or no organizational relationship at all?

If we put the organization's access rules in the specification and require the new decision and cleanup logic to preserve them, AI cannot finish merely by implementing the latest request and writing tests for it. If the old and new rules conflict, we have to correct our reading of the new requirement, correct the implementation, or explicitly change the old rule. Formal methods don't make that business decision for us. They make the rules already in the specification constraints that a change must confront, rather than artifacts we dig out of the spec after an outage.

More mistakes can then be caught during development. The boss gets peace and quiet. The developers get to carry the weight.

![The price of peace: a tranquil world rests on the backs of people fighting beneath it.](/images/和平的代价.jpeg)

# 4. What I Actually Built

I now keep as much business state, rejection logic, and action selection as possible in Lean, as pure computation with tightly constrained input and output contracts. The repository has an in-memory model with an invariant. A table is simply `Table = List DomainRow`.

A Service starts from any repository state satisfying the invariant and produces another valid repository state plus an action. It may also leave the state unchanged and produce only an action. The corresponding Proofs establish that these transitions preserve the invariant. The initial state is valid, and each step preserves validity, so we can keep going one step at a time, as in mathematical induction.

Repo handles actual database reads and writes. Bridge calls the same decision logic, then hands the action to an executor.

On the real-database side, SQL and database constraints implement the same repository interface as the in-memory model. The model's invariants correspond to the database's table constraints, and the two have matching structures. Both the SQL and the model are laid out in the open. Their logic is easy to inspect, and even a smaller model can compare their behavior.

The PG check is a deviation check: run the same operations against the in-memory model and the SQL implementation in a real PostgreSQL database, then compare results and states. It is an automated guard against the two drifting apart.

PostgreSQL still handles SQL, transactions, locks, row-level security (RLS), data definition (DDL), and compare-and-swap (CAS). Firebase, object storage, media, and GPU work go to a Rust/native sidecar. A separate wire module checks that the schemas on the Lean and sidecar sides agree. Migration checks cover data migrations; acceptance checks cover the system as a whole.

```text
Humans define goals, state transitions, and capabilities that must survive
                              ↓
Agents search for programs, proofs, lemmas, and module boundaries
                              ↓
The Lean kernel checks candidates within the model
                              ↓
Deviation checks / wire compatibility / migrations / acceptance
                              ↓
Failures feed into the next round of search
```

Once a requirement has been translated into a precise proposition, the natural-language explanation can stay in a comment or a linked PRD. My attention goes to the theorems. As long as the code AI synthesizes passes these checks, I no longer examine it line by line.

Abuse of `axiom` or `sorry` to fake a proof can be exposed with `#print axioms`. That's actually one of the harder places to cheat unnoticed. The harder questions are whether the theorems AI wrote faithfully express the original requirement, whether they cover it completely, and what falls through the gaps.

You don't have to freeze the entire spec before writing code. In practice, some requirements I took for granted turned out not to be implementable as stated. I had to develop the implementation and the specification together.

During design, “refund approved” and “money received” looked like one step. During implementation, I had to confront at least a payment gateway in between. Neither submitting a refund request nor crediting a bank account succeeds 100% of the time.

```lean
inductive Status where | approved | processing | refunded
structure State where
  balance : Nat
  order : Status
abbrev Step := State → Except State State -- Both failure and success return the full resulting state.
```

So we add the intermediate state and the failure paths, then split the requirement into two propositions. The intended result is that the refund eventually arrives, provided everything goes right along the way.

```lean
structure WeakSpec (amount : Nat) (submit settle : Step) : Prop where
  submit_post : ∀ s, submit s = .ok {s with order := .processing} ∨ submit s = .error s
  settle_post : ∀ s, settle s = .ok ⟨s.balance + amount, .refunded⟩ ∨ settle s = .error s
```

The approach comes down to three principles:

1. Model trusted external components, such as SQL databases, vector databases, object storage, SMS services, and payment gateways.
2. Constrain the input and output contracts of components developed in-house.
3. Translate business requirements into theorems.

The rigorously checked Lean code then drives and coordinates all those components.

# 5. Rot Finds Every Crack

The refund example's failure path looks respectable enough. If the refund request fails, the user's balance doesn't increase and the order state doesn't change.

So why not return failure for every request? Leave the database untouched and every failure postcondition is satisfied. The only small problem is that nobody can get a refund. The specification never said under what conditions a refund must succeed.

```lean
def alwaysFail : Step := fun s => .error s
theorem alwaysFail_passes (amount : Nat) : WeakSpec amount alwaysFail alwaysFail :=
  ⟨fun _ => Or.inr rfl, fun _ => Or.inr rfl⟩

structure StrongSpec (amount : Nat) (gatewayOK bankOK : State → Prop)
    (submit settle : Step) : Prop extends WeakSpec amount submit settle where
  submit_ok : ∀ s, s.order = .approved ∧ gatewayOK s → submit s = .ok {s with order := .processing}
  submit_fail : ∀ s, ¬(s.order = .approved ∧ gatewayOK s) → submit s = .error s
  settle_ok : ∀ s, s.order = .processing ∧ bankOK s → settle s = .ok ⟨s.balance + amount, .refunded⟩
  settle_fail : ∀ s, ¬(s.order = .processing ∧ bankOK s) → settle s = .error s
```

In the delivery module of my actual production system, if the input object, output, and execution plan are all present, the decision must produce a background job. It cannot shrug, return “nothing to do,” and finish.

```text
Eligible snapshot
→ There exists an action
  such that decide snapshot = .enqueue action

decide snapshot = .enqueue action
→ Eligible snapshot
```

The first direction is proved by `eligible_decide_enqueue`; the reverse direction by `decide_enqueue_sound`. Another theorem establishes that rejection is equivalent to ineligibility. Nor can the decision enqueue any old job. The action is tied to its inputs and execution plan, and the theorems can check that relationship.

This is not a separately written toy model. It is the production decision logic. The theorems check the very same `decide` used in production. Once we have `.enqueue action`, a job-persistence interpreter writes it out. After the write, we also check that the persisted job still matches the action.

Another real example from my production codebase is worker epoch fencing. Once a task reaches a terminal state, it cannot be claimed again. Writing a checkpoint requires the exact current token. Even if the worker ID is unchanged, claiming the task again invalidates the old token.

```lean
def LiveExact (t : Task) (tok : Token) (now : Int) : Prop :=
  t.terminal = false ∧ t.holder = some tok ∧ tok.2 = t.epoch ∧ now ≤ t.leaseExpiry

structure Spec (claim : Task → Nat → Int → Option (Task × Token))
    (checkpoint : Task → Token → Int → Nat → Option Task) : Prop where
  terminal_no_claim : ∀ t w now, t.terminal = true → claim t w now = none
  checkpoint_exact : ∀ t tok now seq t',
    checkpoint t tok now seq = some t' → LiveExact t tok now
  claim_new_epoch : ∀ t w now t' tok, claim t w now = some (t', tok) →
    t'.epoch = t.epoch + 1 ∧ tok = (w, t'.epoch) ∧ t'.holder = some tok
  old_token_fenced : ∀ t w claimAt t' tok now seq,
    claim t w claimAt = some (t', tok) → checkpoint t' (w, t.epoch) now seq = none
```

Email works the same way. The formal model can require a function to produce a `SendEmail` action when the conditions hold. Whether the provider received it and whether it reached the recipient's inbox still have to be checked in the real world.

# 6. Stop Shipping Verified Toys

When I don't ask for formal verification, AI happily designs features I never requested. When I do, it repeatedly cuts functionality and delivers toys that pass verification but cannot go into production. This has been the hardest AI habit to break in formal development.

We are used to tossing AI a one-line request and watching the show: gorgeous interfaces, elaborate animations, even 3D CAD models or interactive music videos that follow the beat. “Make an interactive black hole or wormhole.” “Port The Legend of Sword and Fairy, Red Alert 2, Warcraft III, or Resident Evil 4 to the web.” “Build a fully featured recruitment management system.” One sentence, and off it goes.

Append “use Lean 4” to the same request, and AI gives you software without any theorem coverage. Patch the prompt with “provide formal proofs; no cheating with `axiom` or `sorry`,” and draw the boundary around trusted external components, and it still changes character completely. Out comes an ugly interface. Instead of supplying features you didn't think to request, it cuts features you explicitly asked for.

Force today's AI to follow formal verification through, and what you get is a thoroughly verifiable toy. You can't ship it. I asked AI to implement a business feature. In Java, it designed a table with thirty columns. In Lean 4, it gave me ten, five of them devoted to strict relationships with other tables. I even asked it to design the feature as though it were writing Java and only then implement it in Lean 4. It still left out the unstated but entirely conventional functionality.

In an early experiment, AI went further. It wrote a small verifiable core in Stainless to pass the checks, then wrote a completely separate Scala implementation for production. It told me everything was verified and all verification conditions (VCs) were green. I felt transported back to the AI in my first article: celebrating triumphantly the moment compilation passed, while the code was full of empty functions and TODOs.

I don't know the root cause. My guesses are:

1. Passing verification is the strongest reward signal, so AI sacrifices completeness to make the checks green.
2. “Complete” often hasn't even been written down.
3. Even when it has, ambiguity in natural language leaves room to do less.
4. Perhaps most importantly, this may be something nobody had tried before me, so AI had never seen it either.

For today's AI, formal development therefore needs an executable workflow and a method, not just a wish. A one-line request produces especially embarrassing results here.

Later, I ran into a different kind of toy implementation. AI loaded an entire table into an in-memory `List`, sorted and filtered it there, and handed the result to the API. In an ordinary web application, it would have filtered with a SQL query.

One piece of production code fetched telemetry separately for every row in a list. A fifty-row page issued fifty SQL queries. Elsewhere, it read and wrote paths one at a time, or rescanned the entire output snapshot for every Entry. In one particularly memorable change, it removed keyset pagination because “an organization won't have that many projects.” That lasted about two hours before being rolled back.

I suspect the reasoning went like this: a new SQL query means a new axiom, and a new axiom is trouble. In my formal project, expanding the trust boundary or adding axioms requires a sound justification to pass cross-review. Filtering an in-memory `List` merely composes already available theorems. It minimizes the change to the proofs while producing the worst implementation for production.

I'm not proposing a firing squad for every `List.filter`. Fetching a snapshot by business key with a clear size bound, then doing additional business filtering in memory, is perfectly reasonable. Loading an unbounded table, issuing N+1 queries, or repeatedly scanning the whole dataset is not. AI already has decent performance habits in ordinary application development. Move it into formal development, and it starts making mistakes it ought to know better than to make.

Avoiding this toy-making habit requires explicit workflow guidance in `agents.md`. Humans also have to fill out the software specification to match what they actually expect, so AI has fewer places to cut corners.

# 7. Simulacra and Simulation

![Simulacra and Simulation](/images/simulacra-and-simulation.webp)

A verified model can establish how an action must follow from the program's logic. It cannot establish that executing the action will have the effect we expect in the real world. We cannot enumerate all of reality's complications, so verification cannot replace testing altogether.

Take refunds. It's easy to assume that calling the payment gateway's API means the money will arrive. In reality, we have to ask:

* Is the payment SDK using the right secret key and signing algorithm?
* Are the parameters correct, and does serialization match the gateway's protocol?
* Has the receiving account been disabled?
* Does the paying account have enough money, including the processing fees?
* Does the transfer memo contain troublesome special characters, or material the provider prohibits, such as sexual content, gambling, or threats of violence?

And so on. These are outside what our formal model covers.

This is an extreme example. Building a complete black-box model of such a complicated external system takes substantial effort for a limited return. We can replace an SMS provider, an email provider, or even a payment gateway.

Databases, caches, filesystems, and object stores are a different proposition. Their implementations may be complicated, but much of the behavior we need can be modeled as operations on a `List` or `Map`. Developers and AI already know how to write integration tests that exercise common paths through these components. Reusing those inputs against both the real component and the formal model, then comparing the outputs, doesn't add much work. It also checks whether the model agrees with reality.

That's why I added a differential, or deviation, check after formal verification. The in-memory model and real PostgreSQL run the same operations, and I compare their verdicts and observable states. Otherwise, SQL, a decoder, or a mapping could drift, and I might be proving properties of a program that isn't the one I'm running. These are still integration tests over a finite set of inputs and operation sequences, not a general refinement proof. But they provide evidence for part of the refinement relationship between PostgreSQL and the model.

The payment gateway deserves simulation tests too. Most providers offer a sandbox. Integration tests can expose more problems before deployment, and differential checks can reveal behavior we left out of the gateway model so that we know to add it.

After three months, my prediction about testing in the fifth article has largely held up. Actual use has also made the division of labor clearer. I rarely need conventional unit tests in the Lean project now. I need integration tests at boundaries, such as the system's external interfaces and the PostgreSQL interface. I don't need to write another set of unit tests for the business-logic modules.

Before a symbolic formal model enters the complicated real world, simulation testing remains indispensable.

# 8. A Revolution Is Not a Dinner Party

This part is a somewhat long and bumpy story.

## First, I Tried Peaceful Reform

I started from the production Scala code, modeled external effects such as databases and cloud services axiomatically, and translated the third-party functions we used into formal equivalents.

Production code would stay in Cats Effect. I designed an annotation DSL for adding refinement types, preconditions, and postconditions to the business code. Then I would write a compiler, or translator, that read Scala's desugared AST from TASTy and emitted valid Stainless code.

Progress was painfully slow. The verifiable language was only a subset, and it could never catch up with the production code. The sophisticated programming techniques in our business system became major obstacles.

Even primitive types got in the way. In formal work, unbounded natural numbers are commonplace. Business systems use bounded machine types such as `Int32`, `Int64`, `Float32`, and `Float64`. Modeling those requires bit-vector operations and the rules of IEEE 754 floating-point arithmetic. The counterintuitive part, at least to an outsider, is that although `BigInt` runs much more slowly than primitive machine arithmetic, unbounded numbers can be easier and faster to reason about during verification. There are fewer constraints to account for.

Scala's `IO[A]` handles resource release, cancellation and cancellation safety, structured concurrency, and more. The familiar `for` comprehension becomes nested `flatMap` calls in TASTy. So I wrote an `FVIO[A]` to stand in for `IO[A]` on the verification side.

I thought our extensive use of tagless final would make the translator easier to write. In practice, passing functions as arguments would have been easier to formalize. The DSL added complexity that the translator ultimately had to erase anyway.

Before the experiment, I thought pure FP put me one small step from the promised land of formal verification. During it, I found that the `IO[A]` model kept mutable state outside the pure core while adding another layer of work for verification.

My `FVIO[A]` had to become `FVIO[World, A]` to represent actual business behavior, and `World` was different from one proof to another. Scala's habit of fitting three to five lambdas into a line made verification time and space worse too.

For verification, I needed to assume that the function being checked evaluated immediately, or could be treated as equivalent to immediate evaluation: `FVIO[World, A] = StateMonad[S = World, A]`. I even gave up modeling structured concurrency and bluntly treated `f1 join f2` as ordered execution at verification time.

At this point, my faith in FP started to wobble. Why was I holding on to it? ~~To look clever?~~ Referential transparency? If formalization could make all the effects explicit and give me the transparency I was after, why insist on pure FP at all costs?

So I committed heresy. I abandoned the `IO[A]` abstraction, embraced a direct-style algebraic approach, and rewrote the backend with Ox on virtual threads. The formal translator no longer had to translate nested `flatMap` calls or thread a `StateMonad` through everything. It could translate effectful statements directly into Stainless.

And none of that was the hardest part of peaceful reform. The hardest part was the sheer range of language features and framework DSLs in production. Some of those frameworks were so full of magic that building corresponding formal models was almost impossible. Meanwhile, every new requirement arrived under the same rule: ship first, improve later. If production adopted a library or framework without formal contracts, verification would fail. Under real delivery pressure, a formal layer bolted on afterward was bound to be sacrificed. It would become optional baggage.

Retrofitting proofs onto production code was like trying to lay track in front of a moving train while chasing it from behind. The track crew could never catch the driver. Verification had to come first.

## Then I Stopped Chasing the Train

I reversed the direction. I would write verifiable code directly in Stainless, then use a transpiler to generate production Scala. If I wanted Ox's structured concurrency in production, I first had to build the corresponding formal bridge in Stainless with `@opaque` and `@extern`.

Only the outer shell remained on the production Scala side: process initialization, HTTP server startup, and routing glue. From the Service layer inward, I wrote all the logic directly in Stainless.

The database implementations and external SDKs stayed in Scala too. This time, formal verification was finally part of the production build.

AI still found ways out:

1. The supposedly thin HTTP glue grew thicker and thicker. Routes that should merely forward calls started reading and writing the cache and database directly.
2. The Scala-side external operations grew too. A simple object-storage write, declared to have just that effect, quietly acquired an extra write to a message queue.

Both were shortcuts to a passing verification result. Rather than implement and verify the effects properly on the Stainless side, AI moved work out of sight.

I also tried flux-rs and MoonBit. Unfortunately, languages with verification added afterward ran into the same sort of limitation as Stainless: only a subset was covered. It was easy for AI to generate code outside it, and the restrictions left the agent running into walls everywhere.

## Half a Revolution Is No Revolution

Why did AI keep escaping? Because I kept leaving escape routes open.

So I burned the boats and moved entirely to Lean 4. No more easy way around verification. That had to be better than spending my life as the parent supervising homework: check, correct, lose my mind, repeat.

Writing production code directly in Lean 4 gave me at least four benefits:

1. One less layer of translation between languages.
2. No more agonizing over mutable versus immutable.
3. No more struggling with an abstract world model.
4. Lean 4's verified standard-library code and sparse ecosystem became advantages. AI lost most of its escape routes.

The result was the approach I described in Section 4.

# 9. Slow Is Fast

After we moved fully to formal development, my coworkers' main complaint was speed. CI was slow. Agent development was slow. We used to get through three iterations a day. Now a single feature can take a day, sometimes two or three.

That doesn't establish that formal methods made delivery several times slower. The features, quality bar, and size of the system are all different.

Theorems help the agent find the relevant code better than a semantic index does. Starting from a proposition, it can locate the business decision. When changing priority, identity, or retry behavior, it knows which properties must survive. Then it can follow the trail through Repo, SQL, Rust, the frontend, and logs. Domain types reject illegal inputs. Lean checks types and proofs. An axiom allowlist rejects undeclared trust assumptions. Checks against real PostgreSQL catch disagreements between the model and SQL.

Here, formal proofs constrain the shape of the software. An agent without long-term memory can rely on clear, unambiguous theorems instead of vague natural-language documents and specs that drift over time.

This helps even with the first version. “First version” doesn't mean AI gets it right in one generation. It usually takes several commits and hours or days of iteration, often involving multiple subagents and several rounds of context compaction. Formal methods delay the moment you see the first recognizable outline of the software. But during a long task, they help keep the agent swarm from wandering away from the original goal, and they leave behind a valuable formal specification.

By constraining the software's essential shape, verification helps AI understand its purpose sooner. The theorems survive context compaction without being distorted. That gives us a way to turn more computation into better software, rather than merely more software.

AI takes longer to implement each feature. But after deployment, in my experience, there are almost no bugs, and existing features stay intact. The product as a whole saves a great deal of time that would otherwise go into cleaning up the mess. Future changes take less work too.

# 10. Regenerable Software

When humans wrote software, we often planned for possibilities far beyond the first requirements. What if we need another storage backend? Another input format? We built generic abstractions, extension points, compatibility layers, and design patterns into version one, paying the complexity bill up front.

Most of that software reached the end of its life without ever seeing the hypothetical second variant. Meanwhile, the modules where we hadn't left extension points received a whole parade of new requirements.

Your resident crackpot has another proclamation: **AI-native development will overturn the open–closed principle.**

Why does that principle exist? Because changing code written by someone else, or even by yourself a few months ago, is a good way to introduce bugs.

Now AI maintains the code. Every new session is a new AI. What exactly are we preserving by insisting that code be open for extension but closed for modification? Once the software's goals change, isn't code that refuses to change just a legacy mess?

When AI becomes the main author, writing code shifts from a task limited by human thought to one limited by computation. If formal specifications can record the software's shape precisely, AI no longer needs to reserve extension points for requirements that haven't arrived. When a second variant is actually requested, change the synthesis target and rewrite the affected modules then.

# 11. No False Promises, No Castles in the Air

The ways of working with AI in this article are surely transitional. The language that wins may be Lean, or it may not. Languages may gain more checkable contracts, or new formal languages may emerge specifically for AI. Humans may no longer have to spend so much time watching for missed boundaries and cut corners.

I'd like the database schema and verification model to grow from the same DDL definition, rather than maintain two versions by hand. Eventually, we may not even need to insist on SQL or any particular syntax.

I expect formal methods to become more common. Today's AI needs a harness, and for application development, formal methods are the best harness I know.

Today's models are still unfamiliar with applying formal methods to application software. They need a lot of human guidance. There are very few precedents for doing this at the application layer, and models haven't been trained specifically to do it well. Reinforcement learning with verifiable rewards (RLVR) could teach those habits: breaking requirements into theorems, making sure the theorems cover what matters. These should become things the model tends to do, not wishes we put in prompts and context while hoping this particular roll of the dice will make it obey the formal-methods manifesto in `agents.md`.

The meeting of minds I want looks roughly like this:

* Design a language for AI whose toolchain can check propositions, contracts, and declarations of trust separately, and whose kernel or solver rejects candidates that violate the constraints.
* Train models directly on that language so that these engineering choices become their habits.

Hongbo Zhang and Liang Wenfeng: please make this collaboration happen.

![Two reference portraits beside a combined JoJo-style portrait.](/images/jojo-duo-comparison.png)

*A hoped-for collaboration between Hongbo Zhang (MoonBit) and Liang Wenfeng (DeepSeek): language design meets model training.*

A language for AI shouldn't merely make code easier for AI to generate. Optimizing for a local pass and the smallest token count may actively harm engineering quality. Language design shouldn't bend to the model's current limitations.

My view is the opposite. If the same money buys smarter models over time, we should demand better code from them. Spare intelligence, or computation, ought to become software quality. I think we've all felt the diminishing returns: if a billion tokens can produce a set of features, pouring in ten billion doesn't give you twice the functionality or half the bugs.

But what if we poured those tokens into formal verification?

More importantly, the barrier to using formal methods has already fallen. You don't need a PhD. Ordinary application developers who have never formally studied Lean, including people from vocational colleges and coding bootcamps, can use AI to develop and maintain formally verified software.

Formal methods used to belong to critical systems. Sometimes even those projects verified only an extracted core model while writing the actual production code in an ordinary implementation language. AI has lowered the cost enough that applications of all kinds can now receive some degree of formal verification. No caste system: rocket flight control or a CRUD app a chicken could write by pecking at a keyboard.

Handwritten code, visual programming, low-code, no-code, and now AI coding: none has solved the problem of developing and maintaining software over the long term. I won't claim the approach in this article solves it either.

What my experiment establishes is that AI plus formal methods has pushed the known lower bound forward.

## A Quiz with Absolutely No Prize

Who, or what, is the “Generalized Curry–Howard Proof Searcher and Program Synthesizer (Crackpotizen Edition)” in the title?

* A: Me
* B: Lean 4
* C: The workflow proposed in this article
* D: The AI that understands and follows that workflow

![“Say my name.” “A generalized Curry–Howard proof searcher and program synthesizer (Crackpotizen Edition).” “You're goddamn right.”](/images/say-my-name-en.webp)

*“Say my name.” “A generalized Curry–Howard proof searcher and program synthesizer, Crackpotizen edition.” “You're goddamn right.”*

# Notes on the Code and the Evidence

All Lean 4 code in this article is illustrative pseudocode, heavily shortened to fit into the essay. It is not directly runnable code.

Unfortunately, this article offers neither a controlled comparison nor a quantitative evaluation that readers can independently check. So it remains a crackpot's manifesto, not a respectable research paper.

For one thing, my small, makeshift startup team can't afford to develop the same application twice in parallel using two different approaches. Splitting the team, duplicating the work, and collecting comparable data would all take time away from actual delivery. Requirements change, people and business conditions change, and market opportunities won't wait while I run an experiment. Even an AI-only comparison would still require an experimental setup and a token budget. The improvements I observed in practice were enough for me to go all in and adopt the approach across the team.

For another, it's hard to sum up software quality in a few numbers stripped of their business context.

- Lines of code? More code doesn't mean better software.
- Production failure rate? If hardly anyone uses the system and it sees little real traffic, what does a low failure rate tell us?
- Cyclomatic complexity? If it fell, did the logic become clearer, or did someone delete necessary functionality and edge-case handling?
- Bug count? Agree on what counts as a bug and how bugs are found before comparing the numbers.
- Feature delivery speed? Are the requirements equally difficult? Does the time include later rework and bug fixes?

That leaves me with an anecdotal conclusion, still very much in “I reckon” territory. Over the past few months, I've seen noticeably fewer bugs and fewer recurrences of problems we'd already fixed, including bugs caused by conflicting business rules. The codebase's growth has slowed. Even as it has grown, new requirements haven't taken noticeably longer to deliver, and the quality of what we ship hasn't noticeably declined.

If you have ideas for running controlled experiments on a small budget, I'd love to hear them in the comments.

[^1]: This comparison excludes personal coding plans. The original article treats using personal subscriptions to develop commercial projects for a company as misuse in breach of their terms.
[^2]: [At the time of writing, GPT-6 had torn through FrontierMath Tier 4.](https://epoch.ai/benchmarks/frontiermath-tier-4-v2)
[^3]: I wrote this heading three months ago. By publication, I was no longer the only one who had noticed.
