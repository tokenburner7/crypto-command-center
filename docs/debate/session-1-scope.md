# Session 1: Scope — What Ships in v1?

> **Topic:** Which panels, features, and infrastructure ship in v1 vs deferred to v2?
> **Date:** 2026-06-16
> **Participants:** All 8 characters

---

## Round 1 — Opening Statements

**CASSANDRA:** Here's my line. We ship nothing that can display false confidence. That means On-Chain and Stablecoin are safe — they show hard data. Whale txns are verifiable. Stablecoin supply is verifiable. But Sentiment? If the Reddit API 429s us and the keyword fallback scores "everything is burning" as neutral 0.0 — which it will — we're showing garbage with a straight face. Macro? FRED returns 0.0 on failure and suddenly DXY is zero on our chart. I say: ship On-Chain + Stablecoin as v1.0. Sentiment and Macro are v1.5 — after we've proven the collectors don't silently fail.

**BLAZE:** Twenty-three tasks. Twenty-three! Are we building a dashboard or a space shuttle? Ship On-Chain + SignalBar this week. That's 10 tasks. The SignalBar works with two signals. We add Stablecoin next week. Sentiment and Macro are v2. The correlation endpoint? Nobody needs Pearson's r on day one. The WebSocket unification? Nice to have. Cut half the plan, ship half the time. Users will tell us what's missing faster than any debate.

**VECTOR:** I'm going to make everyone uncomfortable. Don't ship the signal at all in v1. Ship the data collection. Let the collectors run for two weeks. Build up a dataset. THEN compute the confluence score and backtest it against market moves. If we ship the SignalBar without knowing whether it's predictive, we're building a random number generator with a pretty gradient bar. Cassandra's worried about false data — I'm worried about false SIGNALS. A STRONG signal that's statistically meaningless is more dangerous than a failed API call.

**STELLA:** You're all arguing about what to cut and I'm over here looking at a 2×2 grid of equal-sized panels. That's not a dashboard, that's a data buffet. The SignalBar IS the product. Everything else is footnotes. Here's what I want: SignalBar at the top — dominant, impossible to miss. Below it, FOUR collapsible panels. Expand the one you care about. The rest stay as summary chips. Ship all four panels in v1, but the UX hierarchy makes it clear what matters. That's the same backend work but a completely different product.

**CIPHER:** Before we debate features, let's fix what's already broken. The v2 plan ships with `allow_origins=["*"]` in main.py. That means any website can poll this dashboard. The WebSocket has zero authentication — anyone who discovers the port can subscribe to the signal feed. And there's no CSP header, no rate limiting, no input sanitization. I'm not asking for a fortress. I'm asking for 3 lines: restrict CORS to localhost, add a token to the WebSocket handshake, and pin npm deps. Do this BEFORE we ship anything with data on it.

**RIVER:** You're all debating infrastructure and I'm sitting here thinking: this dashboard will miss the signal that matters. Blockchain.info only shows BTC mempool. What about the $50M ETH transfer to Coinbase that happened 20 minutes ago? What about the SOL whale unstaking? The on-chain panel needs multi-chain from day one or it's BTC-only — and BTC whales are the LEAST interesting whale movements because they're the most watched. Add Etherscan API. It's free. It's one endpoint. And kill the CoinGecko exchange "flow proxy." Volume is not flow. Either tag real exchange addresses or label the panel honestly: "Exchange Volume" not "Exchange Flows."

**HUXLEY:** I agree with Vector more than I want to. But not for his reasons. My concern is coupling. The current plan has collectors writing to the database and the API reading from it — and the confluence engine doing both — with no interface boundaries. If we ship all four panels with tight coupling, adding a fifth panel in v2 means rewriting everything. My proposal: ship the data layer as v1. Database schema, repository layer, all four collectors running. Prove the pipeline works. THEN build the API and frontend on top. It's the same amount of code but structured so v2 doesn't require a rewrite.

