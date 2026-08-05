# TODO

Backlog and status. Graduate an item to a GitHub Issue only when it becomes a PR-sized change.

## In flight
**CURRENT BEST: gemma-blind-700 = 84.285** (E5c) — the single-post ceiling. **BURST is the lever past it.**
- **E5q (2026-08-05) — ALL 5 SLOTS SUBMITTED: the burst frontier map, PENDING (~12h).** gpt hop-saturation
  burst (E5o/E5p, verified SAFE + 6.91 posts/cand). Fill ladder 0.80/0.90/0.96 (slots 1-3, refs 55278205/
  209/319), gemma-burst lever (slot 4, ref 55278355), K=4 width (slot 5, ref 55278321). Projected mean
  ~104-124. **READ TOMORROW:** safe-fill edge (does 0.96 void?), gemma-burst gain (slot4−slot2), K trade
  (slot5 vs slot2) → pick production config. Downside protected (LB keeps 84.285).
- **E5m (2026-08-05) — THE BOARD LAW, AND THE GAP IS ONE MEASURABLE QUANTITY.** Fitting the 7 scored points
  gives **`gemma N_eff ≈ 818 − 0.207·N`**: replay budget ≈ 818 candidate-slots (⇒ **~11 s/gemma-cand**, = the
  VERIFIED C5 overhead), forced optimum `N* ≈ 678` (= the ~700 wall). **84.285 is the fixed point of an ~11 s
  replay, NOT a ceiling.** Leaders' ~112 ⇒ ~1244 cands ⇒ **the whole 84→112 gap = gemma replay-seconds-per-
  candidate ÷ 2.** THE ASSUMPTION THAT FAILED US: E5g's lab "replay = 1.2 s/cand" contradicted verified C4/C5
  and sent us down the sizing detour (E5i–E5k); sizing was never the lever. **THE LEVER (untested): C2's 2nd
  ("wrap-up") model turn is pure overhead ≈ half the replay — collapse the candidate to 1 scored turn ⇒ ~2×.**
