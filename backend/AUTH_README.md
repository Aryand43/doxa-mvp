# Authentication & Authorisation

This backend implements the auth requirements from the Doxa Agentic AI PRD:

- JWT bearer authentication for AI backend calls
- RBAC through JWT `authorities`
- tenant isolation through `buyer_company_uuid`
- a stable auth context for future agent/service calls
- clear unauthorised-module response text

## Runtime Modes

Local development can stay open:

```env
AUTH_REQUIRED=false
```

UAT/prod-style testing requires a bearer token:

```env
AUTH_REQUIRED=true
AUTH_JWT_SECRET=unit-secret
AUTH_JWT_ALGORITHM=HS256
```

Restart `uvicorn` after changing `.env`.

## JWT Claims

The MVP validator expects HMAC-signed JWTs. Supported claims:

```json
{
  "sub": "test-user",
  "companies": ["3d256fa2-64c3-4045-8174-912e3b122b7d"],
  "authorities": ["AI:read", "REPORT:read", "CRAWLER:read"],
  "roles": ["EXEC"],
  "exp": 1781493803
}
```

Company claims may also be supplied as `company_uuids`, `buyer_company_uuids`,
`buyer_company_uuid`, or `company_uuid`.

User ID may also be supplied as `user_uuid` or `user_id`.

## Authorities

Current endpoint permissions:

| Endpoint | Required authority |
| --- | --- |
| `GET /api/auth/me` | valid token only |
| `POST /api/ai/query` | `AI:read` |
| `POST /api/ai/query` when prompt routes to report mode | `AI:read` + `REPORT:read` |
| `GET /api/ai/summary` | `AI:read` |
| `POST /api/ai/report` | `REPORT:read` |
| `GET /api/ai/report-types` | `REPORT:read` |
| `POST /api/ai/crawl` | `CRAWLER:read` |

Wildcards are supported for local/admin test tokens:

- `*`
- `AI:*`
- `*:read`

## Tenant Isolation

Rows are scoped by the active token's company claims. The backend filters data
where datasets include `buyer_company_uuid`.

Scoped paths include:

- procurement queries
- reports
- crawler detectors and scan counts
- local vector retrieval evidence
- IRIS retrieval metadata, when used

If the token only contains company `A`, records from company `B` are filtered
before the response is built.

## Unauthorised Module Response

RBAC failures return `403` with:

```json
{
  "detail": "You don't have access to that module. Please contact your admin."
}
```

Missing or malformed tokens return `401`.

## Start Backend

From repo root:

```powershell
.\venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

If auth env values changed, stop and restart `uvicorn`. Reload processes can keep
old environment values alive.

## Generate A Full-Access Test Token

```powershell
$env:AUTH_JWT_SECRET="unit-secret"

$token = .\venv\Scripts\python.exe -c "from backend.auth import create_test_token; import time; print(create_test_token({'sub':'test-user','companies':['3d256fa2-64c3-4045-8174-912e3b122b7d'],'authorities':['AI:read','REPORT:read','CRAWLER:read'],'roles':['EXEC'],'exp':int(time.time())+3600}))"
```

## Test Auth Context

```powershell
Invoke-RestMethod `
  -Uri http://localhost:8000/api/auth/me `
  -Headers @{ Authorization = "Bearer $token" }
```

Expected: the response includes `test-user`, company UUID, roles, and authorities.

## Test Assistant

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/api/ai/query `
  -Headers @{ Authorization = "Bearer $token" } `
  -ContentType "application/json" `
  -Body '{"prompt":"What POs are pending my approval today?","explain":false}'
```

Expected: normal assistant response scoped to the token's company.

## Test Reports

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/api/ai/report `
  -Headers @{ Authorization = "Bearer $token" } `
  -ContentType "application/json" `
  -Body '{"report_type":"spend_analysis","target":"BBN4C28"}'
```

Expected: report response.

## Test Crawler

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/api/ai/crawl `
  -Headers @{ Authorization = "Bearer $token" } `
  -ContentType "application/json" `
  -Body '{"window_days":60,"explain":false}'
```

Expected: crawl digest, alerts, phases, and scan stats.

## Test RBAC Denial

Generate a limited token:

```powershell
$env:AUTH_JWT_SECRET="unit-secret"

$limitedToken = .\venv\Scripts\python.exe -c "from backend.auth import create_test_token; import time; print(create_test_token({'sub':'limited-user','companies':['3d256fa2-64c3-4045-8174-912e3b122b7d'],'authorities':['AI:read'],'roles':['USER'],'exp':int(time.time())+3600}))"
```

Call a report endpoint:

```powershell
Invoke-WebRequest `
  -Uri http://localhost:8000/api/ai/report-types `
  -Headers @{ Authorization = "Bearer $limitedToken" }
