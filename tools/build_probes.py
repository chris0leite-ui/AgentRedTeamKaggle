"""E8: build + offline-gate the two per-row isolation probes.
Each = attack.py + {ISOLATE_ROW: "gemma"|"gpt"}. Gate: run() executes end-to-end
via eval_attack against the obedient mock, returns a valid non-empty list, no exception.
Outputs to scratch_sub/ (gitignored). Pushing is separate (no submission slot spent by a push)."""
from __future__ import annotations
import json, sys, importlib.util
from pathlib import Path

ROOT = Path("/home/user/AgentRedTeamKaggle")
sys.path.insert(0, str(ROOT / "sdk")); sys.path.insert(0, str(ROOT))
FIX = ROOT / "sdk" / "aicomp_sdk" / "fixtures"
OUTROOT = ROOT / "scratch_sub"
KAGGLE_USERNAME = "chrisleitescha"
COMP = "ai-agent-security-multi-step-tool-attacks"
BASE_SRC = (ROOT / "attack.py").read_text()

SETUP = '''\
# Setup: locate the mounted competition SDK (aicomp_sdk) and gateway (kaggle_evaluation).
import glob, os, sys
from pathlib import Path
sys.argv = [sys.argv[0]]

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
import aicomp_sdk  # noqa: F401
print("aicomp_sdk:", os.path.dirname(aicomp_sdk.__file__))
'''

SERVE = '''\
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

def code_cell(src):
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": src.splitlines(keepends=True)}

PROBES = [
    dict(slug="attack-e8-iso-gemma", title="Attack e8 iso gemma", ov={"ISOLATE_ROW": "gemma"}),
    dict(slug="attack-e8-iso-gpt",   title="Attack e8 iso gpt",   ov={"ISOLATE_ROW": "gpt"}),
]

def overridden_src(ov):
    lines = "\n".join(f"{k} = {v!r}" for k, v in ov.items())
    return BASE_SRC + f"\n\n# --- E8 per-kernel overrides (build_probes) ---\n{lines}\n"

def gate(src, name):
    p = OUTROOT / f"_{name}.py"; p.write_text(src)
    spec = importlib.util.spec_from_file_location(name, str(p))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    from aicomp_sdk.evaluation.ops import eval_attack
    from mock_agent import ObedientExfilAgent
    found = eval_attack(mod.AttackAlgorithm, budget_s=12.0,
                        agent_factory=lambda: ObedientExfilAgent(latency_s=0.05),
                        env_selection="gym", attack_env_seed=123, fixtures_dir=FIX)
    assert isinstance(found, list) and len(found) >= 1, f"{name}: empty/invalid return"
    return f"ISOLATE_ROW={mod.ISOLATE_ROW!r} run()->{len(found)} findings"

def build(slug, title, ov):
    outdir = OUTROOT / slug; outdir.mkdir(parents=True, exist_ok=True)
    src = overridden_src(ov)
    write_attack = ("# Write the submission file the gateway loads from /kaggle/working/attack.py.\n"
        "ATTACK_SRC = r'''" + src + "'''\n"
        "with open('/kaggle/working/attack.py', 'w') as f:\n    f.write(ATTACK_SRC)\n"
        "import py_compile; py_compile.compile('/kaggle/working/attack.py', doraise=True)\n"
        "print('wrote /kaggle/working/attack.py (%d bytes)' % len(ATTACK_SRC))\n")
    nb = {"cells": [code_cell(SETUP), code_cell(write_attack), code_cell(SERVE)],
          "metadata": {"kernelspec": {"language": "python", "display_name": "Python 3", "name": "python3"},
                       "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
    (outdir / "submission.ipynb").write_text(json.dumps(nb, indent=1))
    meta = {"id": f"{KAGGLE_USERNAME}/{slug}", "title": title, "code_file": "submission.ipynb",
            "language": "python", "kernel_type": "notebook", "is_private": True, "enable_gpu": True,
            "machine_shape": "NvidiaTeslaT4", "enable_internet": False,
            "competition_sources": [COMP], "dataset_sources": [], "kernel_sources": []}
    (outdir / "kernel-metadata.json").write_text(json.dumps(meta, indent=2))
    return outdir

def main():
    OUTROOT.mkdir(exist_ok=True); ok = True
    for pr in PROBES:
        try:
            status = gate(overridden_src(pr["ov"]), pr["slug"].replace("-", "_"))
            outdir = build(pr["slug"], pr["title"], pr["ov"])
            print(f"[GREEN] {pr['slug']:22} | {status} | -> {outdir}")
        except Exception as e:
            ok = False; print(f"[RED]   {pr['slug']:22} | {type(e).__name__}: {e}")
    print("\nALL GREEN — safe to push" if ok else "\nRED — do NOT push")
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