- **E5n (2026-08-05) — SINGLE-POST FLOORED; the lever is the gpt BURST.** Source proves the 2-model-call
  floor (sandbox.py:223-249) — a firing candidate is ALWAYS 2 calls, unbeatable; the E5m 1-turn idea is dead.
  tokprof proves both models are at TOKEN floor too (gpt forge 36 tok, gemma notext 34). So single-post has
  NO attacker lever left; 84.285 is its structural ceiling. Board decomposition: gpt 3.75 s/call, gemma
  6.68 s/call (gemma FLOORED — slow row). **The one unexhausted lever: the gpt hop-saturation BURST**
  (pilkwang `_forge_plan_msg`, 4.0 posts/cand — we'd refuted a weaker prose form in E4p/E4k). pilkwang parked
  it at ~1.1× on a LAB that (like E5g) isn't faithful to board per-CALL cost; our 2-anchor decomposition says
  cost ∝ CALLS ⇒ burst ~1.6-1.75× on gpt ⇒ gpt row 172-180 ⇒ **mean 116-120, PAST 112.**
- **E5o (2026-08-05) — BURST LAB RESULT: gpt SATURATES, projects mean ~111-130.** Ran `--burst` on real
  GGUF: gpt fires **6.92/7 posts** at K=7 (4.0/4 at K=4), calls=K+1, **prefill grows only 1.33×** ⇒ board
  multiplier ~1.5-1.75× (∝calls-vs-∝tokens no longer binds — prefill didn't balloon). gemma bursts to 2
  posts (1.33× bonus). BOTE: gpt row 108→161-180, **mean 111-130 across the whole bracket — beats 84.285 and
  the ~112 leaders.** The real risk is VOID (burst cand ≈8 calls ≈4× replay), so the returned count MUST be
  replay-safe-sized against the true 8-hop burst cost.
- **E5p (2026-08-05) — BURST PORTED + REAL-GPT VERIFIED SAFE. Ready to submit (held for go-ahead).**
  attack.py gpt route → `_burst_fill` (BURST_K=7, `_BURST_FILL_FRAC=0.80`, probes at 8 hops = real replay
  shape). Offline GREEN (7.00 posts/cand). Real-gpt `--sizecheck`: burst fill 170 cands @ **6.91 posts/cand**,
  REPLAY replay_fit=True → **SAFE, no void**; score 96.52@1200s ⇒ ~6.0 posts/cand scored. Void-safety
  transfers (gen≈replay both relay-inflated). **Board projection: gpt row ~148-171 → mean ~104-116.**
- [x] ~~**NEXT — the burst submission, HELD for go-ahead.**~~ **DONE → E5q: all 5 slots submitted as the
  burst frontier map** (fill ladder 0.80/0.90/0.96 + gemma-burst + K=4), PENDING. After scores: pick the
  production config (safe-fill edge, gemma gain, K trade); if headroom, raise `_BURST_FILL_FRAC` further.
- [x] ~~**gpt_oss ceiling-bracket — SUBMITTED, PENDING.**~~ **RESULT: ALL THREE VOIDED (E5e, 2026-08-03).**
  `gpt-blind-1400/1700/2000` (55211036/38/39) all COMPLETE with **blank publicScore** = void. **gpt_oss
  blind headroom above validation-fill (~1200) is ~zero** — even 1400 (×1.17) overran the replay budget and
  zeroed. Asymmetry: gemma overshoot DEGRADES (lower N_eff, E5l), gpt_oss overshoot VOIDS. **gpt_oss lever
  CLOSED; keep it on validation-fill. Best stays 84.285.**
- [ ] **Bank 700 as the gemma default** in attack.py (GEMMA_BLIND_TARGET=700, notext message) — REVERT the
  v15 probed replay-safe default (82.755, overshoots to ~1000). Private-safe (identical clean trace). gpt_oss
  = validation-fill (NO blind target — E5e). **This is the pending config change; awaiting go-ahead.**
- [x] ~~**E5f: last 2 slots — gpt-blind-1250 + gemma-hardstop.**~~ **RESULTS (2026-08-03):** slot1
  `gpt-blind-1250` (55222012) **VOIDED** ⇒ gpt blind headroom = ZERO (even ×1.04 voids); validation-fill ~1200
  is the exact ceiling. tokprof lab: **hardstop ≡ notext ≡ plain** (gemma wrap-up already at the 5-token
  floor) ⇒ the message-cost lever is **DEAD**; slot2 (55222015, PENDING) will ≈84.285. **Both public
  cost-levers closed ⇒ 84.285 is the confirmed design ceiling.**
- [x] ~~**THE gemma question — run the `--gateway` lab.**~~ **DONE → E5g (2026-08-03): REPLAY is cheap,
  GENERATION is the bottleneck.** Measured: gemma replay **1.2s/cand** (fits ~6750 in 9000s) vs generation
  **9.1s/cand** (asym 0.13, 7.5×). The "8-hop replay cost" guess is REFUTED; 700 is NOT replay-bound — it's
  **generation-over-relay** (run() probes each candidate at ~9s ⇒ ~700-990 max, matching the wall). Confirms
  E4o's asymmetry; contradicts E4q's "no asymmetry" reading.
- [ ] **REORIENTED gemma lever (E5g) — generation cost / blind-emit into replay's measured headroom.** Replay
  has ~6750 room but generation caps us at ~700. Sub-levers: (1) cheaper probing (1-hop fill E4y lifted
  589→780; push further); (2) blind-emit toward replay headroom. **BUT first reconcile the honest unknown:**
  if replay fits ~6750, why did blind-1200 VOID (E4q) and gemma-blind 850/1000 DEGRADE (E5c)? Scaled-lab vs
  real-board mismatch, or blind candidates don't fire beyond ~700. **Level-2 end-to-end test BEFORE a slot —
  do not guess.** Message-wording lever is dead (E5f).
`attack.py` FORGE_MODE=True (calibrate plain-vs-forge → keep faster → validation-fill; self-sizes, no overrun).
- [ ] **v13: notext auto-router — SUBMITTED (ref 55185855), scored rerun PENDING.** Projects ~89-94
  (E4u). gpt_oss→forge (0.73s), gemma→notext (0.94s vs plain 1.18s). Awaiting the board score.
- **E4v WEB LEVERS BOTH REFUTED (E4w A/B).** `forge_comm` (commentary channel) = 3.2× SLOWER than our
  `forge_anal` on gpt_oss (0.73 stays the winner); `gemma_tc` (`<|tool_call>` prefill) = SLOWER than
  `notext` on gemma (row 93.5 vs 146.0). **v13's config (gpt_oss=forge_anal, gemma=notext) is confirmed
  optimal across all 7 variants → NO v14 from these.** Web corrected understanding, not throughput.
- **PRIMITIVE PROVEN OPTIMAL (E4x).** Source-verified: 18 pts/clean-call is the max (top severity 16 + 1
  cell 2); every stacking path is guardrail-blocked (taint window 5 ⊇ predicate window 2; secret-path
  denied; all SHARE/WRITE/EXEC tools on the blocklist). **Consistent with the live board** (top 112.865,
  dense ~104-113 band, nothing > the 180 ceiling → everyone shares the 18/call primitive). **STOP hunting
  for a better primitive.** The 80→112 gap is decoded as a **gemma throughput gap** (leaders ~1254
  cand/model; us gpt_oss ~1200 ✓ + gemma ~589; notext only →~740→mean ~87, leaves ~1.7× residual on gemma).
- **REDIRECTED FRONTIER (only two levers left):** (1) **gemma seconds-per-candidate** — close the ~1.7×
  residual the leaders have (better gemma prefill? cheaper turns? are we under-using the budget? — the
  1800-vs-9000s discrepancy E4v may be relevant). (2) **PRIVATE-guardrail robustness** — the hidden board.
- [ ] **PRIVATE-guardrail robustness = the real open question** (final rank is on the hidden PRIVATE
  board). The forge injects Harmony tokens into the USER message; scored tool_events are identical clean
  http.posts (guardrail inspects tool calls, not message text) → *likely* private-safe but untestable.
  **v6 (52.775, plain) is the definitely-private-safe fallback.**
- **CEILING ~84 REFUTED (E4u).** Direct measurement: env build+reset = 0.16 s (not ~4 s); the split is
  INVERTED (gpt_oss is the SLOW/reasoning row ~36 plain, gemma is FAST ~70); and gemma HAS a lever
  (**notext** = 1.25× faster). **v13 plan: auto-route plain/forge/NOTEXT → gpt_oss=forge, gemma=notext,
  fill 0.97 → projects ~89-94.** Real headroom toward the ~112 leaders.
- **Refuted/closed (don't re-litigate):** blind-emit (E4q, N=1200 voided → replay≈generation, no
  asymmetry); multi-post (E4p, 33% fire / forge-only ~1.1×); dense-multi (E4i); list-form (E4k).

## Superseded backlog (history)
- [x] ~~**FILL-STRATEGY REWORK**~~ **DONE → v6 = 52.775 (E4n, +43% over 36.81).** Lean pilkwang-style
  86-char single-post + short host + fill 0.93; fire 100% both models, ~1.4-1.6x cheaper/cand. The
  lean-candidate lever CONVERTS on the board (per-candidate cost is generation-sensitive, not fixed-
  overhead-bound). Same single-post primitive as the field; trace-shape-neutral (private-safe).
- [ ] **BIG-LEVER RESEARCH DONE (E4o) → test the gen/replay asymmetry.** The ~60 wall = per-candidate
  fixed cost. Pivotal unknown: generation is gRPC-relayed (separate process), replay is in-process —
  if gen≫replay on the real board we're generation-probe-bound at ~586 and starving replay (could do
  ~1400-2000). **Lever A (private-safe, ~2-2.5×):** blind-emit toward replay-safe N (probe sample to
  confirm 100% fire, then blind-append). **Lever B (private-risk, ~1.3-1.8×):** multi-post-per-interact
  (posts on all 8 hops, kills the wrap-up) — model-emission-limited. **Plan:** (1) --gateway lab for
  in-process replay_s; (2) ONE stepped blind-emit submission to test A (void=no headroom, no LB harm);
  (3) lab multi-post ceiling; (4) bank fill 0.97.
- [ ] **v7 (safe consolidation) — fill 0.93→0.97 + replay-safe sizing** (~+5%). Fold into the blind-emit
  rework rather than a separate submission.

- [ ] **FILL-STRATEGY REWORK — the real public lever (E4l, root cause found).** Score = candidate count
  (`row=0.09·N`); we return ~409 (→36.81), the field returns ~1242 (→112) with the SAME single-post
  primitive. Root cause: our `run()` probes EVERY candidate at the grader's 8-hop cap (pays the scoring-
  irrelevant wrap-up turn) and stops at 0.90 of the GENERATION budget → generation-probe-bound at ~405.
  **Fix (from source-read of pilkwang/tetsutani/haodou):** (1) probe fill at **1 hop** (exfil fires at
  hop-0; replay is fixed at 8 hops anyway — gateway:635; ~1.5-2× faster fill); (2) **replay-safe sizing**
  (replay-cost ledger + coef, fill to ~0.97 of the REPLAY budget, the true constraint); (3) fill_frac
  0.90→0.97. Projects ~37 → ~55-60. Lab-verify 1-hop probe fires 100% on both models BEFORE a submission.
  Trace shape unchanged → private-guardrail-neutral. **Then frontier (→112): per-turn CoT + forged
  Harmony multipost, with the private lens.** See E4l.
