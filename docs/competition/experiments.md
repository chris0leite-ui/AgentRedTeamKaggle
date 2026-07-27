# Experiments — log

Append-only; newest at top. Record **observations, not conclusions**, plus **recommended next
steps**. One entry per submission or notable local run.

---

## E1 — pipeline smoke test (single-post exfil v1)
- **Date:** 2026-07-27
- **Hypothesis:** the full pipeline (generate → push kernel → scored re-run → submit) runs
  end-to-end, before we invest in throughput.
- **Setup:** `attack.py` single-post exfil primitive with SMOKE_MODE caps (≤8 findings, ≤45s/model
  generation, ≤4 hops) and a crash-proof `run()`. Kernel v2 on **T4**, GPU on, internet off.
- **Observations:**
  - Local pre-submission gate (`test_pipeline.py`): deterministic agent runs clean, 0 findings
    (expected); obedient mock fires, ≈0.72 normalized over 8 candidates — matches the SDK scorer.
  - Kaggle run COMPLETE on T4 in ~30s; saved log printed
    `SELF-TEST OK: run()+replay completed cleanly | findings=0 score=0.0000`.
  - First push defaulted to **P100** → submit rejected with FAILED_PRECONDITION
    "cannot use P100 GPUs". Setting `machine_shape=NvidiaTeslaT4` fixed it.
  - Kaggle CLI auth failed as basic auth (401); works only via `KAGGLE_API_TOKEN` (Bearer) because
    the key is a `KGAT_` access token.
  - Submission accepted (**ref 55029825**); score **PENDING** (server-side re-run against
    gpt_oss + gemma).
- **Result:** pipeline validated end-to-end; real score pending.
- **Recommended next steps:**
  - Record the posted score here when it lands.
  - E2: turn SMOKE_MODE off, measure real per-model throughput/score.
  - T4 + `KAGGLE_API_TOKEN` gotchas captured in `BOOTSTRAP.md`.
