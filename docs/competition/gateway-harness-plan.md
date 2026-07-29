# Local faithful-gateway harness — design & plan

Why: two dense submissions (v3/v4) came back COMPLETE with **no score**; every single-post submission
scored. The gateway zeroes a model row if **any one candidate's replay raises**
(`jed_attack_gateway.py:683`) or the **replay phase overruns** its budget (`:761`). Our approximate
offline scorer never reproduced this because it doesn't run the gateway's exact replay path. This
harness runs that exact path locally so real-board **validity** (and roughly, overrun) becomes a
~30-min T4 question with **no submission** — closing the feedback gap that cost us two slots.

## SDK facts the design rests on (verified)
- **Replay is gateway-internal & in-process.** `_replay_and_score` builds a fresh env per candidate and
  calls the model via `RemoteAgent(model_srv.predict)`; `_require_remote_model_server` does
  `importlib.import_module` → the GGUF runs as an in-process module singleton (no relay for replay).
- **Eval loop:** `for model in MODEL_NAMES: generation(DEFAULT_BUDGET_S); for guardrail: _replay_and_score`.
- **Knobs:** `AICOMP_MODEL_NAMES` env (single-model = fastest); guardrails = public locally (private wheel
  absent); `DEFAULT_BUDGET_S` is a module constant → **monkeypatchable** to scale 9000s → ~300s.
- **Candidate dict:** `{"user_messages": [str, …]}`; validated for chain ≤32 and per-msg char cap.
- **`BaseGateway.__init__` builds relay clients** (base_gateway.py:117) we don't need for replay → bypass
  via `JEDAttackGateway.__new__` and set `_fixtures_dir`; `_replay_and_score` needs nothing else from self.
- **Return:** `{"findings", "summary", "score"}`.

## Level 1 (BUILT) — replay-faithful harness  ·  `make_lab_notebook.py --gateway` → `lab_gateway/`
For each model × {single, dense}:
1. `gwmod.DEFAULT_BUDGET_S = 300` (120 in smoke); `gw = JEDAttackGateway.__new__(...)`; `gw._fixtures_dir = FIXTURES`.
2. `agent_factory = gw._make_agent_factory(model)` (in-process GGUF).
3. Generate candidates by running our REAL `run()` in-process (toggle `attack_mod.DENSITY_MODE`), serialize.
4. **The test:** call the real `gw._replay_and_score(cands, model, OptimalGuardrail)`, timed. Catch
   exceptions (validity). Compare replay s/cand vs gen s/cand (the gen→replay asymmetry) and flag
   `would_overrun` = replay wall time > scaled budget.
5. `gw._unload_model(model)` between models (T4 OOM guard).

Outputs per (model, config): RAISED?/detail, gen & replay s/cand, asym ratio, would_overrun, score.
**Verdict:** dense RAISES while single OK → failure reproduced (iterate fix here). Dense OK+fits →
failure is generation-over-relay or hardware timing (→ Level 2).

### Faithfulness of the scaled budget
Validity (raises) is budget-independent. Overrun is a **ratio** (run() self-sizes candidates to the
scaled generation clock; an overrun at 300s overruns at 9000s). Absolute timing keeps the T4-vs-real
hardware factor (same caveat as `--score`), but the code path now matches, giving a cleaner overhead
re-estimate.

### Catches / doesn't
Catches: per-candidate replay exceptions, the per-candidate env-rebuild + validation path, overrun
ratio. Doesn't: real-hardware absolute timing; the private guardrail (absent locally); a socketed
model server IF the real board uses one (looks in-process here — assumption to sanity-check).

## Level 2 (optional, later) — end-to-end relay harness
Drive the full path incl. generation-over-relay via `JEDAttackInferenceServer().run(...)` →
`run_local_gateway`, producing a real `submission.csv`. Requires fixing the `_get_gateway_for_test`
kwarg mismatch (`competition_data_folder` vs `data_paths`) by subclassing / override. Only needed if
Level 1 shows replay is fine (pointing at generation-over-relay).

## Validation of the harness itself
Run on single-post (should score — proves no false failures) AND dense (small N). Smoke = gpt_oss only,
120s, N=6. Then full (both models, 300s, N=24).
