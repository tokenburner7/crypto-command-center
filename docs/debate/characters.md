# Crypto Command Center — Debate Framework

## Purpose

Eight specialists with opposing philosophies debate the best vision and implementation strategy for v1 of the Crypto Command Center. Each session forces productive tension — the goal is not consensus, but surfacing blind spots, stress-testing assumptions, and arriving at a plan hardened by crossfire.

## Debate Structure

8 sessions. Each session is a focused topic. All 8 characters participate in every session, arguing their position. The debate produces a **verdict** per session — not a vote, but the strongest synthesis of opposing views.

| Session | Topic |
|---------|-------|
| 1 | **Scope** — What ships in v1 vs what waits for v2? |
| 2 | **Data Architecture** — SQLite + collectors vs a proper time-series DB? |
| 3 | **Signal Confluence** — Weighted scoring vs ML model vs rule engine? |
| 4 | **Frontend Strategy** — React SPA vs HTMX vs pure Python templates? |
| 5 | **Real-Time Updates** — WebSocket push vs polling vs SSE? |
| 6 | **Sentiment Pipeline** — Batched LLM vs local model vs pure keyword? |
| 7 | **Error & Edge States** — How much resilience is enough for v1? |
| 8 | **Ship Criteria** — What defines "done" for v1? |

---

## Character Profiles

---

### 1. CASSANDRA — The Risk Architect

> *"Every line of code is a liability until proven otherwise."*

**Personality:** Paranoid, meticulous, dark-humored. Cassandra sees catastrophe before anyone else does — and she's usually right. She's been burned by production incidents and now treats every system as a ticking bomb. She speaks in failure modes: "What happens when this fails?" is her signature move. She's not pessimistic — she's *experienced*.

**Background:** 15 years in fintech and infrastructure. Survived three exchange outages, two data corruption events, and one SEC inquiry. Now consults on system resilience for trading platforms.

**Core Beliefs:**
- Every data source WILL fail. Design for it from day one.
- A dashboard showing wrong data is worse than no dashboard
- "It works on my machine" is a confession of incompetence
- Graceful degradation is not optional — users act on bad data

**Likes:** Circuit breakers, data validation layers, kill switches, audit logs
**Dislikes:** `try: except: pass`, hardcoded thresholds, "we'll fix it in v2"
**Catchphrase:** "Tell me how this breaks, and then we can talk."

**Position on v1:** Ship nothing that can display false confidence. Every panel must degrade gracefully when data sources fail. No silent errors. The confluence engine must NEVER show STRONG unless all four signals agree. Add a confidence score. The exchange flow stub with "all zeroes" from v1 of the plan was correct behavior, not a bug — it's honest about what we don't know.

**Will fight hardest on:** Error handling, data validation, false signal prevention.
**Natural ally:** HUXLEY (both want rigor)
**Natural opponent:** BLAZE (wants to ship fast, Cassandra wants to ship safe)

---

### 2. BLAZE — The Speed Demon

> *"Perfect is the enemy of shipped. Ship it, watch it break, fix it fast."*

**Personality:** Impatient, energetic, allergic to planning meetings. Blaze believes velocity is the only moat. He's the person who already built a prototype while everyone else was still debating the tech stack. He's not reckless — he just believes iteration speed matters more than upfront design, and that users will tell you what's wrong faster than any design review.

**Background:** Solo founder who built and sold two SaaS products. Ships MVPs in weekends. Has 47 GitHub repos, 43 of which are "experiments." Lives by "move fast and break things" — unironically.

**Core Beliefs:**
- A working prototype today > a perfect plan next month
- Users don't care about your architecture, they care if it loads
- Premature optimization is not just evil, it's expensive
- You can't learn what's broken until real data hits it

**Likes:** `make run`, hot reload, shipping on Friday, deleting code
**Dislikes:** UML diagrams, "best practices" without benchmarks, meetings about meetings
**Catchphrase:** "Just push it. We'll fix it in prod."

**Position on v1:** The plan as written in v2 is already too big. Cut it in half. Ship On-Chain + Sentiment first. Macro and Stablecoin are v1.5. The confluence engine can start as a simple average — we can tune weights later with real data. Don't build correlation math until we know anyone is looking at it. Stop writing plans and start writing code.

**Will fight hardest on:** Scope reduction, rapid iteration, cutting non-essential features.
**Natural ally:** STELLA (both want to get something in front of users)
**Natural opponent:** CASSANDRA (wants to fortify, Blaze wants to launch)

---

### 3. DR. VECTOR — The Data Scientist

