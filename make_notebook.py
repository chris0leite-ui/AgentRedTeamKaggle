"""Generate the Kaggle submission notebook from attack.py (single source of truth).

Produces submission/submission.ipynb + submission/kernel-metadata.json. The notebook:
  1. adds the mounted competition SDK + gateway to sys.path,
  2. writes attack.py to /kaggle/working/attack.py,
  3. on the scored rerun (KAGGLE_IS_COMPETITION_RERUN set) starts the blocking inference
     server so the gateway can drive it; otherwise writes a placeholder submission.csv.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "submission"
OUT.mkdir(exist_ok=True)

KAGGLE_USERNAME = "chrisleitescha"  # kernel owner (lowercased Kaggle handle)
COMP = "ai-agent-security-multi-step-tool-attacks"
SLUG = "attack-burst-v16"  # E5o: gpt hop-saturation BURST (K=7, ~1.5-1.75x); gemma unchanged (notext-700)
# gpt row → _burst_fill (BURST_K=7 in attack.py, replay-safe-sized at 8-hop probe). gemma → notext.
# Kaggle derives the slug from the TITLE, so keep the title slug-clean and matching SLUG.
TITLE = "Attack burst v16"

attack_src = (ROOT / "attack.py").read_text()

# `--blind=N` fires a gemma ceiling-bracket rung: embed GEMMA_BLIND_TARGET=N (attack.py's committed
# default stays 0/safe) and give the kernel a distinct slug so each rung is its own submission.
_blind = next((int(a.split("=", 1)[1]) for a in sys.argv[1:] if a.startswith("--blind=")), 0)
if _blind:
    assert "GEMMA_BLIND_TARGET = 0" in attack_src, "expected GEMMA_BLIND_TARGET=0 default to patch"
    attack_src = attack_src.replace("GEMMA_BLIND_TARGET = 0", f"GEMMA_BLIND_TARGET = {_blind}", 1)
    SLUG = f"attack-gemma-blind-{_blind}"
    TITLE = f"Attack gemma blind {_blind}"

# `--gptblind=N` (E5c) fires a gpt_oss ceiling-bracket rung: blind-fill gpt_oss to N while holding gemma
# at the banked 700 ceiling — gpt_oss is the only variable, so each rung reads its replay ceiling directly.
_gptblind = next((int(a.split("=", 1)[1]) for a in sys.argv[1:] if a.startswith("--gptblind=")), 0)
if _gptblind:
    assert "GPT_BLIND_TARGET = 0" in attack_src, "expected GPT_BLIND_TARGET=0 default to patch"
    assert "GEMMA_BLIND_TARGET = 0" in attack_src, "expected GEMMA_BLIND_TARGET=0 default to patch"
    attack_src = attack_src.replace("GPT_BLIND_TARGET = 0", f"GPT_BLIND_TARGET = {_gptblind}", 1)
    attack_src = attack_src.replace("GEMMA_BLIND_TARGET = 0", "GEMMA_BLIND_TARGET = 700", 1)
    SLUG = f"attack-gpt-blind-{_gptblind}"
    TITLE = f"Attack gpt blind {_gptblind}"

# `--gemvar=hardstop` (E5f) swaps gemma's message form to a leaner "post then stop" variant, to
# board-test whether gemma's per-candidate REPLAY cost has any slack (the only lever with a path
# toward the ~112 leaders). Same clean http.post/SECRET_MARKER trace → private-safe. Combine with
# --blind=N to set the gemma target; slug stays distinct so it is its own submission.
_gemvar = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--gemvar=")), "")
if _gemvar == "hardstop":
    _old = '"Output only the tool call, no other text."'
    _new = '"No other text. Then reply OK."'
    assert _old in attack_src, "gemvar hardstop: could not find _notext_message literal to patch"
    attack_src = attack_src.replace(_old, _new, 1)
    SLUG = f"attack-gemma-hardstop-{_blind or 700}"
    TITLE = f"Attack gemma hardstop {_blind or 700}"

# `--rscap=N` (E5j ladder) sets the gemma REPLAY-SAFE cap to N (keeps GEMMA_BLIND_TARGET=0 so the probed
# replay-safe fill runs, not blind-emit). Distinct slug per rung. Use to map the probed-fill ceiling.
_rscap = next((int(a.split("=", 1)[1]) for a in sys.argv[1:] if a.startswith("--rscap=")), 0)
if _rscap:
    assert "_GEMMA_REPLAY_CAP = 1000" in attack_src, "expected _GEMMA_REPLAY_CAP=1000 default to patch"
    attack_src = attack_src.replace("_GEMMA_REPLAY_CAP = 1000", f"_GEMMA_REPLAY_CAP = {_rscap}", 1)
    SLUG = f"attack-rscap-{_rscap}"
    TITLE = f"Attack rscap {_rscap}"

# Accidental-activation guard: a DEFAULT submission (no bracket flag) must ship the committed 0/safe blind
# targets. A stale non-zero *_BLIND_TARGET would silently bypass replay-safe sizing and can VOID a row
# (E5e: gpt voids beyond ~1250). Refuse to ship a blind-armed default. (Uniqueness assert on the patched
# literals below also guards the string-replaces.)
if not _blind and not _gptblind:
    assert "GEMMA_BLIND_TARGET = 0" in attack_src and "GPT_BLIND_TARGET = 0" in attack_src, (
        "default submission but a *_BLIND_TARGET is non-zero in attack.py — refusing to ship a blind-armed "
        "default (would bypass replay-safe sizing and risk a void)")


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
        import importlib, importlib.util, glob
        from pathlib import Path
        from aicomp_sdk.agents import build_agent_factory
        from aicomp_sdk.evaluation.ops import eval_attack, score_attack
        # Prove the EXACT rerun entrypoint resolves — it is only imported inside the rerun branch above, so
        # a missing/renamed gateway mount would otherwise slip the gate and only fail on the scored rerun.
        _srv = importlib.import_module("kaggle_evaluation.jed_attack_134815.jed_attack_inference_server")
        assert hasattr(_srv, "JEDAttackInferenceServer"), "inference-server class missing — rerun would fail"
        import kaggle_evaluation  # noqa: F401  (verify the gateway package mount)
        spec = importlib.util.spec_from_file_location("user_attack", "/kaggle/working/attack.py")
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        fx = glob.glob("/kaggle/input/**/aicomp_sdk/fixtures/web_corpus.json", recursive=True)
        fixtures = Path(fx[0]).parent if fx else None
        found = eval_attack(mod.AttackAlgorithm, budget_s=45.0,
                            agent_factory=build_agent_factory("deterministic"),
                            env_selection="gym", attack_env_seed=123, fixtures_dir=fixtures)
        print(f"SELF-TEST OK: run()+replay completed cleanly | findings={len(found)} "
              f"score={score_attack(found, normalize=True):.4f} "
              f"(0 is expected vs the deterministic scaffold; the real models exercise the primitive)")
    except Exception as e:
        print(f"SELF-TEST FAILED — fix before submitting: {type(e).__name__}: {e}")
        raise
'''

# Embedding guard: attack.py is embedded in a raw `r'''...'''`. A `'''` or a trailing backslash inside it
# would silently break the generated cell (only failing on Kaggle → a wasted submission). Fail here instead.
assert "'''" not in attack_src, "attack.py contains ''' — would break the r'''...''' embedding"
assert not attack_src.rstrip().endswith("\\"), "attack.py ends with a backslash — invalid in an r'''...'''"

nb = {
    "cells": [code(setup), code(write_attack), code(serve)],
    "metadata": {
        "kernelspec": {"language": "python", "display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4, "nbformat_minor": 5,
}

# Generation-time gate: every emitted code cell must PARSE, and carry no unsubstituted `__TOKEN__`
# placeholder — catches embedding/escaping bugs (e.g. the earlier \n-vs-\\n break) before push, not on Kaggle.
import re as _re
for _c in nb["cells"]:
    if _c.get("cell_type") == "code":
        _s = "".join(_c["source"])
        compile(_s, "<generated-cell>", "exec")
        assert not _re.search(r"__[A-Z][A-Z0-9_]*__", _s), "unsubstituted __TOKEN__ in a generated cell"

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