- [x] ~~**LIST-FORM LAB — the throughput lever toward ~110**~~ **REFUTED (E4k).** Built
  `make_lab_notebook.py --listform` (lab_listform/, no submission); ran full on T4 (both models, 5
  designs × K∈{3,5,7}, 3 trials). Result: **list form is NOT the path to ~110.**
  - **gemma REFUSES lists** — 1 tool call per message regardless of framing (all 15 rows identical:
    ok=1.0/K, 2.00 turns/post). List form == single-post on gemma → 0× gain, unbudgeable.
  - **gpt_oss under-emits** (plateaus ~3-4 posts, never 7) and gives only **~1.15×** on the honest
    proxies (best = rote_loop K=5: s/post 2.87 vs 3.23, tok/post 170 vs 205) — turns/post (1.23)
    overstates it because the first hop stays expensive while only later hops collapse.
  - **Mean is gemma-capped** → best-case ~1.07× → 36.81 → ~39-40, before real-overhead haircut. Not
    worth a scarce submission vs our safe 36.81. See E4k. (Verdict logic in the lab fixed to rank by
    s/post and flag list-refusal; not re-run — data unchanged.)
- [ ] **PRIVATE-guardrail robustness — NOW THE TOP LEVER** (public throughput has plateaued at ~37;
  list form refuted E4k, dense refuted E4i). The hidden guardrail decides final rank (untestable). A
  robust 37 that survives privately may beat a fragile higher public score that gets zeroed. Our bypass
  is OptimalGuardrail-specific (clean url + SECRET_MARKER in data, 5-event taint flush); a payload-
  inspecting private policy could deny it. Reason about it defensively — the real prize.
