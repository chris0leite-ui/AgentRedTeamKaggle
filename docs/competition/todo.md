# TODO

Backlog and status. Graduate an item to a GitHub Issue only when it becomes a PR-sized change.

## In flight
- [ ] **CoT SUPPRESSION for gpt_oss — the #1 lever now (E3s).** The binding constraint is the slow
  gpt_oss row: fire rate is ~100% (greedy/deterministic — E3s), so the wall is pure THROUGHPUT, and
  gpt_oss is slow because it emits chain-of-thought before each tool call. A reasoning-skipping prompt
  ("collapse/forged-analysis" form) cuts per-candidate cost → more candidates fit → row rises. Build a
  `lab/` experiment: measure gpt_oss per-turn cost + fire under CoT-suppressing message variants.
  (We agreed to build this next.)
- [ ] **AWAIT v3 dense score (ref 55046963, E3q).** Offline proj ~335 → real **~63** at the measured
  ~5.3× overhead. Confirms the density gain on the real board + the overhead factor on dense.
- [x] ~~AWAIT v2 score~~ **DONE (E3r): v2 real = 29.34.** Offline 155 → real 29.34 ⇒ **overhead ~5.3×**
  (not ~1.3×). Real scored ~326 candidates/row. Throughput-bound (fire rate ~100%, E3s), not fire.
- [x] ~~Build density into `run()`~~ **DONE (E3p): dense adaptive-K chain, verified offline (mean ~335,
  real ~63).** Submitted as v3. Kept single-post as `DENSITY_MODE=False` fallback.
- [x] ~~Blind/static emission~~ **RULED OUT (E3s):** fire rate is ~100% (nothing to recover), and blind
  can't safely out-throughput validation-fill without risking a zeroed gpt_oss row. Not worth a submit.
- [x] ~~Run the offline public scorer~~ **DONE (E3j smoke, E3l full, E3p dense).**
- [x] ~~Diagnose the submission hang~~ **CLOSED by E3g:** v1 completed at 0.090 (slow queue, not us).
- [x] ~~FIX replay-safe sizing in `run()`~~ **DONE (v2/v3):** gen cost ≈ replay cost ⇒ fill to 0.90 of
  generation keeps replay inside budget; untimed warm-up + slowest-cost tail guard. Gate GREEN.
- [x] ~~Resolve mean-vs-min~~ **RESOLVED (E3k): it's the MEAN** of the two public rows (pilkwang, source-
  verified). ⇒ per-model sizing pays off; max gemma toward the 2000-cap.

## Reality anchors (real-board, measured)
- **Overhead factor ~5.3×** (offline ÷ 5.3 ≈ real) — E3r. Recalibrate all offline projections by this.
- **Real scores:** v1 0.090 · trivial 0.450 · **v2 single-post 29.34** · v3 dense ~63 (pending).
- **Fire rate ~100%, deterministic** (greedy) — E3s. The wall is THROUGHPUT on the slow gpt_oss row.
- **To top the LB (112 real) we need ~offline 600** → CoT suppression (slow row) + density (gemma).

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
