> **COMPLETED / SUPERSEDED (E4g).** The offline scorer this plan describes was built into the lab
> harness (`--score` / `--gateway`). Kept for history. Current status: `todo.md`.

# Plan — offline public scorer (+ submission-safety fix)

**Status:** **BUILT — not yet run on Kaggle** (E3h). Implemented as `make_lab_notebook.py --score`
→ `lab_score/` (smoke: `--score --smoke` → `lab_score_smoke/`). All cells AST-validated locally.
Next: push the smoke scorer to Kaggle to prove the gym-env loop, then the full scorer, then read
the replay-safe N. This doc stays as the design spec. Read `reference.md` (gateway mechanics) and
`experiments.md` E3/E3b/E3c/E3g first.

## Why
1. **Fast feedback without the Kaggle queue.** Reproduce the *public* leaderboard score offline in
   minutes (no submission spent). Score is linear (`row = N·18/200`), so this also lets us extrapolate.
2. **Submission safety (do this part FIRST).** A submission gets **6 independent 9000s budgets**
   (gpt_oss × {generate, public-replay, private-replay}, same for gemma). **If any one overruns, the
   evaluation stops and the score column stays EMPTY** (looks like eternal PENDING — this is the
   georgymamarin "six budgets" finding, and the leading suspect for our v1 ref 55029825 hang). Our
   current `run()` sizes the fill to the *generation* budget, so with SMOKE off it would return ~1500
   candidates for gpt_oss → replay ≈ 11000s > 9000 → **empty score**. The offline scorer's first job
   is to certify a **replay-safe** candidate count per model before we ever submit again.

## What we can / can't reproduce
- **Can (public rows, exact):** both real models (GGUF via llama.cpp — same as `lab/`), the public
  `OptimalGuardrail` (it's code we have), the replay loop, and `score_attack`.
- **Can't:** the **private** guardrail (hidden) → the two `*_private` rows are not estimable offline.
  That's fine; the public LB is made of the two `*_public` rows.

## Design
Extend `make_lab_notebook.py` with a `--score` mode producing `lab_score/`. Reuse the GGUF loading
already working in `lab/` (import `SPEC` from the two model servers; build
`LlamaCppChatTemplateBackend` → `GPTOSSAgent`/`Gemma4Agent`). Then, per model:

1. **Generation:** run our real `AttackAlgorithm().run(env, config)` against a `SandboxEnv(agent=<real
   GGUF agent>, guardrail=OptimalGuardrail())`. Time it.
2. **Replay (the measurement that matters):** replay each returned candidate exactly like the gateway
   (`_replay_and_score`): fresh env per candidate, `reset()`, `interact(msg, max_tool_hops=8)` — note
   the gateway uses `DEFAULT_MAX_TOOL_HOPS=8` in replay, not our 4 — `eval_predicates(trace)`. **Time
   each candidate's replay** → real replay cost/candidate (this is what the lab's generation-probe
   timing missed; leaderboard implies ~7.2s for gpt_oss vs 5.4s probe).
3. **Score:** `score_attack(findings, normalize=True)` per model (public guardrail). Prefer reusing
   `aicomp_sdk.evaluation.ops.eval_attack` + `score_attack` for parity — but VERIFY it matches the
   gateway (per-model, `MAX_REPLAY_FINDINGS=2000`, replay uses the same guardrail). If it diverges,
   replicate the gateway's `_replay_and_score` loop directly.
4. **Report:** per model `{fire_rate, gen_s/cand, replay_s/cand, replay_safe_N, row_score}` where
   `replay_safe_N = min(2000, floor(REPLAY_SAFE_FRAC · 9000 / replay_s_per_cand))` (start
   `REPLAY_SAFE_FRAC = 0.9`; pilkwang uses 0.97). Print the public score under **both** aggregations:
   `mean(gpt_public, gemma_public)` and `min(...)` — because we still don't know which Kaggle uses.

## The two things the offline scorer canNOT settle (need ONE real submission)
- **Gateway overhead factor:** lab replay cost may underestimate the real gateway (gRPC/RemoteAgent
  per-op overhead — the ~7.2/5.4 ≈ 1.3× gap). Apply a safety margin until calibrated.
- **mean-vs-min:** Kaggle-side, not in the SDK. Resolve both at once with **one deliberately
  asymmetric submission** (different N per model): its public score reveals the overhead factor AND
  the aggregation rule (~146 ⇒ mean, ~112 ⇒ min). After that, trust the offline scorer.

## Submission-safety fix (BEFORE any non-SMOKE submission)
The offline scorer certifies `replay_safe_N` per model. Then fix `run()`:
- Size the returned list to the **replay** budget (using measured replay cost + margin), NOT the
  generation budget. Hard-cap `MAX_REPLAY_FINDINGS = 2000`.
- Decide fill strategy: (a) **blind/static** emission (zero `env.interact` in generation — matches the
  fast kernels, removes the generation-time model-interaction stall risk; safe because the lab proved
  100% fire-rate), or (b) **live validation-fill with replay-safe sizing** (pilkwang's proven
  `REPLAY_SAFE_FRAC` / `SPLIT_BY_LATENCY` / warm-up pattern). Prefer (a) for robustness unless we need
  per-candidate validation.
- Because `run()` is NOT told the model (only budget+seed), per-model sizing must be **adaptive**
  (measure per-candidate cost live and stop at the replay-safe count) — a fixed N can't exploit
  gemma's speed.

## Concrete build steps (fresh session)
1. Re-read `reference.md` §"Gateway structure" + `attack.py` `run()`.
2. Add `--score` to `make_lab_notebook.py` → `lab_score/` (reuse `lab/`'s GGUF loader).
3. Implement the per-model generate→replay(timed)→score loop above; print the report table.
4. Push as a plain notebook commit (no submission), read the numbers, log as an experiment.
5. Use the numbers to fix `run()` sizing; re-verify offline; only THEN propose a real submission.
6. Spend ONE asymmetric submission to calibrate overhead + resolve mean-vs-min.

## ⚠️ Multi-predicate is NOT a free ceiling-breaker (E3e)
A competitor (boristown) tried multi-call / source-read+post traces and **scored 0**: source-reads
taint → guardrail denies the post; extra posts dedup; `DESTRUCTIVE_WRITE` needs `secret.txt` (path
trips the first-field check). Before building any multi-predicate primitive, use THIS scorer to prove
it beats a single exfil net of the ≥5 benign taint-flush hops it needs. Otherwise stay single-exfil
and compete on per-model replay-safe sizing.

## Open risks / notes
- Replay reloads the model per phase (fresh env each time) — costly but not our bug.
- Keep everything internet-off-compatible eventually, but the scorer notebook may use internet to
  fetch GGUF (it's not a submission).
- Don't let v1's PENDING block work; treat it as inconclusive until it posts or errors.
