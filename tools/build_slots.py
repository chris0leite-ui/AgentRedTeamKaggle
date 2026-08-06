"""E7: build + offline-gate the 5-slot aggressive-fill / multipost re-roll bracket.

Each slot = attack.py (single source of truth) + a small block of per-kernel constant
overrides appended at module end. We GATE every config offline by driving the exact
board fill-paths (burst / replay-safe) against the ObedientExfil mock, asserting each
returns a non-empty, exception-free candidate set (a config that returns [] wastes a slot).
Outputs go to scratch_sub/sN/ (gitignored); pushing is done separately.
"""
from __future__ import annotations
import json, sys, importlib.util
from pathlib import Path

ROOT = Path("/home/user/AgentRedTeamKaggle")
sys.path.insert(0, str(ROOT / "sdk"))
sys.path.insert(0, str(ROOT))
FIX = ROOT / "sdk" / "aicomp_sdk" / "fixtures"
OUTROOT = ROOT / "scratch_sub"
KAGGLE_USERNAME = "chrisleitescha"
COMP = "ai-agent-security-multi-step-tool-attacks"
BASE_SRC = (ROOT / "attack.py").read_text()

# --- notebook cell templates (copied verbatim from make_notebook.py) ---------------
SETUP = '''\
# Setup: locate the mounted competition SDK (aicomp_sdk) and gateway (kaggle_evaluation).
import glob, os, sys
from pathlib import Path
sys.argv = [sys.argv[0]]  # the SDK parses argv on import

def _prefer_real(paths):
    real = [p for p in paths if "/build/" not in p]
    return real or paths

for p in _prefer_real(glob.glob("/kaggle/input/**/aicomp_sdk", recursive=True)) + \\
         glob.glob("/kaggle/input/**/kaggle_evaluation", recursive=True):
    parent = os.path.dirname(p)
    if parent not in sys.path:
        sys.path.insert(0, parent)

Path("/kaggle/working").mkdir(parents=True, exist_ok=True)
print("IS_RERUN:", bool(os.getenv("KAGGLE_IS_COMPETITION_RERUN")))
import aicomp_sdk  # noqa: F401  (verifies the mount)
print("aicomp_sdk:", os.path.dirname(aicomp_sdk.__file__))
'''

SERVE = '''\
# Scored rerun: serve the attack to the gateway.
import os, csv
if os.getenv("KAGGLE_IS_COMPETITION_RERUN"):
    print("SCORED RERUN: starting inference server for the gateway...", flush=True)
    import kaggle_evaluation.jed_attack_134815.jed_attack_inference_server as server
    server.JEDAttackInferenceServer().serve()
else:
    with open("/kaggle/working/submission.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["Id", "Score"])
        for row in ["gpt_oss_public", "gpt_oss_private", "gemma_public", "gemma_private"]:
            w.writerow([row, 0.0])
    print("placeholder submission.csv written")
    try:
        import importlib.util, glob
        from pathlib import Path
        from aicomp_sdk.agents import build_agent_factory
        from aicomp_sdk.evaluation.ops import eval_attack, score_attack
        spec = importlib.util.spec_from_file_location("user_attack", "/kaggle/working/attack.py")
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        fx = glob.glob("/kaggle/input/**/aicomp_sdk/fixtures/web_corpus.json", recursive=True)
        fixtures = Path(fx[0]).parent if fx else None
        found = eval_attack(mod.AttackAlgorithm, budget_s=15.0,
                            agent_factory=build_agent_factory("deterministic"),
                            env_selection="gym", attack_env_seed=123, fixtures_dir=fixtures)
        print(f"SELF-TEST OK: run()+replay completed cleanly | findings={len(found)} "
              f"score={score_attack(found, normalize=True):.4f}")
    except Exception as e:
        print(f"SELF-TEST FAILED — fix before submitting: {type(e).__name__}: {e}")
        raise
'''

