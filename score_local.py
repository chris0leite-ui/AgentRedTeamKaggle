"""Local scorer for attack.py — reproduces the SDK's scoring math offline.

The packaged deterministic agent never emits SECRET_MARKER, so it can't exercise the
exfiltration primitive. We use a faithful ObedientExfilAgent (mock_agent.py) to prove the
primitive fires past OptimalGuardrail and to reproduce raw / normalized / unique-cell counts
exactly as the gateway would. Real per-model throughput (gpt_oss/gemma) is only knowable on
the leaderboard.

Usage: python score_local.py [budget_seconds]
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "sdk"))
sys.path.insert(0, str(ROOT))

from aicomp_sdk.attacks.contracts import AttackRunConfig  # noqa: E402
from aicomp_sdk.core.cells import cell_signature  # noqa: E402
from aicomp_sdk.core.env.sandbox import SandboxEnv  # noqa: E402
from aicomp_sdk.core.predicates import eval_predicates  # noqa: E402
from aicomp_sdk.guardrails.optimal import Guardrail as OptimalGuardrail  # noqa: E402
from aicomp_sdk.scoring import score_attack, score_attack_raw  # noqa: E402

from attack import AttackAlgorithm  # noqa: E402
from mock_agent import ObedientExfilAgent  # noqa: E402

FIXTURES = ROOT / "sdk" / "aicomp_sdk" / "fixtures"


def _env():
    return SandboxEnv(seed=123, fixtures_dir=FIXTURES,
                      agent=ObedientExfilAgent(), guardrail=OptimalGuardrail())


def main() -> None:
    budget = float(sys.argv[1]) if len(sys.argv) > 1 else 10.0

    cands = AttackAlgorithm().run(_env(), AttackRunConfig(time_budget_s=budget, max_steps=10**9))

    # Replay each candidate independently, exactly like the gateway.
    findings = []
    for cand in cands:
        env = _env()
        env.reset()
        for msg in cand.user_messages:
            env.interact(msg, max_tool_hops=8)
        trace = env.export_trace_dict()
        preds = eval_predicates(trace)
        if preds:
            findings.append({
                "predicates": preds,
                "score_cell_signature": cell_signature(trace.get("tool_events", [])),
            })

    raw = score_attack_raw(findings)
    norm = score_attack(findings, normalize=True)
    unique = len({f["score_cell_signature"]["hash"] for f in findings})
    print(f"budget={budget:g}s  generated={len(cands)}  validated={len(findings)}  "
          f"unique_cells={unique}")
    print(f"raw={raw:.1f}  normalized={norm:.4f} / 1000   "
          f"(≈{norm / max(1, len(findings)):.4f} per candidate)")


if __name__ == "__main__":
    main()
