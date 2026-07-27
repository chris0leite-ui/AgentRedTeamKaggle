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
SLUG = "attack-single-post-exfil-v1"

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
# Scored rerun: serve the attack to the gateway. Local/interactive: write a placeholder CSV.
import os, csv
if os.getenv("KAGGLE_IS_COMPETITION_RERUN"):
    import kaggle_evaluation.jed_attack_134815.jed_attack_inference_server as server
    server.JEDAttackInferenceServer().serve()
else:
    with open("/kaggle/working/submission.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["Id", "Score"])
        for row in ["gpt_oss_public", "gpt_oss_private", "gemma_public", "gemma_private"]:
            w.writerow([row, 0.0])
    print("placeholder submission.csv written (real scores come from the gateway rerun)")
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
    "title": "Attack — single-post exfil v1",
    "code_file": "submission.ipynb",
    "language": "python",
    "kernel_type": "notebook",
    "is_private": True,
    "enable_gpu": True,
    "enable_internet": False,
    "competition_sources": [COMP],
    "dataset_sources": [],
    "kernel_sources": [],
}
(OUT / "kernel-metadata.json").write_text(json.dumps(meta, indent=2))

print("wrote", OUT / "submission.ipynb")
print("wrote", OUT / "kernel-metadata.json")
