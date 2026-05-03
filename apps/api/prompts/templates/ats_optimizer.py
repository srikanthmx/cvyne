"""ATS optimization prompt — ensure resume passes applicant tracking systems."""

from prompts.registry import PromptRegistry, PromptTemplate

PromptRegistry.register(
    PromptTemplate(
        name="ats_optimize",
        version="v1.1.0",
        temperature=0.1,
        system_template="""You are an ATS (Applicant Tracking System) optimization expert.

ATS rules to enforce:
- Standard section headings: Experience, Education, Skills, Projects, Certifications
- No tables, columns, or graphics in ATS mode
- Skills listed as comma-separated plain text
- Date format: MM/YYYY or YYYY
- Bullet points start with strong action verbs
- No special characters except hyphens and periods
- File-safe characters only
- Keep JSON schema fields intact; do not drop optional sections that contain source content
- Only include JD keywords when they already match resume evidence

Do not change meaning — only structure and formatting.""",
        user_template="""Resume to optimize:
<resume>
{{ resume_json }}
</resume>

JD Keywords to ensure are present:
{{ keywords | join(", ") }}

Return the ATS-optimized resume JSON.""",
        metadata={"owner": "Codex", "eval_metrics": ["ats_parse_score", "keyword_density"]},
    )
)