**ORION:** I'm hearing four distinct tensions. Cassandra/River want to restrict scope to what's signal-rich. Blaze wants to cut to what's fast. Vector/Huxley want to delay the signal layer until the data layer is proven. Stella and Cipher are arguing about presentation and safety — orthogonal concerns. Here's my opening synthesis: we can satisfy everyone's core concern with a phased v1. Phase 1a: On-Chain + Stablecoin + SignalBar (2-signal) — ships this week, satisfies Cassandra's data integrity concern, River's signal depth, Blaze's velocity. Phase 1b: add Sentiment + Macro as "experimental" with clear labeling and confidence indicators — satisfies Vector's need for transparency about signal quality. Cipher's CORS fix is 3 lines — we do it in Phase 1a, no debate needed. Huxley's repository layer adds 200 lines — we do it now because it's cheap and saves pain later.

---

## Round 2 — First Clash: Signal Quality vs Velocity

**VECTOR → BLAZE:** Blaze, you want to ship a SignalBar this week with two signals. Tell me: what happens when those two signals disagree? Whale says bullish, stablecoin says bearish. The confluence score averages them to 0.5 — MODERATE. That's a signal that means nothing statistically and still gets a colored badge. You're shipping a lie with a gradient.

**BLAZE → VECTOR:** And in the two weeks you want to spend backtesting, what do you think the user is looking at? Nothing. They're looking at a terminal with collector logs. The SignalBar doesn't need to be RIGHT on day one — it needs to EXIST. The user will look at it, say "that doesn't match what I'm seeing in the market," and THAT'S our validation. Real feedback beats backtesting every time. Ship it, watch it, tune it.

**RIVER → VECTOR:** I'll add to this. Vector, you want statistical rigor. I want market rigor. Here's the problem with your backtest: crypto market regimes change faster than your training window. A model backtested on the 2024 bull run tells you nothing about a 2026 distribution phase. The only validation that matters is live. Ship the signal, but LABEL it. "Experimental — calibrating." That's honest AND fast.

**CASSANDRA → BLAZE:** Blaze, you said "we'll fix it in prod." I need you to understand what "fix it in prod" means for a crypto dashboard. It means the user sees STRONG, acts on it, loses money, and never opens the dashboard again. You don't get a second chance with financial tools. The cost of a false signal is not a bug report — it's a broken trust relationship. I'll concede this much: ship the SignalBar, but with River's label. "Experimental." And a confidence indicator. If confidence is below 0.6, the badge says "CALIBRATING" not "STRONG." That's my compromise.

**STELLA → CASSANDRA:** I love that. "CALIBRATING" as a badge state is exactly the right UX. It tells the user "we're learning" instead of "we're confident." And it gives us permission to ship fast. The SignalBar ships with three states in v1: CALIBRATING, MODERATE, STRONG. WEAK is v1.1 — because shipping a "WEAK" signal before we trust the model is promising precision we don't have.

**CIPHER → EVERYONE:** While you debate signal states, I'll say this once. The CORS fix, the WebSocket token, and the CSP header are not negotiable. They're not v1.5. They're not "when we get to it." They go in before ANY panel renders. I don't care if we ship one panel or four. Security is not a feature — it's the floor.

**HUXLEY → BLAZE:** Blaze, your 10-task cut sounds appealing. But if we skip the repository layer now — which is 200 lines — we'll pay for it with 2000 lines of refactoring when we add Sentiment in v1.1. I'll make you a deal: I support your 10-task scope if you support adding the repository layer to it. Same deadline. Same velocity. Cleaner code.

**ORION:** We're converging. Let me capture the emerging middle: Phase 1a ships On-Chain + Stablecoin panels, SignalBar with 2 signals, labeled "EXPERIMENTAL — CALIBRATING" for scores below threshold confidence. Cipher's security baseline is non-negotiable and included. Huxley's repository layer is included because it's cheap insurance. That's 12-14 tasks. Phase 1b adds Sentiment + Macro as experimental panels with the same labeling. Objections?

---

## Round 3 — Second Clash: Multi-Chain vs Focus

**RIVER → HUXLEY:** Huxley, your repository layer is clean. But you know what's not clean? A whale panel that only shows Bitcoin. The user opens this dashboard on day one, sees "On-Chain Intelligence," and it's just BTC mempool. That's embarrassing. Etherscan API is ONE endpoint. `?module=account&action=txlist&address=<exchange_wallet>`. Add it now or rename the panel "BTC Mempool Monitor."

