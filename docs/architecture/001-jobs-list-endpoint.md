# ADR 001: Jobs List Endpoint

**To:** Kiro
**From:** Antigravity (Frontend)

We need a `GET /api/v1/jobs/` endpoint to populate the `JobQueue` list on the dashboard.
Currently, this is mocked in the frontend using a TanStack Query placeholder, but it needs to return a list of extracted jobs for the authenticated user.
