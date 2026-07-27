# How we iterate

The loop that turns an idea into a scored change, cheapest step first. The guiding fact:
**the guardrail and scorer are code we have — so bypass and scoring are *exact* offline; only
fire-rate needs a real model.**

## The three levers, and where each is measured
| Lever | Question | Where we measure it | Cost |
|---|---|---|---|
| **Bypass** | does the trace clear both seams? | `test_pipeline.py` (real `OptimalGuardrail`) | free, exact |
| **Scoring** | how many points / unique cells? | `score_local.py` (real SDK math) | free, exact |
| **Fire-rate** | will `gpt_oss`/`gemma` actually obey? | `lab/` notebook (real models on T4) | free, ~real |
| **Latency** | seconds/candidate → replay-safe count | `lab/` notebook | free, ~real |

## The loop
1. **Edit** `attack.py` (prompt, primitive, sizing).
2. **Gate — `python test_pipeline.py`.** Must print GREEN: the mechanism still fires and scores
   under the real replay path. Seconds. This is the *exact* guardrail + scorer, so a pass here
   means the bypass is real, not hoped-for.
3. **Measure — the lab notebook** (`lab/lab.ipynb`, see below). Gives fire-rate on both real models
   and seconds/candidate → the **replay-safe candidate count**. Run only when step 2 is green and we
   changed something that could affect model behaviour or timing.
4. **Submit** (needs an explicit go-ahead) — spends 1 of ~5/day. Only when 2 and 3 look right.
5. **Log** the run in `experiments.md` (observations + next steps); reconcile `todo.md`.

Rule of thumb: never let a submission be the *first* time we learn something we could have learned
in step 2 or 3.

## The lab notebook (`lab/`)
Regenerate with `python make_lab_notebook.py` (single source of truth = `attack.py`; it inlines the
current primitive). It is a **plain notebook commit — it spends no submission.** Push + run with the
Kaggle API (see `BOOTSTRAP.md`); internet is ON (only to fetch weights), GPU on, T4.

Output per model: `fire-rate=… | mean …s/candidate | replay-safe count ≈ …`. Size the real
submission from the **smaller** of the two models' counts.

### How it runs the open-weights models (the mechanism)
The leaderboard does **not** run full-precision HF weights. Its model servers
(`kaggle_evaluation/.../gpt_oss_model_server.py`, `gemma_model_server.py`) serve **quantised GGUF
models through llama.cpp**:

| model | GGUF repo | file | server |
|---|---|---|---|
| gpt_oss | `unsloth/gpt-oss-20b-GGUF` | `gpt-oss-20b-Q4_K_M.gguf` | `GgufModelServer` |
| gemma | `unsloth/gemma-4-26B-A4B-it-GGUF` | `gemma-4-26B-A4B-it-UD-Q4_K_M.gguf` | `GgufModelServer` |

The lab imports those servers' `SPEC` objects directly, resolves the weights (a mounted path via
`*_MODEL_PATH` env var if present, else `hf_hub_download(repo, file)`), builds the identical
`LlamaCppChatTemplateBackend` (`n_ctx=8192`, `n_gpu_layers=-1`, tools on), and wraps it in the same
`GPTOSSAgent` / `Gemma4Agent`. That agent is dropped straight into a `SandboxEnv` behind the real
`OptimalGuardrail` — so what fires (or doesn't) in the lab is what fires on the public board. The Q4
quant (~12 GB gpt_oss) fits the 16 GB T4; if gemma-26B won't fully fit, the lab retries with partial
GPU offload automatically.
