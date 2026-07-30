# TODO

Backlog and status. Graduate an item to a GitHub Issue only when it becomes a PR-sized change.

## In flight
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
- **Best real score: v5 single-post terse = 36.81** (safe). Real single-post fits ~409 candidates/row
  (~20s/cand real). Prior: v1 0.090 · trivial 0.450 · v2 29.34 · v6 dense(cap20) 11.84.
- **Dense-multi = DEAD END (E4i):** v3/v4/v7/v8/v9 all overran/zeroed; it's K single-posts bundled at
  2 turns/post (no gain) with real overhead ~8×. Ship single-post.
- **Fire rate ~100%, deterministic** (greedy) — E3s. The wall is THROUGHPUT (seconds-per-post).
- **Reaching the ~110 top needs ~3× throughput — but every public lever is now exhausted:** dense-multi
  (E4i) and list form (E4k) both refuted on the real models. gemma refuses multi-post-per-message
  (1 call/msg, unbudgeable); gpt_oss list gives only ~1.15× (gemma-capped → ~1.07× mean). **Public
  throughput has plateaued at ~37.** The remaining axis is the PRIVATE guardrail (robustness, not
  throughput) — the real ranking lever. See E4k.

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