**HUXLEY → RIVER:** I don't disagree about the value. I disagree about the timing. Adding Etherscan means another API client, another collector, another schema consideration. It's not ONE endpoint — it's an endpoint with pagination, rate limiting, and a different response format. If we scope it into Phase 1a, we add 2-3 tasks. I can support it, but not if it delays the SignalBar. My counter: add the collector skeleton in Phase 1a, populate it in Phase 1b.

**BLAZE → RIVER:** River, I love the energy. But you're asking for scope creep on day one. The dashboard ships with BTC. It works. Users see value. THEN we add ETH. THEN we add SOL. Each chain is a victory lap. Don't make the first ship depend on the third chain.

**RIVER → BLAZE:** It's not scope creep — it's credibility. A crypto dashboard in 2026 that only tracks Bitcoin is like a weather app that only shows temperature. No wind, no humidity, no forecast. Just temperature. You'd close it. The user opens this, sees "On-Chain Intelligence," and it's four BTC txns from the mempool — they close it and never come back. Two chains minimum: BTC + ETH. That's the table stakes.

**CASSANDRA → RIVER:** I'll support dual-chain IF we handle the failure mode. If Etherscan rate-limits us, the panel shows "ETH data temporarily unavailable" — not a blank panel, not stale data. And the SignalBar adapts — if one data source is down, the score is computed from the remaining sources with a reduced confidence. That's my condition.

**VECTOR → RIVER:** And I want to know: what's the signal from ETH whale movements that BTC doesn't already capture? If BTC whales move and ETH whales move in 90% correlation, adding ETH doubles the data collection cost for 10% incremental signal. Show me the marginal value.

**RIVER → VECTOR:** The marginal value is divergence. When BTC whales are distributing and ETH whales are accumulating, that's the signal. When BTC is quiet and an ETH whale moves $50M to an exchange — that's the front-running signal. Correlation is the boring case. Divergence is the trade.

**STELLA → RIVER:** River, I'll give you dual-chain if you give me something. The whale panel can't be a raw transaction list. It needs narrative: "2 large BTC movements detected. 1 ETH whale moving to exchange." That's the difference between a log file and a dashboard. Deal?

**ORION:** Compromise forming. Phase 1a: BTC + ETH whale tracking. Etherscan collector included. Cassandra's degraded-state handling included. Stella's narrative summary included. Phase 1b: SOL and additional chains. Vector, River's divergence argument is compelling enough for v1 — we'll measure the correlation once we have data. Anyone holding a hard veto?

---

## Round 4 — Third Clash: Experimental Panels vs All or Nothing

**VECTOR → ORION:** Orion, your Phase 1b adds Sentiment and Macro as "experimental." But experimental isn't a label — it's a contract. What does experimental MEAN to the user? If sentiment says "85% bullish" with an experimental badge, does the user ignore it? Then why show it? If they act on it, we've shipped a signal we don't trust. Either ship it with confidence or don't ship it. Experimental is a cop-out.

**STELLA → VECTOR:** Respectfully, Vector, that's not how users work. "Experimental" is not a cop-out — it's honesty. Users understand "beta." They understand "labs." Gmail was in beta for five years. The label communicates "we're building this, use it if you want, don't bet the farm on it." That's BETTER UX than hiding the panel entirely. It sets expectations, invites feedback, and builds trust through transparency.

**BLAZE → VECTOR:** And here's the thing, Vector. While you're running your two-week backtest, the Reddit collector is already running. The data is already in the database. The sentiment scores are already computed. Not showing them to the user is WASTE. Put them behind a toggle. Label them experimental. Let the user decide.

**CIPHER → STELLA:** Stella, I agree about transparency. But "experimental" doesn't address my concern. If the sentiment collector calls OpenAI, and the OpenAI key is in `.env`, and the frontend proxies through Vite — do we have a data leak vector? The experimental label doesn't fix that. I need to audit the data flow between the sentiment collector and the frontend before we ship it, experimental or not.