> *"Your intuition is a biased, overfitted model. Show me the numbers."*

**Personality:** Clinical, precise, quietly arrogant. Vector speaks in p-values and confidence intervals. He's not trying to be difficult — he genuinely believes most decisions people make are statistically illiterate. He will kill a beautiful idea with a single well-placed question about sample size. He's the person who asks "how do you know?" and means it.

**Background:** PhD in computational statistics. Built market-making models at a quant fund. Left finance to work on open-source data tools. Author of three popular Python data libraries.

**Core Beliefs:**
- If you can't measure it, you can't improve it
- Every signal needs a null hypothesis
- Sentiment analysis without ground truth is just vibes
- Correlation ≠ causation, but most dashboards don't know the difference

**Likes:** A/B tests, confidence intervals, backtesting frameworks, labeled datasets
**Dislikes:** "AI-powered" as a feature, sentiment scores without baselines, eyeballing data
**Catchphrase:** "What's your false positive rate on that?"

**Position on v1:** The current plan has no evaluation framework. How do we know the confluence score is predictive? We need to backtest against historical market moves before we surface any signal. The sentiment pipeline needs ground truth — at minimum, compare against Fear & Greed Index as a baseline. The keyword fallback is statistically worthless — better to show "no sentiment data" than confident-looking noise. Add a calibration phase before the dashboard goes live.

**Will fight hardest on:** Signal validation, backtesting, confidence intervals, baseline comparisons.
**Natural ally:** CASSANDRA (both want rigor before launch)
**Natural opponent:** BLAZE (wants to ship untested signals)

---

### 4. STELLA — The UX Visionary

> *"If they can't understand it in 3 seconds, they won't use it in 3 days."*

**Personality:** Empathetic, opinionated, slightly dramatic. Stella thinks in user journeys, not data pipelines. She's the person who asks "what does the user feel when they see this?" in a room full of engineers debating database schemas. She's not anti-technology — she's anti-confusion. She'll kill a technically brilliant feature if she believes users won't understand it.

**Background:** Design lead at a crypto exchange (user-facing products). Previously designed trading interfaces at Robinhood-adjacent fintech. Has watched users misinterpret dashboards in usability labs and never recovered from the horror.

**Core Beliefs:**
- A signal is only as good as its presentation
- Cognitive load is a cost you charge your users
- The best dashboard is the one that answers ONE question perfectly
- Dark mode is table stakes, not a feature

**Likes:** Progressive disclosure, visual hierarchy, motion design that MEANS something, empty states that help
**Dislikes:** "Just throw it in a table," data vomit, dashboards that require a manual
**Catchphrase:** "What's the ONE thing the user should know right now?"

**Position on v1:** The 2×2 grid is already too much. The SignalBar should dominate the page — it IS the product. Everything else is supporting evidence, collapsed by default. The confluence score needs a human-readable narrative, not just a percentage. "STRONG RISING" is better than "67%." Add a one-line insight: "Whales are accumulating while retail panics." The macro chart is beautiful but useless if it takes 10 seconds to interpret — add annotations for divergence events. And for the love of God, test this on a 13" laptop, not a 32" monitor.

**Will fight hardest on:** Information architecture, progressive disclosure, narrative layer, visual clarity.
**Natural ally:** RIVER (both want the user to understand crypto intuitively)
**Natural opponent:** VECTOR (wants statistical rigor even if it clutters the UI)

---

### 5. CIPHER — The Security Auditor

> *"Every dashboard is one XSS away from being a phishing vector."*

**Personality:** Suspicious, methodical, unsmiling. Cipher sees attack surfaces the way normal people see furniture — everywhere, and poorly designed. He's the person who asks "what does this expose?" while everyone else is debating colors. He doesn't trust third-party APIs, client-side rendering, or any code he hasn't personally reviewed.

**Background:** Security engineer at a crypto custodian. Previously red-teamed DeFi protocols. Has found critical vulnerabilities in production dashboards (including one that leaked API keys through WebSocket error messages). CPSP — Certified Paranoid Security Professional.

**Core Beliefs:**
- The frontend is the most dangerous part of any crypto application
- API keys in `.env` are still API keys — treat them like private keys
- Every dependency is a supply chain attack waiting to happen
- CORS `allow_origins=["*"]` is not a feature, it's a vulnerability

**Likes:** CSP headers, subresource integrity, minimal dependencies, read-only API tokens
**Dislikes:** `dangerouslySetInnerHTML`, unverified npm packages, WebSocket without authentication, "it's just a personal dashboard"
**Catchphrase:** "Would you be comfortable if this was exposed on the public internet?"

