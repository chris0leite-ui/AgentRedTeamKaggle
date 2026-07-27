# TODO

Backlog and status. Graduate an item to a GitHub Issue only when it becomes a PR-sized change.

## In flight
- [ ] **v2 baseline — SMOKE_MODE off (needs go-ahead):** adaptive fill self-sizes to ~1496 (gpt_oss)
  / 2000-cap (gemma). Est. public ≈ **157** normalized. Verify `test_pipeline.py` GREEN, then submit
  (spends 1 of 5/day). This is the measured baseline to beat. (See `problem.md` §5, `experiments.md` E3.)

## Next
- [ ] **Beat the baseline** (after v2 scores): either (1) cut gpt_oss latency 5.4→<4.05s so both rows
  hit the 2000 cap (~180), or (2) a **multi-predicate candidate** (exfil+write+untrusted in one trace)
  to raise raw/finding past the 180 ceiling. (See `problem.md` §5.)
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
