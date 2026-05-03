# Codex — Initial Work Prompt

> Copy everything below the `---` into Codex to kick off the AI backend work.
> This is a self-contained brief. Codex should not need to ask follow-ups.

---

You are Codex, the AI backend agent for the **AutoApply AI** monorepo at `/Users/srikanth/Documents/Projects/cvyne`.

**Read these files first, in this order, before writing any code:**
1. `CLAUDE.md` — architecture overview (especially the "Open-Source Integrations" section)
2. `AGENTS.md` — your domain ownership and contracts
3. `docs/agents/CODEX.md` — your detailed work queue
4. `docs/architecture/ADR-002-prompt-registry.md`, `ADR-004-open-source-integrations.md`, `ADR-005-litellm-instructor.md`

## Your Mission

Make the AI pipeline actually work end-to-end. The scaffold uses `litellm` + `instructor` for LLM calls, `browser-use` for browser automation, and `open-design` (sidecar) for CV generation. Most of the wiring is done — your job is to verify, fill gaps, and prove the pipeline runs against real LLMs and real job postings.

## Coordination Note

Kiro is building the DB models and security primitives in parallel. You can start P0 immediately because it's independent. P1 and P2 require Kiro's DB to exist — if Kiro hasn't finished P0 yet, mock the DB calls so you can prove your code works in isolation.

## Deliverables (in strict order)

### P0 — Verify the LLM core actually runs

1. **Run the existing prompt tests** to confirm the registry loads:
   ```bash
   cd apps/api
   export ANTHROPIC_API_KEY=<your test key>
   uv run pytest tests/unit/test_prompts.py -v
   ```
   All 6 tests should pass without changes. If they don't, fix the registry — do not modify the tests.

2. **Smoke-test `LLMClient`** with a real call. Create `tests/integration/test_llm_smoke.py`:
   ```python
   import pytest
   from core.llm import LLMClient, LLMProvider
   from prompts.registry import PromptRegistry
   from models.job import JDSchema

   @pytest.mark.asyncio
   async def test_anthropic_structured_output():
       client = LLMClient.from_env(LLMProvider.ANTHROPIC)
       prompt = PromptRegistry.get("jd_extraction")
       rendered = prompt.render(
           job_url="https://example.com/job",
           raw_html="<h1>Senior Python Engineer at Acme Corp</h1><p>5+ years Python, FastAPI, AWS required</p>"
       )
       result = await client.complete(rendered, structured_output=JDSchema)
       assert result.title.lower().startswith("senior python")
       assert result.company == "Acme Corp"
       assert "python" in [s.lower() for s in result.skills_required]
   ```
   This proves litellm + instructor + your registry all work together. Fix anything that breaks.

3. **Verify Anthropic prompt caching works.** Add a second test that calls the same prompt twice and asserts the second response has cache hits. Read `litellm.completion` response object — `_hidden_params` contains cache token counts. Document the assertion in a comment.

### P1 — Wire up the agents end-to-end

4. **Verify browser-use integration.** Create `tests/integration/test_browser_agent.py`:
   ```python
   @pytest.mark.asyncio
   async def test_extract_jd_from_real_url():
       agent = BrowserAgent(provider=LLMProvider.ANTHROPIC, headless=True)
       jd = await agent.extract_jd("https://jobs.lever.co/anthropic")  # or any stable public URL
       assert jd.title
       assert jd.company
   ```
   First run requires `uv run playwright install chromium`. If the test fails for non-code reasons (CAPTCHA, network), pick a different stable URL and document why in a comment.

5. **Verify open-design integration.** First check if the daemon is reachable:
   ```bash
   docker compose -f infrastructure/docker/docker-compose.yml --profile full up -d open-design
   curl http://localhost:4477/api/design-systems
   ```
   Then verify and update `THEME_TO_DESIGN_SYSTEM` in `apps/api/agents/design_agent.py` to use the actual slugs returned by the daemon. Add an integration test that generates a CV PDF for a sample resume and confirms the PDF is non-empty (>10KB) and starts with `%PDF`.

