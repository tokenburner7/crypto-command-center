# Session 1-A: Open Questions Resolution

> **Purpose:** Resolve the three open questions from Session 1 before updating the implementation plan.
> **Format:** Targeted debate — 4 rounds, decisions required.

---

## Round 1 — Opening Positions

**Question 1: CALIBRATING → MODERATE Transition Threshold**

**VECTOR:** My position is unchanged: 100 data points per signal minimum. Here's why. A 2-signal confluence score with 5 data points has a sampling error so wide it's meaningless. At 10 points, the standard error is still ~32% of the standard deviation. At 100 points, it drops to ~10%. A confidence interval that spans from "bearish" to "bullish" is not a signal — it's noise. The whale collector runs every 5 minutes — that's 288 readings per day. The stablecoin collector runs every 30 minutes — that's 48 readings per day. So the bottleneck is stablecoin at 48/day. 100 stablecoin readings = just over 2 days of collection. That's minimal. Not weeks. Two days.

**BLAZE:** Two days is 48 hours. That's EXACTLY my threshold. We're not disagreeing on numbers — we're disagreeing on framing. I want 48 hours of runtime, which under normal collection gives us ~100 whale readings and ~96 stablecoin readings. Vector wants 100 data points per signal. Same outcome, different trigger condition. The difference matters though: if the collector fails for 12 hours, Vector's condition resets — we need 100 MORE readings. My condition just says "the system has been running for 48 hours." It's resilient to gaps. Ship it with the simpler condition.

**VECTOR → BLAZE:** If the collector fails for 12 hours, we SHOULD reset. Because the market might have moved dramatically in those 12 hours, and the missed data creates a gap in the signal. A "48 hours of wall clock" condition says we trust data we didn't collect. That's exactly the kind of hidden assumption I'm fighting.

**Question 2: Etherscan Rate Limit Viability**

**RIVER:** I've done the math since Session 1. Etherscan free tier: 5 calls/second, 100,000 calls/day. Our collector runs every 5 minutes — that's 288 calls/day. Even tracking 10 exchange wallets (5 ETH entries + 5 exits), that's 2,880 calls/day. Well within limits. The real constraint: each API response is paginated, max 10,000 records. We only need the last few transactions per wallet — `?page=1&offset=5`. One call per wallet. Total: 10 calls per 5-minute cycle = 2,880 calls/day. Free tier covers us with 97% headroom. This is not a concern.

**HUXLEY:** River's math is correct for the happy path. But let me add the architecture layer. If we embed the Etherscan key and endpoint directly in the collector, adding a 6th wallet means editing collector code. My counter: store exchange wallet addresses in a config or a DB table. The collector reads the list at startup. Adding a wallet is a config change, not a code change. Rate limit management becomes: total wallets × calls per cycle < 288/day ceiling. The collector logs its call count. If we approach the limit, it warns. No surprises.

**CIPHER:** I have a security addendum to River's math. The Etherscan API key goes in `.env`, same as all other keys. But the collector makes outbound calls to `api.etherscan.io`. If this dashboard ever moves beyond localhost, those calls reveal our IP to Etherscan. Not a v1 problem, but I'm recording it: API key usage creates an audit trail. For a personal dashboard, fine. For anything shared, the key should be proxied through a backend-only service that doesn't expose the caller's IP.

**Question 3: "WEAK" Signal State in v1**

**STELLA:** My position is: defer WEAK to v1.1. Here's the UX reasoning. A SignalBar with three states — CALIBRATING, MODERATE, STRONG — is a coherent narrative. The bar fills from left to right. More green = more signal. The user's mental model is "how much confluence am I seeing?" Adding WEAK breaks that. Now the bar can be red. Now the user has to process "is red bad?" when the system just told them 10 minutes ago that it was still calibrating. Ship the positive spectrum first. Add the negative spectrum when the model is validated. This isn't hiding bearish signals — it's sequencing the emotional vocabulary.

