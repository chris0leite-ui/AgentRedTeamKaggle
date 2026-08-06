# CLAUDE.md — how we work

The operating manual. Kept deliberately short; details live in the files it points to.

## Read first, every session
1. **`BOOTSTRAP.md`** — re-provision the container, use the Kaggle API, submit, use our GitHub.
   Nothing works until the container is provisioned.
2. **`docs/competition/problem.md`** — what we're solving and where we are in the 7 steps.
3. **`docs/competition/todo.md`** — what's next.

## Hard rules
- **AXIOM: reaching the TOP of the leaderboard is achievable, and we take that as given.** Our current
  best is never "the ceiling" — only the best we have *so far*. The ~112 leaders are an existence proof
  that a higher score exists, so whenever the evidence says "we've exhausted every lever," the correct
  conclusion is **our model of the problem is incomplete**, NOT that the board has a wall. Never write or
  imply "this is the ceiling / public is exhausted / no lever left." A refuted lever is a fact; "therefore
  we're done" is a banned inference. Respond to a dead end by REFRAMING the problem (re-run the 7 steps on
  the gap itself) and by finding what the leaders know that we don't — not by settling.
- **Git.** Develop on `claude/kaggle-ai-agent-security-8i09kr`. Clear commit messages. Never push
  to another branch without permission.
- **No outward actions without an explicit go-ahead in that turn.** Do not submit to Kaggle, open a
  PR, or otherwise publish unless I say so.
- **Ask in plain text — never the Q&A / AskUserQuestion tool.** When you need input, ask directly
  in prose.
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
- **The problem framing is a draft, always.** `problem.md` is never final — we reframe as we learn,
  and we re-run the whole 7-step loop on sub-problems as they surface. Expect to revisit and rewrite
  it; that's the method working, not a failure.
- **Teach as we go.** Explain what I'm doing in simple, concise terms so the user learns from it.

## Where things live
- `docs/competition/how-it-works.md` — **plain-English explainer with diagrams (START HERE).**
- `docs/competition/assumptions.md` — every assumption we rely on, with confidence + how we'd know it's wrong.
- `docs/glossary.md` — our shared vocabulary (ubiquitous language). Fix fuzzy terms here.
- `docs/knowledge-base.md` — transferable AI-agent-security knowledge (survives the competition).
- `docs/competition/agent-model.md` — visual model (agent loop, guardrail seams, our v12 forge program, throughput).
- `docs/competition/reference.md` — competition-specific facts (contract, scoring, guardrail).
- `docs/competition/problem.md` — 7-step problem framing, BOTE calcs, option comparisons.
- `docs/competition/forward-plan.md` — constraint analysis, profiling plan, the exfil-density lever
  (source-verified) and the model-emission experiments that gate it.
- `docs/competition/iteration.md` — the edit→gate→measure→submit loop; the `lab/` notebook.
- `docs/competition/plan-offline-scorer.md` — planned offline public scorer + submission-safety fix.
- `docs/competition/private-guardrail-plan.md` — **next-session focus:** private-board strategy
  (hedge-not-adapt, why runtime adaptation is impossible), the extraction-route map (with/without
  SECRET_MARKER), and the spec for the harness-interaction / guardrail-simulation tool.
- `docs/competition/experiments.md` — dated, append-only log.
- `docs/competition/todo.md` — backlog / in-flight / done.
