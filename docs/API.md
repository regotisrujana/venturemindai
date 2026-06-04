# API Documentation

Base URL: `http://localhost:8000/api`

Interactive docs: `/api/docs`

## Auth

`POST /auth/register`

```json
{"email":"founder@example.com","full_name":"Founder","password":"Founder123!"}
```

`POST /auth/login`

```json
{"email":"founder@example.com","password":"Founder123!"}
```

Returns:

```json
{"access_token":"jwt","token_type":"bearer","user":{"id":1,"email":"founder@example.com","role":"user"}}
```

`GET /auth/me`

Requires bearer token. Returns current user profile.

## Analysis

`POST /analysis`

```json
{
  "mode": "startup",
  "query": "AI Recruitment Platform",
  "project_name": "AI Recruitment Platform",
  "industry": "HR Tech"
}
```

Modes:

- `startup`
- `company_comparison`
- `startup_vs_competitors`

Returns a full report with sections, citations, scorecard, viability score, and confidence score.

`GET /analysis/reports`

Returns user reports, or all reports for admins.

`GET /analysis/reports/{report_id}`

Returns one report if the user owns it or is admin.

## RAG

`POST /rag/upload`

Multipart form:

- `collection`: one knowledge-base collection name
- `file`: UTF-8 text document

`POST /rag/search`

```json
{"query":"pricing strategy for AI recruiting","collection":"Market Reports","limit":5}
```

Returns semantic-style retrieval hits with source, collection, and confidence.

## Dashboards

`GET /dashboard/user`

User metrics, recent reports, and scorecards.

`GET /dashboard/admin`

Admin metrics, agent usage, industry analytics, security count, audit count.

`GET /dashboard/evaluation`

Admin-only evaluation history.

`GET /dashboard/security`

Admin-only security events.

## Admin

`GET /admin/users`

Admin-only user management list.

`GET /admin/agent-logs`

Admin-only agent execution logs.

`GET /admin/audit-logs`

Admin-only audit logs.

## Reports

`GET /reports/{report_id}/download.pdf`

Downloads a PDF report.

`GET /reports/{report_id}/download.docx`

Downloads a DOCX report.

`POST /reports/{report_id}/feedback`

```json
{"rating":5,"comment":"Useful report"}
```