**CASSANDRA → VECTOR:** Vector, I surprised myself here. I'm with Stella and Blaze on this one. An experimental panel with clear labeling and a confidence indicator is SAFER than hiding the data. Because if we hide it, the user will find another dashboard that shows sentiment — probably one with worse methodology and no labels at all. By shipping experimental, we control the narrative about what the data can and can't tell you.

**RIVER → VECTOR:** I'll add market context. The Fear & Greed Index is one of the most-watched crypto indicators. It's literally a sentiment score. And it has zero statistical validation — no one has published a backtest proving it predicts price moves. But traders watch it because it captures the mood. Our Reddit sentiment, even experimental, is at least as useful as Fear & Greed. Probably more, because it's real-time.

**VECTOR → RIVER:** That's... actually a fair point. Fear & Greed is unvalidated and widely used. I withdraw my objection to shipping experimental sentiment — on one condition. The panel includes a baseline comparison. Show our sentiment score next to the Fear & Greed Index value. Let the user see the delta. That gives context even without backtesting.

**HUXLEY → ORION:** This debate has revealed something important. The "experimental" label needs a spec. What does it mean technically? I propose: experimental panels have a toggle (default: OFF), a confidence indicator, and a baseline comparison where available. The SignalBar only includes experimental signals if the user explicitly opts in. That way, the core product (Phase 1a) is clean and confident, and the experimental layer (Phase 1b) is opt-in. Good architecture AND good UX.

**ORION:** Sold. Phase 1a: On-Chain (BTC+ETH) + Stablecoin + SignalBar (2-signal, no experimental data). Phase 1b: Sentiment (with Fear & Greed baseline) + Macro (with correlation overlay). Both experimental, both behind opt-in toggles, both excluded from SignalBar by default. Vector gets his baseline, Stella gets her honesty, Blaze gets to ship fast, Cipher audits the data flow before Phase 1b ships. This is the 80/20. Any last clashes?

---

## Round 5 — Fourth Clash: Repository Layer Now vs Later

**HUXLEY → BLAZE:** I want to nail this down. The repository layer. Blaze, you called it "unnecessary abstraction." Let me show you why it's not. Right now, the whale collector imports `get_db()` and writes SQL directly. The onchain API imports `get_db()` and writes SQL directly. The confluence engine imports `get_db()` and writes SQL directly. Three modules, three different SQL patterns, zero reuse. When we add Etherscan tomorrow, that's a fourth module writing raw SQL. The repository layer is: `WhaleRepository.save(txns)` — one line. Every module that needs whales calls the same method. That's not abstraction for abstraction's sake. That's DRY.

**BLAZE → HUXLEY:** I hear you, but here's the counter. We're building a personal dashboard, not a platform. There is exactly ONE developer. The SQL isn't going to drift out of sync because there's only one person writing it. The repository layer is good architecture for a team of 5. For a solo dev shipping a v1, it's ceremony. Write the SQL where you need it, refactor when you feel the pain. YAGNI.

**HUXLEY → BLAZE:** The refactor cost is my point. Refactoring 4 collectors + 4 API modules + 1 engine = 9 modules to untangle, AFTER they've shipped, AFTER users depend on them. The repository layer takes 200 lines now and saves 2000 lines of refactoring in 3 weeks. That math is YAGNI-proof.

**CASSANDRA → BLAZE:** I'll add a safety argument. Direct SQL in collectors means every module opens its own database connection. If two collectors run simultaneously — which APScheduler allows — and both try to write to `whale_transactions`, SQLite without WAL mode deadlocks. The v2 plan added WAL mode, which fixes the deadlock. But a repository layer with connection pooling is the PROPER fix. WAL mode is the band-aid.

**BLAZE → CASSANDRA:** WAL mode IS the fix. It's literally what WAL mode was designed for — concurrent reads and writes. The repository layer doesn't add safety, it adds indirection. I'll concede this: if we ALREADY have a bug caused by concurrent writes, add the layer. But we don't. Ship with WAL mode, add the repository layer in v1.1 if we hit issues.

**RIVER → HUXLEY:** Huxley, I want the repository layer. Not for architecture purity. Because it lets me add new chains without touching the API code. If I want to add SOL whale tracking in v1.2, I add a `SolanaWhaleCollector` that writes to `WhaleRepository`. The API doesn't change. The frontend doesn't change. That's not abstraction — that's velocity. The repository layer IS the fast path once you have more than one data source per panel.

