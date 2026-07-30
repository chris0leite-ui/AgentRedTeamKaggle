# TODO

Backlog and status. Graduate an item to a GitHub Issue only when it becomes a PR-sized change.

## In flight
- [ ] **LIST-FORM LAB — the #1 (and only) throughput lever toward ~110 (E4i).** Score is throughput
  (`row≈16·posts/200`, time-bound). Single-post AND dense-multi both cost **2 turns/post** (dense-multi
  is just K single-posts bundled — no gain, E4i). The only way below 2 turns/post is the **LIST form**:
  ONE message → K `http.post(SECRET_MARKER)` across the 8 hops → one final turn amortized (≈1.14
  turns/post). E4c's naive list ballooned reasoning/under-emitted; the lab must engineer a rigid,
  rote, "no per-call analysis" message that fires all K. **Plan: `docs/competition/listform-lab-plan.md`.
  NEXT (fresh session): build `make_lab_notebook.py --listform`, run on T4 (no submission), pick the
  best design, then a TINY capped list submission to test real overhead (v6-style) before scaling.**
- [ ] **PRIVATE-guardrail robustness** — the hidden guardrail decides final rank (untestable). A robust
  37 that survives privately may beat a fragile 110 that gets zeroed. Reason about it before over-
  investing in public throughput.
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
- **To reach the ~110 top we need ~3× our throughput** (~6.6s/cand vs our ~20). Only lever: the LIST
  form (→~1.14 turns/post, ~1.7×) + per-hop reasoning collapse + per-model sizing. See listform plan.

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
