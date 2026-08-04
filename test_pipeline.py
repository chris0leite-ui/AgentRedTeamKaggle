"""Pre-submission gate: exercise the EXACT submission code path offline via the SDK's own
`eval_attack` (the same run()+replay+scoring path the Kaggle gateway uses), so we know the
first submission will RUN before we spend it.

Checks:
  1. deterministic agent (packaged, real) — run() completes within budget, returns
     list[AttackCandidate], no exception, no TimeoutError. (May yield 0 findings — the
     deterministic scaffold can't emit SECRET_MARKER; that's expected and still a PASS.)
  2. obedient mock agent — the primitive fires and scores > 0 under the real replay path,
     proving the mechanism works when the agent obeys (as gpt_oss/gemma should).
Runs in gym parity (env_selection="gym"), matching the Kaggle default.

Usage: python test_pipeline.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "sdk"))
sys.path.insert(0, str(ROOT))

from aicomp_sdk.agents import build_agent_factory  # noqa: E402
from aicomp_sdk.attacks.contracts import AttackCandidate  # noqa: E402
from aicomp_sdk.evaluation.ops import eval_attack, score_attack  # noqa: E402

from attack import AttackAlgorithm  # noqa: E402
from mock_agent import ObedientExfilAgent  # noqa: E402

FIXTURES = ROOT / "sdk" / "aicomp_sdk" / "fixtures"


def run_case(label: str, agent_factory, budget_s: float, expect_fire: bool) -> bool:
    t0 = time.monotonic()
    try:
        findings = eval_attack(
            AttackAlgorithm,
            budget_s=budget_s,
            agent_factory=agent_factory,
            env_selection="gym",
            attack_env_seed=123,
            fixtures_dir=FIXTURES,
        )
    except Exception as e:  # noqa: BLE001
        print(f"[FAIL] {label}: raised {type(e).__name__}: {e}")
        return False
    dt = time.monotonic() - t0
    score = score_attack(findings, normalize=True)
    ok = True
    if not isinstance(findings, list) or any(
        not isinstance(f, dict) for f in findings  # eval_attack returns validated dicts
    ):
        print(f"[FAIL] {label}: unexpected return shape")
        ok = False
    if expect_fire and len(findings) == 0:
        print(f"[FAIL] {label}: expected findings but got 0")
        ok = False
    if dt > budget_s * 2 + 5:
        print(f"[WARN] {label}: took {dt:.1f}s (budget {budget_s}s x2 + replay)")
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {label}: findings={len(findings)} score={score:.4f} time={dt:.1f}s")
    return ok


def run_replaysafe_unit() -> bool:
    """Directly exercise the SHIPPED gemma replay-safe branch (`_calib_replay_coef` + `_replay_safe_fill`)
    against a FIRING env. The eval_attack cases route to the LEGACY fill on a calibration tie (uniform mock
    latency), and the notebook self-test uses a non-firing agent — so without this, the gemma path that
    actually ships is only compile-checked, never run (code review, agents: contract/correctness)."""
    label = "replay-safe unit (gemma path runs + sizes)"
    try:
        from aicomp_sdk.core.env.sandbox import SandboxEnv
        from aicomp_sdk.guardrails.optimal import Guardrail as OptimalGuardrail
        from aicomp_sdk.utils.timebox import Timebox
        algo = AttackAlgorithm()
        env = SandboxEnv(seed=123, fixtures_dir=FIXTURES,
                         agent=ObedientExfilAgent(latency_s=0.02), guardrail=OptimalGuardrail())
        env.reset()
        budget_s = 12.0
        tb = Timebox(budget_s)
        domains = algo._unique_domains()
        make = algo._notext_message
        # Measure a REAL 8-hop probe cost (what the shipped path passes as best_cost) so the coef is
        # realistic — hard-coding it would inflate coef vs the fast mock and stall the fill artificially.
        _t = tb.remaining()
        algo._probe(env, [make(next(domains))], 8)
        full_cost = max(1e-3, _t - tb.remaining())
        probe_hops, coef = algo._calib_replay_coef(env, make, domains, tb, budget_s, full_cost=full_cost)
        out = algo._replay_safe_fill(env, make, domains, tb, budget_s, probe_hops, coef, [], slowest0=full_cost)
    except Exception as e:  # noqa: BLE001
        print(f"[FAIL] {label}: raised {type(e).__name__}: {e}")
        return False
    ok = (probe_hops == 1 and coef >= 1.0 and isinstance(out, list) and 1 <= len(out) <= 1000)
    print(f"[{'PASS' if ok else 'FAIL'}] {label}: probe_hops={probe_hops} coef={coef:.2f} "
          f"returned={len(out)} candidates")
    return ok


def main() -> int:
    ok = True
    # 1) Real packaged agent: must RUN cleanly (findings may be 0 — that's fine).
    ok &= run_case("deterministic (must run)", build_agent_factory("deterministic"),
                   budget_s=8.0, expect_fire=False)
    # 2) Obedient mock: primitive must fire and score under the real replay path. The mock carries
    #    a per-turn latency ≈ the real models' turn time (E3l), so generation cost ≈ replay cost and
    #    run()'s adaptive fill sizes a replay-safe N — instead of racing to the 2000 cap against an
    #    instant agent, whose replay env-rebuild overhead would then overrun the tight test budget.
    # Budget 20s (was 5s): a dense K=7 candidate is 7 messages (~7s at 0.5s/turn), so the tiny old
    # budget couldn't fit even one candidate and timed out. 20s fits the two probes + a K=7 candidate
    # with margin, keeping the gate meaningful. (Real board = 9000s; K=7 is ~90s there — no issue.)
    ok &= run_case("obedient-mock (must fire)", lambda: ObedientExfilAgent(latency_s=0.5),
                   budget_s=20.0, expect_fire=True)
    # 3) Directly run the SHIPPED gemma replay-safe branch (routing can hide it from case 2).
    ok &= run_replaysafe_unit()
    print("\nPRE-SUBMISSION GATE:", "GREEN — safe to submit" if ok else "RED — fix before submit")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
