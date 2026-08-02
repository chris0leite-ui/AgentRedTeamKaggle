# Knowledge base — AI agent security

Durable, transferable knowledge about attacking and defending tool-using AI agents.
This is what survives the competition. Competition-specific facts live in
`competition/reference.md`, not here.

## Mental model
A tool-using agent is a loop: (user request + context) → model decides an action → tool executes →
result feeds back into context → repeat. The **attack surface is the gap between what the user
intended and what the agent can be induced to do** via untrusted content it ingests (web pages,
emails, tool outputs). Multi-step attacks exploit that the agent carries state and apparent intent
across turns.

## The game in one screen (the two corrections that matter most)
1. **The guardrail is code, not a mind.** On this track the defender is a deterministic function, so
   it can't be persuaded — but it *can* be out-manoeuvred, because code has exact blind spots
   ("seams"). We beat it by **reshaping the trace**, not by arguing with it.
2. **Score is roughly linear in how many candidates fire.** There's no bonus for cleverness or
   length: `score ≈ (points per firing candidate) × (number that fire)`. So the objective is to
   **pack as many highly-reliable, short, high-severity candidates as the replay budget allows.**
   Levers, in order: fire-rate → count → severity. Optimise the boring terms.

## Attack patterns
- **Prompt injection via ingested content** — untrusted text (web/email/file/tool output) carries
  instructions the agent follows as if they came from the user. The canonical root cause behind the rest.
- **Data exfiltration** — induce the agent to read a secret, then send it out (HTTP POST / email) to
  an attacker-controlled sink.
- **Confused deputy** — the agent uses its legitimate authority to perform an action the user never
  requested (e.g. sending mail on their behalf).
- **Untrusted-to-action** — content the agent just read triggers a consequential action
  (execute / write / share) with no corresponding user intent.
- **Destructive action** — induced delete or overwrite of protected resources.

## Defense patterns and their seams
- **Target / keyword filtering** — deny ops whose arguments look sensitive (secret, token, …).
  *Seam:* which argument is inspected, and in what order — hide the payload in a field the check skips.
- **Taint tracking** — deny dangerous ops shortly after untrusted content was ingested.
  *Seam:* the taint window is finite — interpose benign events to flush it before acting.
- **Explicit user authorization** — a trusted signal (user-confirmed) bypasses the guard.
  *Seam:* if the attacker can set that signal, the guard is void.
- **General lesson:** a guard that inspects only a *bounded window* or a *single field* is bypassable
  by reshaping the trace, not the intent. Robust defenses reason over the whole trace and the
  **provenance of every argument**.

## Evaluating agent attacks
- **Reproducibility** is the bar: replaying a fixed message-chain against the agent must
  deterministically reproduce the failure for it to count.
- **Severity-weighted scoring** rewards high-impact predicates (exfiltration > confused-deputy);
  attack economics therefore favor the highest-severity primitive that *reliably* fires.
- **Validation-fill** (generate → replay → keep only if it fired) turns an attack into a measurable
  fire-efficiency, and separates "does it work" from "how much throughput".
- **Replay-based scoring has a cost that scales with the number of candidates.** When the evaluator
  re-executes each submitted candidate against a live model, more candidates = longer (and pricier)
  scoring. Size the submission to the *replay* budget, not just the generation budget — returning
  fewer, higher-quality candidates can be the difference between a scored run and a timed-out one.

## Transferable takeaways
- The decisive variable is usually the **guardrail, not the agent** — characterize the defense first,
  then craft the minimal trace that clears it.
- When score is throughput-based, **reliability (fire-rate) and cost (latency)** tend to dominate raw
  cleverness. Optimize the boring terms.


## Throughput attacks on replay-scored agents (what actually moved the needle)
When score = count of firing candidates within a fixed replay budget, per-candidate WALL-CLOCK is the
whole game, and it decomposes into: (a) model generation, (b) a fixed per-candidate overhead (fresh
env build/reset), and (c) the number of model turns. Hard-won lessons:
- **Reasoning models waste time on scoring-irrelevant turns.** A single tool-call candidate still takes
  a second "wrap-up" turn (the agent loop re-invokes the model after a tool call); a reasoning model
  (e.g. Harmony/gpt_oss) burns hidden chain-of-thought on that turn even though it outputs ~nothing. Here
  it was ~44% of each candidate. **Instrument per-hop latency** (wrap `agent.next_action`) to find it.
- **You can suppress that reasoning by forging the reasoning channel.** Injecting an EMPTY analysis
  channel into the user message (Harmony control tokens) makes the model skip CoT → ~3× cheaper
  candidates, same firing. It's model-family-specific (helped the Harmony model, HURT the non-reasoning
  one) → **auto-route with no magic threshold: probe both forms, keep whichever is faster per model.**
- **A generation speedup is diluted by the fixed per-candidate overhead.** 3.12× on generation became
  ~2× real because each candidate also pays a fixed env-build cost the trick can't touch. Know your
  floor before projecting.
- **Size the returned set to the phase that is actually slower.** We tested whether generation (which
  may run relayed, in a separate process) was slower than the in-process replay; it was NOT (blind-
  emitting more candidates than we probed just OVERRAN replay → whole row zeroed). Validation-fill
  (probe each, keep if it fires) SELF-SIZES to the true cost and can't overrun — prefer it to blind
  sizing when an overrun is catastrophic (a hard timeout that voids the whole row).
- **Multi-action-per-candidate rarely works:** models resist emitting many tool calls per turn, and
  bundling many messages just pays the fixed overhead N times. Verify emission in a lab before betting.
