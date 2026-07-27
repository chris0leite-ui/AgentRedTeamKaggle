# Experiments — log

Append-only; newest at top. Record **observations, not conclusions**, plus **recommended next
steps**. One entry per submission or notable local run.

---

## E2 — lab smoke: real-model fire-rate + latency (gpt_oss only)
- **Date:** 2026-07-27
- **Hypothesis:** the `lab/` path can load the *real* leaderboard model (GGUF via llama.cpp) on a T4
  and measure our primitive's fire-rate + latency — offline-measurable throughput without spending a
  submission.
- **Setup:** `lab_smoke/` (gpt_oss only, N_TRIALS=2, max_hops=4), plain notebook commit
  (`chrisleitescha/attack-lab-smoke`), internet ON (weights fetch), GPU T4. First push ERRORED in 9s.
- **Observations:**
  - **Bug found & fixed:** the generator embedded `attack.py` in a raw *triple-double-quoted* string;
    `attack.py`'s own `"""` docstring closed it early → `SyntaxError`. Fixed by embedding via
    triple-*single*-quote concatenation (as `make_notebook.py` does) + an AST-compile check on every
    cell before push. Same latent bug existed in the full `lab/` — fixed there too.
  - Kaggle derives the kernel **slug from the title**, not the metadata `id`; gave both labs
    slug-clean titles so the URL is predictable.
  - Re-run COMPLETE in ~3 min. `llama-cpp-python` installed from the **cu124** prebuilt wheel;
    `llama_cpp 0.3.34`. `gpt-oss-20b-Q4_K_M.gguf` loaded with `n_gpu_layers=-1` on the T4 in **54s**
    (download + load together — HF path is fast).
  - **fire-rate = 100% (2/2)** on the real gpt_oss; **mean 5.3s/candidate**; implied replay-safe
    count ≈ **1523** (0.9·9000/5.3), which is under the 2000-findings cap.
- **Result:** the lab mechanism works end-to-end on the real model; our primitive fires on gpt_oss
  (first evidence beyond the obedient mock).
- **Recommended next steps:**
  - Run the **full** `lab/` (20 trials × both models) — need gemma's fire-rate + latency; gemma is
    bigger, so its replay-safe count (and any fire-rate gap) will govern sizing. N=2 is too small to
    trust 100% yet.
  - **De-prioritise the GGUF-weights dataset:** load was 54s, so mounting weights saves ~1 min, not
    ~10 — BOTE no longer justifies a 27 GB upload for an internet-on lab.
  - If gpt_oss ends up latency-bound below the cap, the lever is a terser prompt / fewer hops.

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

### Follow-up (same day) — score still PENDING at ~2h; investigated
- **Observations:**
  - Pulled 7 real competitor kernels + the official starter via API, and read the gateway/SDK
    source. Our notebook's rerun path is functionally equivalent to the official starter
    (`serve()` self-gates blocking on `KAGGLE_IS_COMPETITION_RERUN`); our `run()` matches the
    official live-probe idiom and is hard-capped at 45s in SMOKE_MODE.
  - Verified the gateway budget: `DEFAULT_BUDGET_S = 9000s`, run **twice per model** (generation +
    replay), ×2 models — so multi-hour reruns are expected. Startup limit is 900s (a dead server
    errors at 15 min, does not hang). No error observed → the server started fine.
  - A competitor reported **restricting the candidate count to reduce rerun duration** — confirms
    replay cost scales with the number of returned candidates ("replay-safe sizing").
  - No evidence our submission is broken; the long PENDING is most consistent with queue + the heavy
    two-phase per-model budget. The colleague's ~20-min turnaround is the low-queue outlier.
- **Recommended next steps:**
  - Keep waiting on ref 55029825; treat an eventual ERROR (not a slow PENDING) as the signal to change.
  - For E2, size candidates to the replay budget; keep a static blind fallback (`_emit(FALLBACK_N)`).