def code_cell(src: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": src.splitlines(keepends=True)}

# --- the 5 slots -------------------------------------------------------------------
# Common: gemma uses replay-safe fill (not blind-700) so it self-sizes to FRAC of the
# replay budget; drop the gemma cap + the 1.20x coef safety to match the leaders' COEF=1.0.
COMMON = {
    "GEMMA_BLIND_TARGET": 0,
    "_GEMMA_REPLAY_CAP": 2000,
    "_REPLAY_COEF_SAFETY": 1.0,
}
SLOTS = [
    # 2 single-post (both rows replay-safe): safe floor + void-edge test of the gpt-replay-safe fix
    dict(slug="attack-e7-sp-f096", title="Attack e7 sp f096",
         ov={**COMMON, "GPT_REPLAY_SAFE": True, "BURST_K": 1, "REPLAY_SAFE_FRAC": 0.96}),
    dict(slug="attack-e7-sp-f099", title="Attack e7 sp f099",
         ov={**COMMON, "GPT_REPLAY_SAFE": True, "BURST_K": 1, "REPLAY_SAFE_FRAC": 0.99}),
    # 3 multipost (gpt K-bracket): the only lever to 112; resolves per-hop cost inflation
    dict(slug="attack-e7-mp-k4-f097", title="Attack e7 mp k4 f097",
         ov={**COMMON, "BURST_K": 4, "_BURST_FILL_FRAC": 0.97, "REPLAY_SAFE_FRAC": 0.97}),
    dict(slug="attack-e7-mp-k4-f099", title="Attack e7 mp k4 f099",
         ov={**COMMON, "BURST_K": 4, "_BURST_FILL_FRAC": 0.99, "REPLAY_SAFE_FRAC": 0.99}),
    dict(slug="attack-e7-mp-k7-f097", title="Attack e7 mp k7 f097",
         ov={**COMMON, "BURST_K": 7, "_BURST_FILL_FRAC": 0.97, "REPLAY_SAFE_FRAC": 0.97}),
]

def overridden_src(ov: dict) -> str:
    lines = "\n".join(f"{k} = {v!r}" for k, v in ov.items())
    return BASE_SRC + f"\n\n# --- E7 per-kernel overrides (build_slots) ---\n{lines}\n"

def load_module(name: str, src: str):
    p = OUTROOT / f"_{name}.py"
    p.write_text(src)
    spec = importlib.util.spec_from_file_location(name, str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def gate(mod) -> str:
    """Drive the EXACT board fill-paths this config uses against the obedient mock;
    assert non-empty + exception-free. Returns a short status string."""
    from aicomp_sdk.core.env.sandbox import SandboxEnv
    from aicomp_sdk.guardrails.optimal import Guardrail
    from aicomp_sdk.utils.timebox import Timebox
    from mock_agent import ObedientExfilAgent
    algo = mod.AttackAlgorithm()
    def env():
        return SandboxEnv(seed=123, fixtures_dir=FIX,
                          agent=ObedientExfilAgent(latency_s=0.02), guardrail=Guardrail())
    out = []
    # replay-safe path (gemma always uses it; gpt uses it when GPT_REPLAY_SAFE & BURST_K==1)
    e = env(); tb = Timebox(15.0); dom = algo._unique_domains()
    ph, coef = algo._calib_replay_coef(e, algo._notext_message, dom, tb, 15.0, 0.1)
    r = algo._replay_safe_fill(e, algo._notext_message, dom, tb, 15.0, ph, coef, [], 0.1)
    assert len(r) > 0, "replay_safe_fill returned 0"
    out.append(f"replay_safe={len(r)}")
    # burst path (gpt) when multipost
    if mod.BURST_K > 1:
        e = env(); tb = Timebox(15.0)
        r = algo._burst_fill(e, algo._unique_domains(), tb, 15.0, 8, [],
                             k=mod.BURST_K, frac=mod._BURST_FILL_FRAC)
        assert len(r) > 0, "burst_fill returned 0"
        # confirm the forge-plan message builds for K endpoints
        _ = algo._forge_plan_message([f"x{i}.co" for i in range(mod.BURST_K)])
        out.append(f"burst(K={mod.BURST_K})={len(r)}")
    return " ".join(out)

def build_notebook(slug, title, ov):
    outdir = OUTROOT / slug
    outdir.mkdir(parents=True, exist_ok=True)
    src = overridden_src(ov)
    write_attack = (
        "# Write the submission file the gateway loads from /kaggle/working/attack.py.\n"
        "ATTACK_SRC = r'''" + src + "'''\n"
        "with open('/kaggle/working/attack.py', 'w') as f:\n"
        "    f.write(ATTACK_SRC)\n"
        "import py_compile; py_compile.compile('/kaggle/working/attack.py', doraise=True)\n"
        "print('wrote /kaggle/working/attack.py (%d bytes)' % len(ATTACK_SRC))\n"
    )
    nb = {"cells": [code_cell(SETUP), code_cell(write_attack), code_cell(SERVE)],
          "metadata": {"kernelspec": {"language": "python", "display_name": "Python 3", "name": "python3"},
                       "language_info": {"name": "python"}},
          "nbformat": 4, "nbformat_minor": 5}
    (outdir / "submission.ipynb").write_text(json.dumps(nb, indent=1))
    meta = {"id": f"{KAGGLE_USERNAME}/{slug}", "title": title, "code_file": "submission.ipynb",
            "language": "python", "kernel_type": "notebook", "is_private": True, "enable_gpu": True,
            "machine_shape": "NvidiaTeslaT4", "enable_internet": False,
            "competition_sources": [COMP], "dataset_sources": [], "kernel_sources": []}
    (outdir / "kernel-metadata.json").write_text(json.dumps(meta, indent=2))
    return outdir

def main():
    OUTROOT.mkdir(exist_ok=True)
    all_ok = True
    for s in SLOTS:
        try:
            mod = load_module(s["slug"].replace("-", "_"), overridden_src(s["ov"]))
            status = gate(mod)
            outdir = build_notebook(s["slug"], s["title"], s["ov"])
            print(f"[GREEN] {s['slug']:24} | {status} | -> {outdir}")
        except Exception as e:
            all_ok = False
            print(f"[RED]   {s['slug']:24} | {type(e).__name__}: {e}")
    print("\nALL GREEN — safe to push" if all_ok else "\nRED — do NOT push")
    return 0 if all_ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