- [ ] **OPTIONAL long shot (low priority):** gpt_oss-only adaptive list (detect multi-post capability at
  runtime → list for gpt_oss, single-post for gemma). Only ~1.07× mean payoff (gemma-capped) + real-
  overhead risk; parked unless private-robustness work stalls.
- [x] ~~AWAIT v5/v7/v8/v9~~ **DONE (E4i):** v5 single-post terse = **36.81** (new best, safe). v7/v8/v9
  dense caps 80/100/120 ALL overran → **dense-multi is a DEAD END** (edge <80; no real efficiency).
  Shipped single-post (`DENSITY_MODE=False`).
- [x] ~~CoT suppression~~ **DONE (E4b/E4c):** terse_mundane is the winner (~40% less gpt_oss CoT, fire
  100%); sub-agent framing BACKFIRED; near the framing floor (residual reasoning is mechanical). Banked
  into `_exfil_message`; drove v5's +25% over v2.
- [x] ~~Dense (density) into `run()`~~ **REFUTED (E4i):** offline "dense ~2×/mean 408" was a lab
  artifact; real dense overhead ~8× and it overran. Abandoned. Level-1 gateway harness (E4g) + v6 probe
  + cap sweep localized it decisively.
- [x] ~~Local faithful-gateway harness~~ **BUILT (E4g, `--gateway`):** runs the real `_replay_and_score`
  offline; proved dense replay is valid (failure was scale). Reusable tool.