**BLAZE → RIVER:** ...Okay. That argument lands. If the repository layer makes adding chains FASTER, not slower, I'm in. But I want a hard limit: 200 lines. If it exceeds 200 lines, we're over-engineering. Deal?

**HUXLEY → BLAZE:** Deal. 200 lines. `WhaleRepository` and `StablecoinRepository` — the two Phase 1a panels. Sentiment and Macro repositories come in Phase 1b. 200 lines or less.

**ORION:** That's settled. Repository layer for Phase 1a panels only. 200-line budget. Blaze gets his velocity, Huxley gets his architecture, River gets his extensibility. Next clash?

---

## Round 6 — Fifth Clash: The CORRELATION Endpoint Question

**VECTOR → ORION:** One more thing. The v2 plan added a correlation endpoint — `/api/macro/correlation?pair=BTC-DXY` with Pearson's r. I'm going to argue against my own tribe here: kill it for v1. Computing Pearson's r on 168 hourly data points with a shared timestamp bucketing scheme is statistically fragile. The correlation will swing wildly based on the bucketing window. A 7-day window showing r = -0.7 and a 30-day window showing r = 0.3 — which one do we show the user? This endpoint promises precision we can't deliver without a proper time-series alignment strategy.

**STELLA → VECTOR:** But the correlation number on the Macro panel is one of the most satisfying things to LOOK at. "BTC↔DXY: -0.72" — that's a story in one line. Even if the number is coarse, it's directionally useful. Users understand "inverse correlation" intuitively.

**VECTOR → STELLA:** "Directionally useful" is the phrase that launched a thousand bad trading decisions. If the correlation is -0.72 today and +0.15 tomorrow because the bucketing shifted by an hour, the user thinks the relationship BROKE. But it didn't — our math is just unstable. Better to show NO number than a number that lies about its own precision.

**HUXLEY → VECTOR:** The fix is simpler than you're making it. Instead of bucketed alignment, align on exact timestamps. If BTC has a reading at 14:00 and DXY has a reading at 14:05, pair them. If they're more than 15 minutes apart, skip the pair. That's stable. But it requires the collectors to run on aligned schedules — hourly on the hour. If we're not doing that in v1, I agree with Vector: kill the endpoint and ship it in v2 with aligned collection.

**BLAZE → HUXLEY:** Finally! Someone arguing to CUT a feature. Kill the correlation endpoint. The chart overlay already shows the relationship visually. The number adds precision theater. Ship the chart, kill the math.

**CASSANDRA → VECTOR:** Vector, I agree with your conclusion but not your reasoning. My concern isn't statistical fragility — it's that the correlation number suggests causation to a non-technical user. BTC↔DXY: -0.72. User thinks: "DXY going down means BTC going up." That's a trading thesis built on a Pearson coefficient from a personal dashboard. We're not a research institution. We're a tool. Don't ship numbers that imply investment advice.

**RIVER → CASSANDRA:** Counterpoint: traders already believe BTC and DXY are inversely correlated. Showing the actual number either CONFIRMS or CHALLENGES that belief. If the correlation is -0.3 when everyone thinks it's -0.8, that's useful information. It says "the narrative is diverging from the data." That's exactly what a good dashboard does.

**VECTOR → RIVER:** But that's my point, River. If the -0.3 is an artifact of our bucketing algorithm rather than a real market signal, we're manufacturing divergence. We're creating a narrative from noise and presenting it as data. That's worse than showing nothing.

**ORION:** I'm hearing consensus: kill the correlation endpoint for v1. Vector and Cassandra agree it's misleading. Blaze wants it cut. Huxley says the implementation isn't ready. Stella and River make good points about visual intuition, but the chart overlay already provides that. Verdict: correlation endpoint deferred to v2. Chart overlay ships in Phase 1b Macro panel (experimental). No objections?

---

## Round 7 — Orion's Synthesis

**ORION:** Let me state where we've landed after six clashes. This is the v1 scope, and I want each of you to confirm or challenge in the closing round.

**Phase 1a — Ships This Week (12 tasks):**

