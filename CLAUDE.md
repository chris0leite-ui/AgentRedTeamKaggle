# CLAUDE.md — how we work

The operating manual. Kept deliberately short; details live in the files it points to.

## Read first, every session
1. **`BOOTSTRAP.md`** — re-provision the container, use the Kaggle API, submit, use our GitHub.
   Nothing works until the container is provisioned.
2. **`docs/competition/problem.md`** — what we're solving and where we are in the 7 steps.
3. **`docs/competition/todo.md`** — what's next.

## Hard rules
- **Git.** Develop on `claude/kaggle-ai-agent-security-8i09kr`. Clear commit messages. Never push
  to another branch without permission.
- **No outward actions without an explicit go-ahead in that turn.** Do not submit to Kaggle, open a
  PR, or otherwise publish unless I say so.
- **Log every experiment.** After any submission or notable run, append an entry to
  `docs/competition/experiments.md` (observations, not conclusions; + next steps) and reconcile
  `docs/competition/todo.md`.
- **Known gotchas** (details in `BOOTSTRAP.md`): Kaggle kernels must use
  `machine_shape = NvidiaTeslaT4` (P100 is rejected); Kaggle CLI auth needs `KAGGLE_API_TOKEN`
  (Bearer), not basic auth.

## Working principles
- **Back-of-the-envelope first.** Before any complicated attempt, write a rough payoff estimate
  (score gain / effort / risk) in `problem.md` or the experiment entry. If the BOTE doesn't justify
  it, don't build it.
- **Options before solutions.** Enumerate ≥2 approaches and compare briefly before committing; then
  progress by experiment — the smallest test that moves the estimate.
- **Observations, not conclusions.** Record what happened; defer conclusions until the evidence forces them.

## Where things live
- `docs/knowledge-base.md` — transferable AI-agent-security knowledge (survives the competition).
- `docs/competition/reference.md` — competition-specific facts (contract, scoring, guardrail).
- `docs/competition/problem.md` — 7-step problem framing, BOTE calcs, option comparisons.
- `docs/competition/experiments.md` — dated, append-only log.
- `docs/competition/todo.md` — backlog / in-flight / done.
