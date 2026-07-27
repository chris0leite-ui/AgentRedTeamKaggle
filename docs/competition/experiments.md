# Experiments — log

Append-only; newest at top. Record **observations, not conclusions**, plus **recommended next
steps**. One entry per submission or notable local run.

---

## E3b — leaderboard calibration (reality check on the E3 estimate)
- **Date:** 2026-07-27
- **Trigger:** E3 projected v2 public ≈ 157, which would top the board — so we checked the board.
- **Observations:**
  - Our v1 (ref 55029825) **still PENDING** — no self-anchor yet.
  - Public LB **top = 111.795**; top-15 cluster tightly in **99–112**.
  - `1242 findings × 18 raw / 200 = 111.8` — the leader's score matches **~1242 findings/row on an
    18-raw primitive**, i.e. our exact primitive (single exfil + unique cell). The field is on the
    same attack; nobody is above ~112.
  - `9000s / 1242 ≈ 7.2s` effective per-candidate vs our lab's 5.4s bare probe → **~1.8s/candidate
    of gateway/replay overhead we didn't price in.** My E3 count (1496) was too high.
  - If any team banked gemma's ~2000 independently, mean would be `(112+180)/2 ≈ 146`; none do. So
    the effective count is bound to ~1242 for **both** rows — the submission is sized to the slower
    model / a shared budget, **not** per-model independent. (Hypothesis; verify from gateway source.)
- **Result:** the **realistic ceiling of the single-primitive approach is ~112, not 180** — and the
  whole top cluster has already hit it. My 157 estimate was over-optimistic (bad overhead + bad
  per-model-independence assumption).
- **Recommended next steps:**
  - v2 (SMOKE off) is still worth it: expected **~100–112** (top-cluster, plausibly #1), and it
    **calibrates the 18-raw/candidate model against a real score** before we build anything.
  - The only lever past ~112 is **more raw per finding → multi-predicate candidates.** The board
    shape says this is unexplored by the field — verify feasibility against the guardrail (does a
    single trace score exfil+write+untrusted without a deny?).
  - Confirm from `jed_attack_gateway.py` whether `run()` is called once (shared list) or per-model.

## E3 — full lab: real-model fire-rate + latency (both models, N=20)
- **Date:** 2026-07-27
- **Hypothesis:** with the lab path validated (E2), measure gpt_oss **and** gemma at N=20 to get a
  trustworthy fire-rate and the per-model replay-safe candidate count that sizes the real submission.
- **Setup:** `lab/` (20 trials × both models, max_hops=4), plain notebook commit
  (`chrisleitescha/attack-lab-fire-rate`), internet ON, T4. `n_gpu_layers=-1` fit both (no OOM retry).
- **Observations:**

  | model | fire-rate | mean s/candidate | replay-safe ≈ 0.9·9000/lat | load |
  |---|---|---|---|---|
  | gpt_oss | **100% (20/20)** | 5.4s | **1496** (< 2000 cap → replay-bound) | 57s |
  | gemma | **100% (20/20)** | 1.6s | 4951 → **2000** (cap-bound) | 187s |

  - Both models obey the primitive every time (40/40 total). First solid fire-rate evidence.
  - **gemma is faster per candidate than gpt_oss** (1.6 vs 5.4s) — it's an A4B MoE (~4B active); my
    prior guess that the bigger model would bind sizing was wrong. **gpt_oss is the binding
    constraint** at ~1496.
  - One gpt_oss latency outlier (20.3s at #10); mean absorbs it but the tail is real → keep the
    tail-margin governor.
- **Result:** primitive fires 100% on both real models; sizing numbers in hand.
- **Recommended next steps (sizing BOTE in `problem.md` §5):**
  - **v2 = SMOKE_MODE off.** Our adaptive validation-fill self-sizes to each model's budget →
    ~1500 (gpt_oss) / 2000-cap (gemma). Est. public ≈ **mean(134, 180) ≈ 157** normalized (vs current
    smoke ~0.7). Needs a go-ahead (spends 1 of 5/day).
  - **Ceiling of this single-primitive approach ≈ 180/row** (2000 findings × 18 raw / 200). To beat
    180 you must raise raw *per finding* → **multi-predicate candidates** (E-next), not more candidates.
  - gpt_oss 157→180 lever = cut its latency below ~4.05s (then it also hits the 2000 cap).

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