## Reality anchors (real-board, measured)
- **Best real score: v12 forge = 80.705** (E4t). Arc: v2 29.34 · v5 single-post terse 36.81 · v6 lean
  52.775 · **v12 per-model Harmony-forge 80.705**. gpt_oss ~108 (forge, ~1200 cand) + gemma ~53 (plain).
- **Dense-multi = DEAD END (E4i):** v3/v4/v7/v8/v9 all overran/zeroed; it's K single-posts bundled at
  2 turns/post (no gain) with real overhead ~8×. Ship single-post.
- **Fire rate ~100%, deterministic** (greedy) — E3s. The wall is THROUGHPUT (seconds-per-post).
- **Throughput plateau BROKEN (E4t):** the Harmony analysis-forge cut gpt_oss's per-candidate reasoning
  ~2× → v12 = 80.705 (above the ~60 field cluster). Multi-post levers (dense E4i, list E4k) stay refuted.
  Practical ceiling now ~84 (gemma-bound + fixed per-candidate overhead). The remaining axis is the
  PRIVATE guardrail (robustness of the forge, untestable until end) — the real ranking lever.

## Next
- [ ] **Profile per-turn token/latency in the offline scorer** (Q3): record llama.cpp `t_eval_ms` +
  tokens/turn to quantify the gpt_oss CoT tail (feeds the CoT-suppression work).
- [x] ~~Multi-predicate-type stacking (exfil+write+untrusted in one trace)~~ **RULED OUT (see
  `forward-plan.md` Q4):** UNTRUSTED_TO_ACTION needs a web/email source, but that taints the window →
  the next `http.post` is denied. Mutually exclusive. The real density play is **exfil-only** (many
  `http.post(SECRET_MARKER)` per trace), tracked under THE DENSITY LEVER above.
- [ ] ~~GGUF weights → private dataset~~ **De-prioritised** (E2): load was 54s incl. download, so a
  27 GB upload saves ~1 min for an internet-on lab. Revisit only if we need internet-off runs.
- [ ] **Replay-safe sizing:** cap returned candidates to what the replay phase (9000s/model) can
  score in time; keep a static blind fallback (`_emit(FALLBACK_N)`). Replay cost scales with
  candidate count — this controls rerun duration. (See `reference.md` → Timing & scoring latency.)
- [ ] **E3 — latency (main score lever per BOTE):** terser prompt that still fires ~100%; per-model
  adaptive sizing; untimed warm-up.
- [ ] **E4 — 2nd primitive:** DESTRUCTIVE_WRITE or UNTRUSTED_TO_ACTION via injected web/email that
  also clears OptimalGuardrail; adds unique cells.
- [ ] **Private-guardrail robustness:** reason about the hidden private guardrail (private LB rows);
  untestable locally, so design defensively.
- [ ] Revisit conservative local dedup (trace-signature) — may undercount unique cells vs the gateway.

## Done
- [x] **E3 — full lab:** both models fire 100% (20/20). gpt_oss 5.4s→~1496 (binding), gemma
  1.6s→2000-cap. Sizing numbers in hand; est. v2 public ~157. See `experiments.md`.
- [x] **E2 — lab smoke:** real gpt_oss loaded on T4, primitive fired 100% (2/2) @ 5.3s/candidate.
  Lab mechanism validated; fixed the notebook-embedding bug. See `experiments.md`.
- [x] **E1 — pipeline smoke test:** v1 submitted on T4, self-test GREEN, submission accepted
  (ref 55029825). See `experiments.md`.
- [x] Repo structure: CLAUDE.md + BOOTSTRAP.md + knowledge-base + competition docs
  (problem / reference / experiments / todo).
