# TODO

Backlog and status. Graduate an item to a GitHub Issue only when it becomes a PR-sized change.

## In flight
- [ ] **Run the offline public scorer on Kaggle** (needs go-ahead). Built in E3h
  (`make_lab_notebook.py --score` → `lab_score/`; smoke `--score --smoke` → `lab_score_smoke/`).
  Push the **smoke** kernel first (gpt_oss only) to prove the gym loop, then the full one; read the
  per-model replay-safe N + projected public score (mean & min). Log as E3i.
- [x] ~~Diagnose the submission hang~~ **CLOSED by E3g:** v1 was never broken — it COMPLETED at 0.090
  after a multi-hour queue. The trivial static probe (E3f) also just sat in queue. Not our side.
- [x] **Build the offline public scorer** — done (E3h). Notebook ready, cells AST-validated; run
  pending go-ahead (moved to the run item above).
- [x] ~~FIX replay-safe sizing in `run()`~~ **DONE (v2):** E3l showed gen cost ≈ replay cost on the
  REAL models (5.44≈5.64 gpt_oss, 1.76≈1.80 gemma), so sizing the fill to `_BUDGET_FILL_FRAC=0.90`
  of the generation clock keeps replay safely inside its own 9000s budget (adaptive live sizing
  self-corrects for the overhead factor; env-rebuild delta is covered by the 10% cushion). Added
  untimed warm-up + a slowest-cost tail guard for gpt_oss CoT spikes. Gate GREEN.
- [x] ~~Resolve mean-vs-min~~ **RESOLVED (E3k): it's the MEAN** of the two public rows (pilkwang
  v3.1.2, source-verified). ⇒ per-model sizing pays off; **max gemma toward the 2000-cap** + get
  gpt_oss as high as its CoT cost allows. Asymmetric submission now only calibrates gateway overhead.
- [ ] **gpt_oss CoT is the slow-row ceiling (E3k):** competitors see ~24s/cand on gpt_oss (chain-of-
  thought) vs our lab's 4.66s. Test a CoT-suppressing "collapse/forged-analysis" prompt variant in
  `lab/`; measure whether our gpt_oss replay stays ~5s under realistic conditions.
- [ ] **v2 baseline — PIVOT to blind/static emission (E3i, needs go-ahead after scorer run):** emit N
  unique-domain exfil candidates with NO live probing (proven by trivial ref 55034976 → 0.450 = all 5
  static fired). Sidesteps the model-load truncation that capped v1 at 1 candidate. Size N to the
  REPLAY budget from the offline scorer's measured `replay_s/cand` (~1200 ⇒ ~112). Verify
  `test_pipeline.py` GREEN, submit (1/5 day).

## Next
- [ ] **Multi-predicate candidate (the actual differentiator):** the field is walled at ~112 on the
  single 18-raw primitive; the only way past is more raw *per finding* — one trace scoring
  exfil+write+untrusted (16+4+5…). **First verify feasibility:** does such a trace clear the guardrail
  without a deny? (Test in `lab/` before any submission.) (See `problem.md` §5, `experiments.md` E3b.)
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
