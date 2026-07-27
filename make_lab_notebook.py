"""Generate the Kaggle LAB notebook — measures real-model fire-rate + latency.

This is NOT a submission. It runs the *exact* leaderboard models (the GGUF/llama.cpp
gpt_oss + gemma servers) against our attack primitive on a free T4, so we can read the two
numbers we can't get offline:
  1. fire-rate  — does the real model obey the prompt and emit the http.post?
  2. latency    — seconds per candidate → the replay-safe candidate count.

It spends NO competition submission (it's a plain notebook commit). See docs/competition/iteration.md.

Produces lab/lab.ipynb + lab/kernel-metadata.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# --smoke: a fast end-to-end check on Kaggle — ONE model (gpt_oss, fits the T4 cleanly), 2 probes.
# Proves mount + llama.cpp install + real GGUF load + probe all work before the full measurement.
SMOKE = "--smoke" in sys.argv

ROOT = Path(__file__).resolve().parent
OUT = ROOT / ("lab_smoke" if SMOKE else "lab")
OUT.mkdir(exist_ok=True)

KAGGLE_USERNAME = "chrisleitescha"
COMP = "ai-agent-security-multi-step-tool-attacks"
SLUG = "attack-lab-smoke" if SMOKE else "attack-lab-fire-rate"
# Kaggle derives the kernel slug from the TITLE (not the id), so keep the title slug-clean and
# matching SLUG to avoid a surprising URL.
TITLE = "Attack lab smoke" if SMOKE else "Attack lab fire rate"

N_TRIALS = 2 if SMOKE else 20
RUN_GEMMA = not SMOKE

attack_src = (ROOT / "attack.py").read_text()


def code(src: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": src.splitlines(keepends=True)}


def md(src: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": src.splitlines(keepends=True)}


intro = '''\
# Lab — real-model fire-rate + latency

Runs the **exact leaderboard models** (gpt_oss + gemma, GGUF via llama.cpp) against our attack
primitive on a T4. Reports fire-rate and seconds/candidate → the replay-safe candidate count.
**Not a submission — spends nothing.** Internet is ON only to fetch the GGUF weights.
'''

setup = '''\
# 1) Mount the competition SDK + gateway.
import glob, os, sys, time
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
sys.path.insert(0, "/kaggle/working")

import aicomp_sdk  # noqa: F401
print("aicomp_sdk:", os.path.dirname(aicomp_sdk.__file__))
_fx = glob.glob("/kaggle/input/**/aicomp_sdk/fixtures/web_corpus.json", recursive=True)
FIXTURES = Path(_fx[0]).parent if _fx else None
print("fixtures:", FIXTURES)
'''

# Embed attack.py via concatenation with triple-SINGLE quotes (attack.py's docstrings use """,
# so a raw triple-double-quoted wrapper would terminate early — this is why make_notebook.py does
# it this way too). attack.py contains no ''' sequence.
write_attack = (
    "# 1b) Drop in our version-controlled attack.py (single source of truth for the primitive).\n"
    "ATTACK_SRC = r'''" + attack_src + "'''\n"
    "with open('/kaggle/working/attack.py', 'w') as f:\n"
    "    f.write(ATTACK_SRC)\n"
    "import py_compile; py_compile.compile('/kaggle/working/attack.py', doraise=True)\n"
    "print('wrote /kaggle/working/attack.py (%d bytes)' % len(ATTACK_SRC))\n"
)

ensure_llama = '''\
# 2) Ensure llama-cpp-python (CUDA) is importable. Prefer a mounted wheel; else pip (internet ON).
import subprocess, sys, glob, os
try:
    import llama_cpp
    print("llama_cpp already present:", llama_cpp.__version__)
except Exception:
    whls = glob.glob("/kaggle/input/**/llama_cpp_python*.whl", recursive=True)
    installed = False
    if whls:
        print("installing mounted wheel:", whls[0])
        installed = subprocess.run([sys.executable, "-m", "pip", "install", "-q", whls[0]]).returncode == 0
    if not installed:
        for idx in ("cu124", "cu122", "cu121"):
            url = f"https://abetlen.github.io/llama-cpp-python/whl/{idx}"
            print("trying prebuilt CUDA wheel:", idx, flush=True)
            if subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                               "llama-cpp-python", "--extra-index-url", url]).returncode == 0:
                installed = True
                print("installed via", idx)
                break
    if not installed:
        print("prebuilt wheels failed; compiling from source with CUDA (slow)...", flush=True)
        os.environ["CMAKE_ARGS"] = "-DGGML_CUDA=on"
        subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                        "--no-cache-dir", "llama-cpp-python"], check=True)
    import llama_cpp
    print("llama_cpp ready:", llama_cpp.__version__)
'''