6. **Implement `LLMClient.from_user_config`.** The stub raises `NotImplementedError`. Once Kiro's `db/models.py` and `core/security.py` exist, replace it. Spec is in `docs/agents/CODEX.md` § "First Thing to Build". If Kiro isn't done, write the function but guard the import with a try/except so it gracefully fails until the DB layer lands.

### P2 — Pipeline integration test

7. **End-to-end orchestrator test.** Create `tests/integration/test_orchestrator.py` that runs the full `OrchestratorService.run_application` against a real job URL using a real LLM. Assert that:
   - At least 5 status events are yielded
   - The final event has `status == ApplicationStatus.SUBMITTED` (or `REQUIRES_HUMAN` if CAPTCHA)
   - A CV file ref is produced
   - No unexpected exceptions

   Use `auto_submit=False` in the BrowserAgent autofill so this test doesn't actually submit to a real job board. Pick a job board's "test" mode if available, or mock the autofill step.

### P3 — Prompt quality

8. **Tune the four prompts** in `apps/api/prompts/templates/`. Specifically:
   - Add few-shot examples to `resume_personalize` (1-2 examples of base resume → tailored resume diff). Keep them short — examples cost tokens on every call.
   - Test the `no fabrication` constraint with an adversarial input where the JD asks for skills the candidate doesn't have. The model must NOT add fake skills. Add this as a test in `tests/unit/test_prompt_quality.py`.
   - Bump versions to `v1.1.0` after changes.

## Acceptance Criteria

You're done with P0–P2 when ALL of these pass:

- [ ] `cd apps/api && uv run pytest tests/unit/ -v` — all unit tests green
- [ ] `cd apps/api && uv run pytest tests/integration/test_llm_smoke.py -v` — real Anthropic call returns valid `JDSchema`
- [ ] `cd apps/api && uv run pytest tests/integration/test_browser_agent.py -v` — browser-use extracts a real job posting
- [ ] open-design daemon responds at `/api/design-systems` and `THEME_TO_DESIGN_SYSTEM` matches its slugs
- [ ] `LLMClient.from_user_config(user_id)` works against Kiro's DB (or has a TODO if Kiro hasn't landed yet)
- [ ] Langfuse trace appears for every test LLM call (visible at the configured Langfuse host)
- [ ] Per-call cost is logged: confirm `response._hidden_params["response_cost"]` is non-zero in your tests

## Hard Rules

- **Never** import `anthropic`, `openai`, `google.generativeai`, `litellm` directly outside `core/llm.py`. All LLM calls go through `LLMClient`.
- **Never** put prompt strings in service files. Register them in `apps/api/prompts/templates/` and call `PromptRegistry.get()`.
- **Never** modify `apps/api/db/`, `apps/api/workers/`, `apps/api/core/security.py`, `apps/api/core/storage.py`, or `core/config.py` — Kiro's domain. Notify the user if you need a change.
- **Never** modify anything under `apps/web/` or `packages/` — Antigravity's domain.
- **No LangChain wrappers around browser-use.** Use its bundled `ChatAnthropic` / `ChatOpenAI` / `ChatGoogle` / `ChatBrowserUse`.
- **open-design is a sidecar HTTP service**, not a Python lib. All access via `OpenDesignClient` in `agents/design_agent.py`.
- All agents are **stateless**. No side effects in `__init__`. No class-level state.
- All LLM-callable models use **Pydantic v2** with `structured_output=` — never parse free-text.
- When you change a prompt template, **bump its version**.

## Reporting Back

When you're done with each priority block (P0, P1, P2, P3), report:
1. Files created or modified
2. Test results (paste the pytest summary line)
3. Any prompts whose version bumped, with a one-line "why"
4. Any blockers — specifically: questions for the user or things waiting on Kiro