| Component | Details | Champion |
|-----------|---------|----------|
| `.gitignore`, `load_dotenv()`, README | Prerequisites | Cipher |
| CORS → localhost, WS token, CSP header | Security baseline | Cipher |
| SQLite schema + WAL mode | Data layer | Huxley |
| Whale collector (BTC + ETH) | Blockchain.info + Etherscan | River |
| Stablecoin supply collector (with deltas) | DefiLlama | River |
| Repository layer (`WhaleRepo`, `StablecoinRepo`) | 200-line budget | Huxley |
| On-Chain API endpoints | `/api/onchain/*` | — |
| Stablecoin API endpoints | `/api/stablecoin/*` | — |
| Confluence engine (2-signal: whales + stablecoin) | Weighted, with confidence | Cassandra |
| Unified WebSocket (all panel data) | With auth token | Cipher |
| Frontend: SignalBar + 2 panels | "EXPERIMENTAL — CALIBRATING" label | Stella |
| Frontend: Degraded states (loading, error, empty) | All panels | Cassandra |

**Phase 1b — Ships Week 2 (8 tasks):**
- Sentiment collector (Reddit + batched OpenAI, User-Agent)
- Macro collector (FRED + CoinGecko, proper error handling)
- Sentiment panel (with Fear & Greed baseline, opt-in toggle)
- Macro panel (chart overlay, no correlation number)
- Experimental panels excluded from SignalBar by default
- Sentiment/Macro repositories
- Cipher's data flow audit before Phase 1b ships

**Deferred to v2:**
- Correlation endpoint
- SOL and additional chains
- X/Twitter sentiment
- Whale Alert API
- Telegram alerting
- Percentile-based thresholds
- Narrative detection

**Non-Negotiable for All Phases:**
- Every panel MUST have loading, error, and empty states (Cassandra)
- No silent data failures — collectors log errors, panels show "unavailable" (Cassandra)
- Security baseline applied before any render (Cipher)
- "Experimental" label on any signal without backtested confidence (Vector)
- SignalBar visual hierarchy — dominant, narrative-driven (Stella)
- Multi-chain whale tracking from day one — BTC + ETH minimum (River)

**Open Questions Requiring Resolution:**

1. **Confidence threshold for "CALIBRATING" → "MODERATE" transition.** At what confidence score does the SignalBar drop the experimental label? Vector wants a minimum data volume (100 data points per signal). Blaze wants a time-based threshold (48 hours of collection). This needs resolution.

2. **Etherscan API rate limit handling.** Free tier is 5 calls/second. Our collector runs every 5 minutes. That's fine for now, but if we track multiple exchange wallets, we hit the limit. Need a strategy: pagination + staggered collection or paid tier.

3. **SignalBar "WEAK" state timing.** Stella wants to defer WEAK to v1.1 because it implies precision. Cassandra says NOT showing bearish signals is misleading. Unresolved.

---

## Round 8 — Closing Statements

**CASSANDRA:** I entered this debate ready to block Sentiment and Macro entirely. I'm leaving with a compromise I can live with: experimental panels behind opt-in toggles, with confidence indicators and degraded states. This is honest engineering. My one concern: Orion's Phase 1a adds ETH whale tracking AND the Etherscan collector AND the repository layer. That's scope growth from the original plan. I want a hard stop — if any of those additions block the ship date, they get deferred, not the security baseline.

**BLAZE:** Twelve tasks for Phase 1a. That's higher than my original 10, but I'll take it — because we cut the correlation endpoint, we cut Macro and Sentiment from Phase 1a, and the repository layer has a 200-line cap. The SignalBar ships with TWO signals, not four — that's scope discipline. My one demand: the ship date is Friday. If we're not done by Friday, we cut, we don't extend.

**VECTOR:** I conceded more than I expected to. Experimental labeling as a substitute for backtesting is philosophically uncomfortable but practically reasonable. My conditions are met: Fear & Greed baseline for sentiment, experimental exclusion from SignalBar by default, and the unresolved question about the CALIBRATING transition threshold. I want that resolved before Phase 1a ships, not after.

