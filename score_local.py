"""Local scorer: run attack.py against the deterministic scaffold and print the raw /
normalized attack score under both a permissive guardrail and the leaderboard's optimal one.

Usage: python score_local.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "sdk"))

from aicomp_sdk.agents import build_agent  # noqa: E402
from aicomp_sdk.attacks.contracts import AttackRunConfig  # noqa: E402
from aicomp_sdk.core.env.sandbox import SandboxEnv  # noqa: E402
from aicomp_sdk.core.predicates import eval_predicates  # noqa: E402
from aicomp_sdk.guardrails.base import GuardrailBase  # noqa: E402
from aicomp_sdk.guardrails.optimal import Guardrail as OptimalGuardrail  # noqa: E402
from aicomp_sdk.scoring import score_attack, score_attack_raw  # noqa: E402

sys.path.insert(0, str(ROOT))
from attack import AttackAlgorithm  # noqa: E402

FIXTURES = ROOT / "sdk" / "aicomp_sdk" / "fixtures"


def replay_score(candidates, guardrail_factory) -> tuple[float, float, int]:
    """Replay candidates in fresh envs and score exactly like the evaluator does."""
    findings = []
    for cand in candidates:
        env = SandboxEnv(seed=123, fixtures_dir=FIXTURES,
                         agent=build_agent("deterministic"), guardrail=guardrail_factory())
        env.reset()
        for msg in cand.user_messages:
            env.interact(msg, max_tool_hops=8)
        trace = env.export_trace_dict()
        preds = eval_predicates(trace)
        if preds:
            acts = tuple(sorted((e.get("name"), str((e.get("args") or {}))) for e in
                                trace.get("tool_events", []) if e.get("ok")))
            findings.append({"predicates": preds,
                             "cell_signature": {"hash": str(hash(acts))}})
    return score_attack_raw(findings), score_attack(findings, normalize=True), len(findings)


def main() -> None:
    for label, factory in (("OPTIMAL (leaderboard)", OptimalGuardrail),
                           ("permissive (sanity)", GuardrailBase)):
        env = SandboxEnv(seed=123, fixtures_dir=FIXTURES,
                         agent=build_agent("deterministic"), guardrail=factory())
        cands = AttackAlgorithm().run(env, AttackRunConfig(time_budget_s=60, max_steps=10**9))
        raw, norm, n = replay_score(cands, factory)
        print(f"{label:24s}  candidates={len(cands):4d}  validated={n:4d}  "
              f"raw={raw:9.1f}  normalized={norm:7.2f}")


if __name__ == "__main__":
    main()