```

Expected: `403` with the unauthorised-module message.

The same limited token should still work for a normal assistant query:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/api/ai/query `
  -Headers @{ Authorization = "Bearer $limitedToken" } `
  -ContentType "application/json" `
  -Body '{"prompt":"What POs are pending my approval today?","explain":false}'
```

## Test Missing Token

```powershell
Invoke-WebRequest `
  -Method Post `
  -Uri http://localhost:8000/api/ai/query `
  -ContentType "application/json" `
  -Body '{"prompt":"hello"}'
```

Expected: `401`.

## Frontend Token Forwarding

The frontend API client reads a token from either:

- `VITE_AUTH_TOKEN`
- `localStorage["doxa_auth_token"]`
- `localStorage["access_token"]`

Browser console:

```js
localStorage.setItem("doxa_auth_token", "<JWT>")
```

Reload the app and use Assistant, Reports, or Crawler. In browser Network tools,
requests to `/api/ai/*` should include:

```text
Authorization: Bearer <JWT>
```

## Frontend Login Page

The React app includes a login screen that removes the need to paste JWTs into
browser storage by hand.

Flow:

1. The app calls `GET /api/auth/dev-options`.
2. The user selects a tenant and access profile.
3. The app calls `POST /api/auth/dev-login`.
4. The backend issues a signed JWT.
5. The frontend stores it under `localStorage["doxa_auth_token"]`.
6. All `/api/ai/*` calls include `Authorization: Bearer <JWT>`.

Backend endpoints used by the login page:

| Endpoint | Purpose |
| --- | --- |
| `GET /api/auth/dev-options` | Returns mock tenants and access profiles |
| `POST /api/auth/dev-login` | Issues a scoped JWT for local/UAT testing |
| `GET /api/auth/me` | Validates the stored token and returns current user context |

Access profiles:

| Profile | Authorities |
| --- | --- |
| `executive` | `AI:read`, `REPORT:read`, `CRAWLER:read` |
| `assistant` | `AI:read` |
| `reports` | `REPORT:read` |
| `crawler` | `CRAWLER:read` |

To test:

1. Set `AUTH_REQUIRED=true`, `AUTH_JWT_SECRET=unit-secret`, and
   `AUTH_DEV_LOGIN_ENABLED=true`.
2. Restart the backend.
3. Start the frontend.
4. Open the app.
5. Choose a tenant and access profile.
6. Sign in.

Use different tenants to verify row-level isolation. Use `Assistant only` and
then open Reports to verify RBAC denial.

## Testing In Swagger UI / Scalar

FastAPI Swagger UI:

```text
http://localhost:8000/docs
```

Scalar:

```text
http://localhost:8000/scalar
```

Swagger and Scalar are useful for testing auth because protected endpoints show
an authorisation control and send the bearer token for you.

### Authorise Swagger

1. Open `http://localhost:8000/docs`.
2. Click `Authorize`.
3. Paste the raw JWT only.
4. Click `Authorize`.
5. Close the modal.

Paste this:

```text
eyJhbGciOiJIUzI1NiIsInR5cCI6...
```

Do not paste this:

```text
Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6...
```

Swagger already adds the `Bearer` prefix. If you paste the prefix yourself, the
backend receives the wrong value and returns:

```json
{
  "detail": "Bearer token must be a compact JWT."
}
```

### Check The Token Context

Run:

```text
GET /api/auth/me
```

Expected: user ID, companies, authorities, roles, and `auth_required`.

### Test An AI Query

Run:

```text
POST /api/ai/query
```

Request body:

```json
{
  "prompt": "What POs are pending my approval today?",
  "session_id": "swagger-test",
  "explain": false
}
```

Expected: normal assistant response scoped to the token's company.

### Test RBAC Denial

Generate a limited token that only has `AI:read`, then re-authorise Swagger with
that token:

```powershell
$env:AUTH_JWT_SECRET="unit-secret"

$limitedToken = .\venv\Scripts\python.exe -c "from backend.auth import create_test_token; import time; print(create_test_token({'sub':'limited-user','companies':['3d256fa2-64c3-4045-8174-912e3b122b7d'],'authorities':['AI:read'],'roles':['USER'],'exp':int(time.time())+3600}))"
```

Run:

```text
GET /api/ai/report-types
```

Expected:

```json
{
  "detail": "You don't have access to that module. Please contact your admin."
}
```

### Test Tenant Isolation

Authorise Swagger with a token for tenant A and call:

```text
POST /api/ai/query
```

Then log out from the Swagger authorisation modal, authorise with a token for
tenant B, and call the same endpoint with the same prompt.

The returned counts, rows, evidence, and crawler scan stats should be scoped to
the active token's `companies` claim.

## Production Note

This MVP uses HMAC JWT validation because the repository does not currently
include a JWKS-capable JWT dependency. For production, replace the verifier in
`backend/auth.py` with JWKS/RS256 validation while preserving `AuthContext`.
