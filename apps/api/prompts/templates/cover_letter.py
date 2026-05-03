"""Cover letter generation prompt."""

from prompts.registry import PromptRegistry, PromptTemplate

PromptRegistry.register(
    PromptTemplate(
        name="cover_letter",
        version="v1.1.0",
        temperature=0.5,
        system_template="""You are a professional cover letter writer. Write compelling, authentic cover letters.

Rules:
- 3-4 short paragraphs maximum
- Opening: specific role + company name + one genuine hook
- Middle: 2-3 most relevant accomplishments from resume (match JD)
- Closing: clear call to action, no clichés
- Tone: confident but not arrogant, genuine not generic
- Never fabricate achievements not in the resume
- If a requirement has no matching resume evidence, do not claim it
- Do not use: "I am writing to express", "To whom it may concern", "I believe I am a great fit"
- Do not summarize the resume — complement it""",
        user_template="""Resume (key highlights):
<resume_highlights>
Name: {{ name }}
Current/Recent Role: {{ current_role }}
Top Skills: {{ top_skills | join(", ") }}
Key Achievements:
{% for bullet in top_bullets %}
- {{ bullet }}
{% endfor %}
</resume_highlights>

Job:
Company: {{ company }}
Role: {{ job_title }}
Key Requirements: {{ key_requirements | join(", ") }}
Company Info: {{ company_info | default("Not provided") }}

Write a cover letter for this application.""",
        metadata={"owner": "Codex", "eval_metrics": ["authenticity", "relevance_to_jd"]},
    )
)
