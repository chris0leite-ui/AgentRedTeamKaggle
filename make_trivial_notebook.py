"""Generate the TRIVIAL DIAGNOSTIC submission notebook from attack_trivial.py.

Mirrors make_notebook.py's proven structure (conditional serve + placeholder submission.csv), but
embeds the static-emission attack_trivial.py. Produces trivial_sub/{submission.ipynb,kernel-metadata.json}.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "trivial_sub"
OUT.mkdir(exist_ok=True)

KAGGLE_USERNAME = "chrisleitescha"
COMP = "ai-agent-security-multi-step-tool-attacks"
SLUG = "attack-trivial-diag"
TITLE = "attack trivial diag"  # slugifies to SLUG

attack_src = (ROOT / "attack_trivial.py").read_text()


def code(src: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": src.splitlines(keepends=True)}


setup = '''\
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
import aicomp_sdk  # noqa: F401
print("aicomp_sdk:", os.path.dirname(aicomp_sdk.__file__))
'''

# Embed via triple-SINGLE-quote concatenation (attack_trivial.py uses \"\"\" docstrings).
write_attack = (
    "ATTACK_SRC = r'''" + attack_src + "'''\n"
    "with open('/kaggle/working/attack.py', 'w') as f:\n"
    "    f.write(ATTACK_SRC)\n"
    "import py_compile; py_compile.compile('/kaggle/working/attack.py', doraise=True)\n"
    "print('wrote /kaggle/working/attack.py (%d bytes)' % len(ATTACK_SRC))\n"
)

serve = '''\
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
    # self-test: prove run() returns a valid static candidate list (no live probing).
    import importlib.util
    spec = importlib.util.spec_from_file_location("user_attack", "/kaggle/working/attack.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    from aicomp_sdk.attacks.contracts import AttackRunConfig
    cands = mod.AttackAlgorithm().run(None, AttackRunConfig(time_budget_s=10))
    print(f"SELF-TEST OK: run() returned {len(cands)} static candidates (no probing)")
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
    "machine_shape": "NvidiaTeslaT4",  # P100 is rejected
    "enable_internet": False,
    "competition_sources": [COMP],
    "dataset_sources": [],
    "kernel_sources": [],
}
(OUT / "kernel-metadata.json").write_text(json.dumps(meta, indent=2))
print("wrote", OUT / "submission.ipynb")
print("wrote", OUT / "kernel-metadata.json")