harness = '''\
# 3) Build each real model the SAME WAY the leaderboard gateway does, then probe our primitive.
#    We import the model SPECs straight from the gateway's own model servers, so repo / filename /
#    n_ctx / tool settings can never drift from what actually scores us.
import gc, time
from aicomp_sdk.agents.hf_chat_template.backends.llama_cpp import LlamaCppChatTemplateBackend
from aicomp_sdk.agents.hf_chat_template.types import HFBackendConfig
from aicomp_sdk.core.env.sandbox import SandboxEnv
from aicomp_sdk.guardrails.optimal import Guardrail as OptimalGuardrail
from aicomp_sdk.core.predicates import eval_predicates
from huggingface_hub import hf_hub_download
from kaggle_evaluation.jed_attack_134815.gpt_oss_model_server import SPEC as GPT_OSS_SPEC
from kaggle_evaluation.jed_attack_134815.gemma_model_server import SPEC as GEMMA_SPEC
from attack import AttackAlgorithm

# --- knobs (set by make_lab_notebook.py) ---
N_TRIALS = __N_TRIALS__  # candidates probed per model (raise for a tighter fire-rate estimate)
RUN_GEMMA = __RUN_GEMMA__
MAX_HOPS = 4             # tool hops per candidate (matches our smoke default)
REPLAY_BUDGET_S = 9000.0 # gateway per-model replay budget
FILL = 0.9               # leave a 10% cushion when computing the replay-safe count


def build_agent(spec, n_gpu_layers=-1):
    """Resolve GGUF (mounted path env var, else hf download) and wrap in the gateway's agent."""
    mp = os.environ.get(spec.model_path_env_var, "").strip()
    model_path = mp if (mp and os.path.exists(mp)) else hf_hub_download(
        repo_id=spec.repo(), filename=spec.filename())
    cfg = HFBackendConfig(model_id=spec.model_id, model_path=model_path,
                          max_new_tokens=spec.max_new_tokens)
    backend = LlamaCppChatTemplateBackend.from_model_path(
        model_path=model_path, config=cfg, n_ctx=spec.n_ctx,
        n_gpu_layers=n_gpu_layers, supports_tools=spec.supports_tools)
    return spec.create_agent(backend), backend


def measure(spec, n_gpu_layers=-1):
    print(f"\\n=== {spec.model_label}: loading {spec.repo()}/{spec.filename()} "
          f"(n_gpu_layers={n_gpu_layers}) ===", flush=True)
    t0 = time.monotonic()
    agent, backend = build_agent(spec, n_gpu_layers)
    print(f"loaded in {time.monotonic() - t0:.0f}s", flush=True)
    env = SandboxEnv(seed=123, fixtures_dir=FIXTURES, agent=agent, guardrail=OptimalGuardrail())
    domains = AttackAlgorithm._unique_domains()
    fires, times = 0, []
    for i in range(N_TRIALS):
        msg = AttackAlgorithm._exfil_message(next(domains), i)
        env.reset()
        s = time.monotonic()
        fired = False
        try:
            env.interact(msg, max_tool_hops=MAX_HOPS)
            fired = bool(eval_predicates(env.export_trace_dict()))
        except Exception as e:
            print("  probe error:", type(e).__name__, e)
        dt = time.monotonic() - s
        times.append(dt); fires += int(fired)
        print(f"  [{i + 1:>2}/{N_TRIALS}] fired={fired!s:<5} {dt:5.1f}s", flush=True)
    mean = sum(times) / len(times) if times else 0.0
    rate = fires / N_TRIALS if N_TRIALS else 0.0
    implied = int(FILL * REPLAY_BUDGET_S / mean) if mean > 0 else 0
    print(f"\\n>>> {spec.model_label}: fire-rate={rate:.0%} ({fires}/{N_TRIALS}) | "
          f"mean {mean:.1f}s/candidate | replay-safe count ≈ {implied}", flush=True)
    backend.close(); del agent, backend, env; gc.collect()
    try:
        import torch; torch.cuda.empty_cache()
    except Exception:
        pass
    return {"model": spec.model_label, "fire_rate": rate, "mean_s": round(mean, 2),
            "implied_count": implied}


def measure_safe(spec):
    try:
        return measure(spec)
    except Exception as e:
        print(f"full-GPU load failed ({type(e).__name__}: {e}); retrying with partial offload",
              flush=True)
        gc.collect()
        try:
            import torch; torch.cuda.empty_cache()
        except Exception:
            pass
        return measure(spec, n_gpu_layers=20)


results = [measure_safe(GPT_OSS_SPEC)]
if RUN_GEMMA:
    results.append(measure_safe(GEMMA_SPEC))
print("\\n==================== SUMMARY ====================")
for r in results:
    print(r)
print("\\nreplay-safe count = 0.9 * 9000s / mean_s_per_candidate. Use the SMALLER of the two")
print("models' counts (and its fire-rate) to size the real submission.")
'''

harness = (harness
           .replace("__N_TRIALS__", str(N_TRIALS))
           .replace("__RUN_GEMMA__", str(RUN_GEMMA)))

nb = {
    "cells": [md(intro), code(setup), code(write_attack), code(ensure_llama), code(harness)],
    "metadata": {
        "kernelspec": {"language": "python", "display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4, "nbformat_minor": 5,
}
(OUT / "lab.ipynb").write_text(json.dumps(nb, indent=1))

meta = {
    "id": f"{KAGGLE_USERNAME}/{SLUG}",
    "title": TITLE,
    "code_file": "lab.ipynb",
    "language": "python",
    "kernel_type": "notebook",
    "is_private": True,
    "enable_gpu": True,
    "machine_shape": "NvidiaTeslaT4",  # P100 is rejected by this competition
    "enable_internet": True,           # only to fetch the GGUF weights (this is not a submission)
    "competition_sources": [COMP],
    "dataset_sources": [],
    "kernel_sources": [],
}
(OUT / "kernel-metadata.json").write_text(json.dumps(meta, indent=2))

print("wrote", OUT / "lab.ipynb")
print("wrote", OUT / "kernel-metadata.json")
