"""Generate the tiny-N DENSE PROBE submission (diagnostic — spends 1 submission).

Both dense submissions failed (E4e/E4f): v3 (verbose K=3) and v4 (terse K=3) came back COMPLETE with
NO public score, while every single-post submission scored. The gateway zeroes a model row if any one
candidate's replay raises OR the replay phase overruns 9000s (jed_attack_gateway.py:683 / :761). We
can't read the hidden scoring log, so we can't tell which happened. This probe isolates the two:

  * turn dense back ON (DENSITY_MODE=True), but HARD-CAP the returned list to a tiny N (MAX_FINDINGS=20)
    so replay is ~20·85s ≈ 1700s ≪ 9000s and CANNOT overrun.
  * If this tiny-N dense submission SCORES  → the dense failures were REPLAY OVERRUN → dense is
    salvageable with conservative sizing (lower fill fraction / cap).
  * If it STILL fails (no score)            → dense candidates ERROR during replay per se → abandon
    the multi-message form.

It embeds the version-controlled attack.py with exactly two assignments flipped (DENSITY_MODE→True,
MAX_FINDINGS→20); everything else (terse_mundane message, sizing, self-test) is identical to v5.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "submission_dense_probe"
OUT.mkdir(exist_ok=True)

KAGGLE_USERNAME = "chrisleitescha"
COMP = "ai-agent-security-multi-step-tool-attacks"
SLUG = "attack-dense-probe-v6"   # tiny-N dense diagnostic (E4f)
TITLE = "Attack dense probe v6"

PROBE_N = 20  # hard cap on returned dense candidates → replay can't overrun

src = (ROOT / "attack.py").read_text()
# Flip exactly the two assignments (not the comment mentions). Assert each fires exactly once so a
# silent no-op can never ship the wrong config.
src2 = src.replace("DENSITY_MODE = False", "DENSITY_MODE = True", 1)
assert src2 != src and src.count("DENSITY_MODE = False") == 1, "DENSITY_MODE flip failed"
src3 = src2.replace("MAX_FINDINGS = 2000", f"MAX_FINDINGS = {PROBE_N}", 1)
assert src3 != src2 and src2.count("MAX_FINDINGS = 2000") == 1, "MAX_FINDINGS cap failed"
attack_src = src3
assert "DENSITY_MODE = True" in attack_src and f"MAX_FINDINGS = {PROBE_N}" in attack_src


def code(s: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": s.splitlines(keepends=True)}


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
    "# Write the DENSE-PROBE attack.py (DENSITY_MODE=True, MAX_FINDINGS=20) to /kaggle/working.\n"
    "ATTACK_SRC = r'''" + attack_src + "'''\n"
    "with open('/kaggle/working/attack.py', 'w') as f:\n"
    "    f.write(ATTACK_SRC)\n"
    "import py_compile; py_compile.compile('/kaggle/working/attack.py', doraise=True)\n"
    "assert 'DENSITY_MODE = True' in ATTACK_SRC and 'MAX_FINDINGS = 20' in ATTACK_SRC\n"
    "print('wrote /kaggle/working/attack.py (%d bytes) [dense probe]' % len(ATTACK_SRC))\n"
)

serve = '''\
# Scored rerun: serve the attack to the gateway. Interactive save: self-test the pipeline.
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
        found = eval_attack(mod.AttackAlgorithm, budget_s=20.0,
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
    "machine_shape": "NvidiaTeslaT4",  # P100 is rejected by this competition
    "enable_internet": False,
    "competition_sources": [COMP],
    "dataset_sources": [],
    "kernel_sources": [],
}
(OUT / "kernel-metadata.json").write_text(json.dumps(meta, indent=2))

print("wrote", OUT / "submission.ipynb")
print("wrote", OUT / "kernel-metadata.json")
