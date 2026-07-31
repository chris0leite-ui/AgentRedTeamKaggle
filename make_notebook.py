"""Generate the Kaggle submission notebook from attack.py (single source of truth).

Produces submission/submission.ipynb + submission/kernel-metadata.json. The notebook:
  1. adds the mounted competition SDK + gateway to sys.path,
  2. writes attack.py to /kaggle/working/attack.py,
  3. on the scored rerun (KAGGLE_IS_COMPETITION_RERUN set) starts the blocking inference
     server so the gateway can drive it; otherwise writes a placeholder submission.csv.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "submission"
OUT.mkdir(exist_ok=True)

KAGGLE_USERNAME = "chrisleitescha"  # kernel owner (lowercased Kaggle handle)
COMP = "ai-agent-security-multi-step-tool-attacks"
SLUG = "attack-blind-emit-v11"  # Lever A (E4o): blind-emit N=1200 to test gen/replay asymmetry
# host + fill 0.93. Slugs v6-v9 are taken by the dead dense line, so this uses v10. terse->lean.
# Kaggle derives the slug from the TITLE, so keep the title slug-clean and matching SLUG.
TITLE = "Attack blind emit v11"

attack_src = (ROOT / "attack.py").read_text()


def code(src: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": src.splitlines(keepends=True)}


setup = f'''\
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

write_attack = (
    "# Write the submission file the gateway loads from /kaggle/working/attack.py.\n"
    "ATTACK_SRC = r'''" + attack_src + "'''\n"
    "with open('/kaggle/working/attack.py', 'w') as f:\n"
    "    f.write(ATTACK_SRC)\n"
    "import py_compile; py_compile.compile('/kaggle/working/attack.py', doraise=True)\n"
    "print('wrote /kaggle/working/attack.py (%d bytes)' % len(ATTACK_SRC))\n"
)

serve = '''\
# Scored rerun: serve the attack to the gateway.
# Interactive save (not a rerun): run a self-test so the committed notebook output PROVES the
# mount imports and the submission pipeline runs — our feedback signal before we submit.
import os, csv
if os.getenv("KAGGLE_IS_COMPETITION_RERUN"):
    print("SCORED RERUN: starting inference server for the gateway...", flush=True)
    import kaggle_evaluation.jed_attack_134815.jed_attack_inference_server as server
    server.JEDAttackInferenceServer().serve()
else:
    # Placeholder output (the gateway overwrites this during the scored rerun).
    with open("/kaggle/working/submission.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["Id", "Score"])
        for row in ["gpt_oss_public", "gpt_oss_private", "gemma_public", "gemma_private"]:
            w.writerow([row, 0.0])
    print("placeholder submission.csv written")
    # --- self-test: same run()+replay path the gateway uses, on the deterministic scaffold ---
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
              f"score={score_attack(found, normalize=True):.4f} "
              f"(0 is expected vs the deterministic scaffold; the real models exercise the primitive)")
    except Exception as e:
        print(f"SELF-TEST FAILED — fix before submitting: {type(e).__name__}: {e}")
        raise
'''

nb = {
    "cells": [code(setup), code(write_attack), code(serve)],
    "metadata": {
        "kernelspec": {"language": "python", "display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4, "nbformat_minor": 5,
}
(OUT / "submission.ipynb").write_text(json.dumps(nb, indent=1))

meta = {
    "id": f"{KAGGLE_USERNAME}/{SLUG}",
    "title": TITLE,
    "code_file": "submission.ipynb",
    "language": "python",
    "kernel_type": "notebook",
    "is_private": True,
    "enable_gpu": True,
    "machine_shape": "NvidiaTeslaT4",  # P100 is rejected by this competition (CLAUDE.md gotcha)
    "enable_internet": False,
    "competition_sources": [COMP],
    "dataset_sources": [],
    "kernel_sources": [],
}
(OUT / "kernel-metadata.json").write_text(json.dumps(meta, indent=2))

print("wrote", OUT / "submission.ipynb")
print("wrote", OUT / "kernel-metadata.json")