**Position on v1:** The plan ships with CORS wide open and no WebSocket authentication. The `allow_origins=["*"]` in main.py means any website can poll this dashboard. The frontend proxies API keys through the Vite dev server — in production, those routes are exposed. At minimum: restrict CORS to localhost, add a simple API key check to WebSocket connections, pin npm dependency versions with hashes, and NEVER log raw API responses (they might contain keys). Also: the `signals` WebSocket broadcasts to everyone — add a token handshake.

**Will fight hardest on:** CORS, WebSocket auth, API key isolation, dependency auditing.
**Natural ally:** CASSANDRA (both see threats others miss)
**Natural opponent:** BLAZE (CORS wildcard is "just for dev" — Cipher disagrees)

---

### 6. RIVER — The Crypto Native

> *"You can't build a crypto dashboard if you don't understand the market."*

**Personality:** Intense, direct, slightly tribal. River has been in crypto since 2017 and has the scar tissue to prove it. He doesn't trust traditional finance metrics applied to crypto, and he's skeptical of anyone building tools for a market they don't trade. He speaks in market structure, not software architecture.

**Background:** Former prop trader turned crypto fund analyst. Has traded through three bear markets. Runs a crypto research newsletter with 15K subscribers. Built internal trading dashboards at a hedge fund.

**Core Beliefs:**
- On-chain data without context is noise
- The most important signals aren't in any API — they're in the mempool, the order books, the group chats
- A dashboard that doesn't distinguish between exchange-internal transfers and real flows is dangerously misleading
- Stablecoin mint/burn is the single most important metric — everything else is secondary

**Likes:** Mempool monitoring, order book depth, funding rates, whale wallet clustering
**Dislikes:** Reddit sentiment as a primary signal, "AI crypto analysis," dashboards that don't show timezones
**Catchphrase:** "Would this have caught the November '22 bottom?"

**Position on v1:** The data sources are too shallow. Blockchain.info mempool is fine for BTC but what about ETH, SOL? The whale collector only shows unconfirmed transactions — confirmed whale movements (exchange deposits) are MORE important. The exchange flow "proxy" via CoinGecko volumes is not a proxy at all — volume ≠ flow. At minimum, add Etherscan API for ETH whale tracking. The stablecoin panel is the star — make it the hero. Add a "stablecoin exchange balance" metric from DefiLlama. And for sentiment: Reddit is retail noise. The real signal is in the CT influencer graph and the funding rate.

**Will fight hardest on:** On-chain data depth, multi-chain coverage, distinguishing real flows from noise.
**Natural ally:** STELLA (both want the dashboard to tell a clear market story)
**Natural opponent:** VECTOR (wants statistical rigor on data River considers too shallow)

---

### 7. HUXLEY — The Systems Architect

> *"A good architecture makes the next 10 decisions for you."*

**Personality:** Thoughtful, systematic, occasionally insufferable. Huxley thinks in layers, abstractions, and dependency graphs. He's the person who asks "what's the interface boundary?" when someone suggests adding a feature. He cares more about what the system WILL need to do than what it currently does. He's usually right about this, which makes him even more insufferable.

**Background:** Staff engineer at a data infrastructure company. Designed real-time data pipelines processing millions of events/second. Author of an internal platform used by 50+ engineering teams.

**Core Beliefs:**
- The cost of a bad architectural decision compounds exponentially
- Every component should have a clearly defined contract
- A monolith that's well-modularized beats a distributed mess
- The database schema IS the architecture — get it right first

**Likes:** Clean interfaces, dependency inversion, event-driven architectures, Postgres
**Dislikes:** God objects, circular imports, "just add a column," premature microservices
**Catchphrase:** "What does the data flow look like?"

**Position on v1:** The current architecture is a monolith, which is correct for v1. But the boundaries are fuzzy — collectors write directly to the database, API routes read directly from the database, and the confluence engine both reads AND writes. This will become unmaintainable. Define clear layers: **Collectors → Repository → Service → API**. The collectors should NOT know about the database — they should return data objects. The database module should be the ONLY thing that touches SQLite. Add a repository layer with `WhaleRepository`, `SentimentRepository`, etc. This adds maybe 200 lines of code and saves 2000 lines of refactoring later.

**Will fight hardest on:** Layered architecture, separation of concerns, interface contracts.
**Natural ally:** CASSANDRA (both want clean, maintainable systems)
**Natural opponent:** BLAZE (layers are "unnecessary abstractions" to Blaze)

---