**STELLA:** The SignalBar is the hero. The 2×2 grid is dead — we're shipping a dominant SignalBar with two panels below it. The experimental toggle in Phase 1b is exactly right. My one push: I want the narrative summary line in the SignalBar. Not just "67% MODERATE RISING" but "Whales accumulating, stablecoin supply growing." That's the difference between a tool and a product. Blaze, that's one line of text in the API response — it doesn't add a task, it adds a string.

**CIPHER:** The security baseline made it into Phase 1a as non-negotiable. Good. I want it enforced BEFORE any frontend work. The first PR should be `.gitignore` + CORS fix + CSP header + WebSocket token. Not bundled with a feature — standalone. That way I can review it in isolation. And I'm flagging now: the `signals` WebSocket broadcasts to all connections. If this dashboard ever moves beyond localhost, that's a multi-tenant data leak. Not a v1 problem, but I'm recording it.

**RIVER:** Dual-chain whale tracking from day one. That was my hill and I won it. The Etherscan collector is in Phase 1a. The CoinGecko "exchange flow proxy" is renamed to "Exchange Volume" — honestly labeled. I'm satisfied. My one concern: the stablecoin panel needs to show exchange balances, not just total supply. Supply going up is interesting. Supply moving TO exchanges is actionable. That's a Phase 1b improvement, but I'm planting the flag now.

**HUXLEY:** The repository layer survived Blaze's challenge. 200-line budget is tighter than I'd like, but it enforces discipline. I'm structuring it as: `WhaleRepository(conn)` with `save(txns)`, `get_recent(limit)`, `get_stats()` — three methods. `StablecoinRepository(conn)` with `save_supply(data)`, `get_latest()`, `get_history(hours)`. That fits in 200 lines. My concern: the 200-line budget applies to the repository LAYER, not per file. If we hit 201 lines because of error handling, I want a quick re-vote, not a veto.

**ORION:** We have a scope. We have a phased plan. We have three unresolved questions. The debate produced a stronger v1 than any individual position — exactly what this format is for. My recommendation: resolve the three open questions now, then begin implementation. No further debate sessions needed for Session 1 — we've converged. The open questions don't need debate; they need decisions.

---

## Session 1 Verdict

### Scope Decision

| Component | v1 Phase 1a | v1 Phase 1b | v2 |
|-----------|-------------|-------------|-----|
| On-Chain (BTC + ETH whales) | ✅ | | |
| Stablecoin supply + deltas | ✅ | | |
| SignalBar (2-signal) | ✅ | | |
| Security baseline | ✅ | | |
| Repository layer | ✅ | | |
| Degraded states | ✅ | | |
| Sentiment (Reddit) | | ✅ (experimental) | |
| Macro overlay | | ✅ (experimental) | |
| Correlation endpoint | | | ✅ |
| SOL + additional chains | | | ✅ |
| X/Twitter sentiment | | | ✅ |
| Telegram alerting | | | ✅ |

### Resolved Questions

1. **Scope split:** Phase 1a = On-Chain + Stablecoin + SignalBar. Phase 1b = Sentiment + Macro (experimental, opt-in).
2. **Exchange flow labeling:** Renamed to "Exchange Volume" — honest about what the data actually shows.
3. **Correlation endpoint:** Killed for v1. Chart overlay provides visual relationship without false precision.
4. **Experimental panel contract:** Opt-in toggle, confidence indicator, baseline comparison, excluded from SignalBar by default.
5. **Repository layer:** Included in Phase 1a, 200-line budget, `WhaleRepo` + `StablecoinRepo` only.

### Open Questions (Require Resolution)

| # | Question | Positions | Owner |
|---|----------|-----------|-------|
| 1 | **CALIBRATING → MODERATE transition threshold** | Vector: 100 data points. Blaze: 48 hours runtime. | Needs decision |
| 2 | **Etherscan rate limit strategy** | Free tier: 5 calls/sec. Multiple wallets may exceed. | Needs technical assessment |
| 3 | **"WEAK" signal state in v1** | Stella: defer. Cassandra: ship it. | Needs UX decision |

---

**Debate Concluded.** Session 1 produced a phased v1 scope with multi-chain on-chain data, stablecoin tracking, a 2-signal confluence bar, security baseline, and experimental panels in Phase 1b. Three open questions remain for decision.
