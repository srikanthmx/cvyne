"""JD extraction prompt — parse raw job page HTML into structured JobSchema."""

from prompts.registry import PromptRegistry, PromptTemplate

PromptRegistry.register(
    PromptTemplate(
        name="jd_extraction",
        version="v1.0.0",
        temperature=0.0,
        system_template="""You are a precise job description parser. Extract structured information from job posting HTML.

Rules:
- Extract ONLY information explicitly stated in the posting
- Do not infer or fabricate requirements
- Normalize experience levels: "entry" | "mid" | "senior" | "lead" | "executive"
- Skills must be atomic (no "Python/Django" — split to ["Python", "Django"])
- If a field is not present, omit it or use null

Output the extracted job as JSON matching the provided schema exactly.""",
        user_template="""Job URL: {{ job_url }}

Raw page content:
<job_content>
{{ raw_html | truncate(8000) }}
</job_content>

Extract the job details into structured JSON.""",
        metadata={"owner": "Codex", "eval_metrics": ["field_recall", "no_hallucination"]},
    )
)