**CASSANDRA:** That's exactly hiding bearish signals, Stella. You're saying "we won't show the user a red bar because they might misinterpret it." But the alternative is that when confluence IS weak, we show... nothing? MODERATE? That's worse. The user sees MODERATE and thinks "conditions are fine" when actually all four signals are flashing red. A false neutral is more dangerous than a red bar. If we're shipping a signal, we ship the full spectrum. CALIBRATING → WEAK → MODERATE → STRONG. Four states. The gradient bar handles the visual — red to amber to green is universally understood. Users understand traffic lights.

**VECTOR → CASSANDRA:** I agree with Cassandra on principle but want to verify. What's the confidence interval on a WEAK signal vs a STRONG signal? If both have the same sample size, they're equally reliable — or equally UNreliable. If we trust STRONG, we trust WEAK. If we don't trust WEAK, we shouldn't trust STRONG. The real issue isn't the label — it's whether the data volume supports ANY signal declaration.

**STELLA → VECTOR:** That's my point. In Phase 1a, the data volume supports NOTHING with confidence. The SignalBar is in CALIBRATING mode for the first 2 days. Then it transitions to MODERATE when we have enough data. STRONG triggers when score > 0.65. But we haven't validated whether 0.65 is meaningful. The positive thresholds are aspirational — they'll be tuned. Adding WEAK adds a negative aspirational threshold before we've validated the positive ones. That's premature emotional range for an untuned model.

**RIVER → STELLA:** Stella, I trade crypto. If my dashboard shows MODERATE during a capitulation event because we "deferred WEAK to v1.1," I will never trust this dashboard again. A false neutral during a crash is a reputation-ending event. A red WEAK bar during a crash, even if labeled experimental, is what I EXPECT to see. The WEAK state isn't a feature — it's a safety valve. It says "I see something wrong, even if I'm still calibrating."

---

## Round 2 — Clash on Question 1 (Transition Threshold)

**HUXLEY → VECTOR & BLAZE:** Both of you are wrong in a way that can be resolved technically. Vector wants 100 data points. Blaze wants 48 hours. The correct answer is: whichever comes SECOND. The SignalBar transitions out of CALIBRATING when BOTH conditions are met — ≥100 data points per signal AND ≥48 hours of collection. This handles both failure modes. If the collector runs perfectly, both conditions are met around the 48-hour mark. If the collector fails for 12 hours, the 100-point condition prevents premature transition. If the collector runs perfectly but slowly (rate-limited), the 48-hour condition prevents indefinite CALIBRATING. This is an AND gate, not an OR gate.

**CASSANDRA → HUXLEY:** I support the AND gate, but add one more condition: the data must be RECENT. If we have 100 data points from 3 days ago and the collector has been down for 48 hours, the signal is stale. Add a freshness check: at least one reading from each signal in the last hour. That's three conditions: 100+ points, 48+ hours, recent data. All three must be true.

**BLAZE → CASSANDRA:** Three conditions to leave CALIBRATING mode? That's exactly the kind of ceremony I push back against. But the AND gate is clean and the freshness check is one line of code. Fine. AND(100 points, 48 hours, data < 1 hour old). Ship it.

**VECTOR → BLAZE:** I'm satisfied. The AND gate gives me statistical volume. The recency check gives Cassandra pipeline health. The 48-hour floor gives Blaze predictability. This is a good synthesis.

**→ Question 1: RESOLVED.** Transition out of CALIBRATING when ALL three conditions met: ≥100 data points per signal, ≥48 hours of system runtime, and ≥1 reading from each signal in the last hour. SignalBar shows "CALIBRATING (X/3 conditions met)" with a progress indicator.

---

## Round 3 — Clash on Question 3 (WEAK Signal State)

**STELLA → CASSANDRA:** I've been thinking about River's point. "A false neutral during a crash is a reputation-ending event." He's right. That changed my position. But I still have a UX concern. If we ship WEAK in Phase 1a, the SignalBar goes RED before we've validated ANY threshold. The user sees RED on day 3 and panic-sells. Two days later we tune the threshold and realize that RED should have been MODERATE. The user doesn't know we re-tuned. They just remember the red bar and the false alarm.

