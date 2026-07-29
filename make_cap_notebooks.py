"""Generate three dense submission notebooks at caps 80 / 100 / 120 (E4h calibration).

v6 proved dense scores (11.84 at cap 20); v3/v4 died from replay OVERRUN at large counts. This
sweeps three hard COUNT caps in parallel (one submission each) to pin the real overrun edge in a
single day: whichever caps SCORE are safe; the first that FAILS (no score) is past the edge.
Each notebook embeds the version-controlled attack.py with only `_MAX_RETURN_CANDIDATES` changed.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KAGGLE_USERNAME = "chrisleitescha"
COMP = "ai-agent-security-multi-step-tool-attacks"
CAPS = {80: "v7", 100: "v8", 120: "v9"}  # cap -> version label

base_src = (ROOT / "attack.py").read_text()
assert base_src.count("_MAX_RETURN_CANDIDATES = 80") == 1, "cap anchor not found exactly once"
assert "DENSITY_MODE = True" in base_src, "dense must be ON"


def code(src: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": src.splitlines(keepends=True)}


setup = '''\
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
              f"(0 expected vs deterministic scaffold; real models exercise the primitive)")
    except Exception as e:
        print(f"SELF-TEST FAILED: {type(e).__name__}: {e}")
        raise
'''

for cap, ver in CAPS.items():
    src = base_src.replace("_MAX_RETURN_CANDIDATES = 80", f"_MAX_RETURN_CANDIDATES = {cap}", 1)
    assert f"_MAX_RETURN_CANDIDATES = {cap}" in src and "DENSITY_MODE = True" in src
    out = ROOT / f"submission_cap{cap}"
    out.mkdir(exist_ok=True)
    write_attack = (
        f"# Dense submission, hard count cap = {cap} (E4h calibration).\n"
        "ATTACK_SRC = r'''" + src + "'''\n"
        "with open('/kaggle/working/attack.py', 'w') as f:\n"
        "    f.write(ATTACK_SRC)\n"
        "import py_compile; py_compile.compile('/kaggle/working/attack.py', doraise=True)\n"
        f"assert '_MAX_RETURN_CANDIDATES = {cap}' in ATTACK_SRC and 'DENSITY_MODE = True' in ATTACK_SRC\n"
        f"print('wrote attack.py (%d bytes) [dense cap {cap}]' % len(ATTACK_SRC))\n"
    )
    nb = {
        "cells": [code(setup), code(write_attack), code(serve)],
        "metadata": {
            "kernelspec": {"language": "python", "display_name": "Python 3", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4, "nbformat_minor": 5,
    }
    (out / "submission.ipynb").write_text(json.dumps(nb, indent=1))
    slug = f"attack-dense-cap{cap}-{ver}"
    meta = {
        "id": f"{KAGGLE_USERNAME}/{slug}",
        "title": f"Attack dense cap{cap} {ver}",
        "code_file": "submission.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": True,
        "machine_shape": "NvidiaTeslaT4",
        "enable_internet": False,
        "competition_sources": [COMP],
        "dataset_sources": [],
        "kernel_sources": [],
    }
    (out / "kernel-metadata.json").write_text(json.dumps(meta, indent=2))
    print(f"wrote {out}  ->  {slug}")