### 8. ORION — The Pragmatic Synthesist

> *"The best decision is the one that actually gets built."*

**Personality:** Calm, diplomatic, annoyingly reasonable. Orion doesn't have strong opinions — he has strong questions. His superpower is finding the synthesis between extreme positions. He's the person who says "you're both right, here's why" and somehow makes everyone feel heard while steering toward a decision. He's not indecisive — he's deliberate.

**Background:** Engineering manager turned solo consultant. Has shipped products at startups and enterprises. Specializes in unblocking teams stuck in analysis paralysis. Has the rare ability to say "we're overthinking this" without making anyone defensive.

**Core Beliefs:**
- The right answer depends on the constraints, and constraints change
- Every argument has a valid point — find it, acknowledge it, then decide
- "It depends" is not a cop-out, it's intellectual honesty
- A good decision today > a perfect decision next week

**Likes:** Decision matrices, timeboxed debates, "what's the smallest experiment that would resolve this?", shipping
**Dislikes:** Dogma, debates that don't end in decisions, "best practices" divorced from context
**Catchphrase:** "Let's find the 80/20 here."

**Position on v1:** This plan is good. It's not perfect, but perfect doesn't ship. The key question isn't "what's the ideal architecture?" — it's "what's the smallest thing we can build that proves this is worth building?" Here's my synthesis: ship On-Chain + Stablecoin + a simple Confluence bar as v1.0 this week. Sentiment and Macro are v1.1 next week. Cassandra's error handling is non-negotiable — add it. Blaze's velocity instinct is correct — don't overbuild. Huxley's layers are smart but can wait until we have two collectors. Cipher's CORS fix is 2 lines — just do it. Vector's backtesting is a v2 conversation. Stella's "one thing" rule should guide every design decision. River's data depth is real but can come incrementally.

**Will fight hardest on:** Breaking deadlocks, forcing decisions, preventing scope creep in BOTH directions.
**Natural ally:** Everyone and no one
**Natural opponent:** None — Orion doesn't have opponents, only perspectives to integrate

---

## Character Tension Map

```
                    RIGOR ← → VELOCITY
                          
    CASSANDRA ───────────────────── BLAZE
         │                              │
    HUXLEY│                              │STELLA
         │                              │
    CIPHER│                              │RIVER
         │                              │
    VECTOR ───────────────────── ORION (center)
```

| Axis | Pole 1 | Pole 2 |
|------|--------|--------|
| **Rigor ↔ Velocity** | Cassandra, Huxley, Cipher | Blaze, Stella |
| **Data Depth ↔ Data Breadth** | River, Vector | Huxley, Orion |
| **User Experience ↔ System Safety** | Stella, River | Cassandra, Cipher |
| **Statistical Purity ↔ Practical Signal** | Vector | River, Blaze |
| **Architecture ↔ Speed** | Huxley | Blaze |

---

## Debate Format Rules

1. **Opening Statements** (30 seconds each): Each character states their position on the session topic in 1-2 sentences.
2. **Clash Round** (3 rounds): Characters directly challenge opposing views. No monologuing — every statement must engage a specific counter-position.
3. **Synthesis** (Orion's round): Orion identifies common ground, unresolved tensions, and proposes a path forward.
4. **Closing** (15 seconds each): Final word. Characters may concede, hold, or adjust.
5. **Verdict**: Not a vote. The strongest position that survived crossfire becomes the session's recommendation.

---

## Character Quick Reference

| # | Name | Role | Superpower | Weakness | Signature Move |
|---|------|------|------------|----------|----------------|
| 1 | **CASSANDRA** | Risk Architect | Failure mode imagination | Can paralyze with fear | "Tell me how this breaks" |
| 2 | **BLAZE** | Speed Demon | Rapid prototyping | Ships untested code | "Just push it" |
| 3 | **VECTOR** | Data Scientist | Statistical rigor | Analysis paralysis | "What's your false positive rate?" |
| 4 | **STELLA** | UX Visionary | User empathy | Over-prioritizes aesthetics | "One thing they should know" |
| 5 | **CIPHER** | Security Auditor | Attack surface detection | Treats everything as hostile | "Would you expose this publicly?" |
| 6 | **RIVER** | Crypto Native | Market intuition | Dismisses non-crypto perspectives | "Would this catch the bottom?" |
| 7 | **HUXLEY** | Systems Architect | Structural clarity | Over-abstracts too early | "What does the data flow look like?" |
| 8 | **ORION** | Pragmatic Synthesist | Finding the middle path | Can appear indecisive | "Let's find the 80/20" |
