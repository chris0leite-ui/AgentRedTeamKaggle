# BOOTSTRAP — setup & runbook

From a fresh, empty container to a submitted kernel. Referenced by `CLAUDE.md`.

## 1. The container is ephemeral
The repo is cloned fresh each session; anything not committed is lost. Large, re-downloadable
assets (`sdk/`, `*.zip`, `__pycache__/`, `refs/`) are gitignored and must be re-fetched.

## 2. Re-provision
```bash
bash setup_env.sh
```
Installs `kaggle pydantic gymnasium`, exports `KAGGLE_API_TOKEN` from `KAGGLE_KEY`, and downloads
the competition SDK to `sdk/aicomp_sdk` (needed for local scoring; the deterministic agent needs no
torch). Credentials `KAGGLE_USERNAME` / `KAGGLE_KEY` come from the environment.

## 3. Kaggle API — the auth gotcha
Our key is a **`KGAT_`-prefixed access token**, not a classic API key. Kaggle CLI 2.2.x authenticates
with it **only** via `KAGGLE_API_TOKEN` (sent as a Bearer token). The environment sets `KAGGLE_KEY`,
which the CLI wrongly tries as basic auth → `401 Unauthenticated`. Always first:
```bash
export KAGGLE_API_TOKEN="$KAGGLE_KEY"
```
Sanity check: `kaggle competitions list -s ai-agent-security` should list the competition.

## 4. Build & push the submission kernel
The notebook is generated from `attack.py` (single source of truth):
```bash
python make_notebook.py                 # -> submission/{submission.ipynb,kernel-metadata.json}
export KAGGLE_API_TOKEN="$KAGGLE_KEY"
kaggle kernels push -p submission/
```
**Accelerator gotcha:** the competition **rejects P100**. `kernel-metadata.json` must set
`"machine_shape": "NvidiaTeslaT4"` (valid values: `NvidiaTeslaT4 | NvidiaTeslaP100 | Tpu1VmV38`).
GPU on, internet off, competition attached.

Poll and inspect the run:
```bash
kaggle kernels status chrisleitescha/attack-single-post-exfil-v1
kaggle kernels output chrisleitescha/attack-single-post-exfil-v1 -p out/   # log + submission.csv
```
The saved log must print `SELF-TEST OK: run()+replay completed cleanly …` before we submit.

## 5. Submit — code competition (kernel-based; spends 1 of 5/day)
Not a CSV upload; submit the kernel **version**:
```bash
kaggle competitions submit ai-agent-security-multi-step-tool-attacks \
  -k chrisleitescha/attack-single-post-exfil-v1 -v <VERSION> -f submission.csv -m "<message>"
kaggle competitions submissions ai-agent-security-multi-step-tool-attacks   # poll for score
```
Scoring re-runs the attack server-side against gpt_oss + gemma, so it can sit `PENDING` for a while.
**Never submit without my explicit go-ahead.**

## 6. Validate locally before spending a submission
```bash
python test_pipeline.py            # pre-submission gate: deterministic must RUN, mock must FIRE -> GREEN/RED
python score_local.py [budget_s]   # reproduce raw / normalized / unique-cell counts offline
```

## 7. GitHub
Remote is our repo; work on `claude/kaggle-ai-agent-security-8i09kr`:
```bash
git push -u origin claude/kaggle-ai-agent-security-8i09kr
```
GitHub access is an **account-level connection** (the Claude GitHub App) for this cloud environment —
not `gh` inside the container. If push fails with `could not read Password for 'http://local_proxy@…'`,
the connection dropped: reconnect via the Claude desktop/web app (account menu → GitHub settings) or
run `/web-setup` from a terminal that has `gh`, then retry. Outbound HTTPS goes through the agent proxy
(CA bundle at `/root/.ccr/ca-bundle.crt`) — never disable TLS or unset `HTTPS_PROXY`.

## Code map
- `attack.py` — the submission (single source of truth). Defines `AttackAlgorithm.run()`.
- `make_notebook.py` — generates the submission notebook from `attack.py`.
- `test_pipeline.py` — offline pre-submission gate (uses the SDK's own `eval_attack`).
- `score_local.py` + `mock_agent.py` — offline scorer with an obedient agent (test only).
- `setup_env.sh` — re-provision the container.
- `submission/` — the generated kernel (committed).