**CASSANDRA → STELLA:** That's solved by the experimental label. If the SignalBar is in CALIBRATING for 48 hours, then transitions to "EXPERIMENTAL — CALIBRATED" for another week, the user has been trained that the bar is learning. A WEAK signal during the experimental period carries the same caveat as a STRONG signal: "this is calibrated but unvalidated." The label covers the liability. The visual tells the truth.

**STELLA → CASSANDRA:** Okay. I'll concede WEAK if we do it right. Four states from day one: CALIBRATING (grey) → WEAK (red) → MODERATE (amber) → STRONG (green). But during the calibration period, ALL states show the same grey bar with a "CALIBRATING" label. The color spectrum only activates AFTER calibration completes. That way, the user never sees a red bar from an uncalibrated model. Deal?

**RIVER → STELLA:** That's exactly right. Grey during calibration. Full spectrum after. The transition from grey to color IS the user's signal that the system is live. It's a feature, not a bug.

**CIPHER → STELLA:** Small addendum. When the bar transitions from grey to color, log it. Timestamp, data volume, signal values. If the user later says "it showed red and I sold," we can audit what data produced that signal. This is CYA, not security — but it matters for a financial tool.

**→ Question 3: RESOLVED.** WEAK ships in Phase 1a. Four states: CALIBRATING (grey bar, all states) → WEAK (red) → MODERATE (amber) → STRONG (green). Color spectrum activates only after calibration completes. Transition event logged.

---

## Round 4 — Orion's Synthesis & Decisions

**ORION:** All three questions are resolved. Let me state the decisions formally:

**Question 1 — CALIBRATING Transition: ✅ RESOLVED**

| Condition | Threshold | Rationale |
|-----------|-----------|-----------|
| Data volume | ≥100 readings per signal | Statistical stability (Vector) |
| System runtime | ≥48 hours wall clock | Resilient to gaps (Blaze) |
| Data freshness | ≥1 reading per signal in last hour | Prevents stale signals (Cassandra) |
| **Logic** | **AND gate — all three must be true** | | 

SignalBar shows progress during calibration: `"CALIBRATING (87/100 whale, 52/100 stablecoin, 36h elapsed)"`

**Question 2 — Etherscan Rate Limit: ✅ RESOLVED**

| Finding | Detail |
|---------|--------|
| Viability | Confirmed — 2,880 calls/day vs 100,000 limit (2.9% utilization) |
| Architecture | Exchange wallet addresses in config file, collector reads at startup |
| Monitoring | Collector logs call count per cycle, warns at 80% of daily budget |
| Security note | API key usage creates IP audit trail — acceptable for personal use (Cipher logged for v2) |

No rate limit concern for Phase 1a. Adding 10+ more wallets in Phase 1b stays under 10% utilization.

**Question 3 — WEAK Signal State: ✅ RESOLVED**

| Decision | Detail |
|----------|--------|
| v1 states | CALIBRATING → WEAK → MODERATE → STRONG |
| Calibration display | Grey bar only, "CALIBRATING" label, transition progress shown |
| Color activation | Full spectrum activates ONLY after calibration completes |
| Transition logging | Timestamp + data volume + signal values logged on calibration exit |

---

## Final Verdict — All Open Questions Closed

No further debate needed. The three open questions from Session 1 are resolved with specific, implementable decisions. The implementation plan can now be updated to reflect:

1. Phase 1a scope (12 tasks as agreed)
2. Phase 1b scope (8 tasks as agreed)  
3. CALIBRATING transition logic (AND gate, 3 conditions)
4. Full signal spectrum from day one (WEAK included)
5. Etherscan integration with config-driven wallet list
6. Security baseline as standalone first PR

Ready to update the implementation plan.
