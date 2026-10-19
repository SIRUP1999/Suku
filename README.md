# Suku

A mobile-friendly, multi-tenant study platform for Ghanaian junior high schools. The first slice includes school-scoped accounts, syllabus content management, MCQ practice with instant feedback, and student/admin progress views. Subjects and content are data-driven; no subject-specific question logic is built into the schema.

## Workspace layout

- `backend/` — Django REST API, domain models, tenant-scoped endpoints, and Django admin content-entry tools.
- `frontend/` — React + TypeScript + Vite student/admin web application.
- `docker-compose.yml` — local PostgreSQL option.

## Requirements

- Python 3.12+ (tested locally with the available interpreter where dependencies support it)
- Node.js 20+
- PostgreSQL for deployment (SQLite is the local default)

## Run locally

1. Backend:

   ```powershell
   Copy-Item .env.example .env
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py test learning
   python manage.py runserver
   ```

2. Frontend, in another terminal:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

   For a production frontend check, run `npm run build`.
   Configure your static host to fall back to `index.html` for application paths such as `/topics/12`.

3. Open `http://localhost:5173`. Students and school admins sign in with the school's code (the school slug), their username, and password. The English, Mathematics, and Science subject records are seeded automatically; use Django admin at `http://localhost:8000/admin/` to create a school, attach a School Admin user to it, activate the school after confirming payment, and add topics/questions. For now, activation is an admin-controlled status; Paystack checkout and webhooks are intentionally not simulated.

The `.env.example` is for local development only. Production defaults to `DEBUG=false`, requires a strong `SECRET_KEY` of at least 50 characters and a PostgreSQL `DATABASE_URL`, redirects HTTP to HTTPS, enables secure cookies, and emits one-year HSTS. Configure `ALLOWED_HOSTS`, `DATABASE_URL`, and CORS for your deployment. If TLS terminates at a trusted load balancer, set `USE_X_FORWARDED_PROTO=true` only when the application cannot be reached except through that proxy. HSTS preload is enabled by default in production; ensure every subdomain supports HTTPS before deployment. Login throttling uses Redis when `CACHE_URL` is set; otherwise production uses Django's shared database cache, which must be initialized with `python manage.py createcachetable`. To use PostgreSQL locally, start `docker compose up -d db` and set `DATABASE_URL=postgres://suku:suku-dev-password@localhost:5432/suku`.

## Initial workflows

- Admins sign in, create classes and student accounts in batches, and view score/progress summaries filterable by class and subject.
- Student accounts can be deactivated/reactivated and have passwords reset by their school admin. Only active accounts use paid seats. CSV imports are limited to 200 students and 2 MB; create classes first and remove CSV files containing temporary passwords after importing.
- Student usernames are unique within a school, not across all schools. Login uses school slug/code plus username. Login throttling allows 300 requests per IP per minute while limiting each school-code/username pair to 10 per minute.
- Access JWTs expire after 15 minutes and refresh JWTs after 7 days. The web client stores tokens in local storage for this v1.
- Students browse subjects and topics, answer MCQs, and immediately see correctness, the right answer, and the authored method explanation.
- Each student, attempt, and subscription belongs to one school. Content can be shared globally across schools; school performance endpoints always scope data to the signed-in admin's school.

Theory question fields are present in the generic content model for the upcoming AI grading slice. The v1 exercise loop currently serves MCQs only; no success-shaped AI grading stub is exposed. Term subscriptions support explicit dates and seats; Paystack confirmation and automatic renewal/expiry processing remain a later integration.

## API overview

- `POST /api/auth/login/` — obtain JWT tokens; inactive/pending school users cannot log in.
- `GET /api/auth/me/` — signed-in user profile.
- `GET /api/subjects/`, `GET /api/subjects/{id}/topics/`
- `GET /api/topics/{id}/questions/` — question prompts/options only.
- `POST /api/attempts/` — submit an MCQ choice and receive instant feedback.
- `GET /api/progress/` — student's own history and summary.
- `POST /api/admin/students/bulk-create/` — school-admin batch provisioning.
- `POST /api/admin/students/import/` — multipart CSV import (`file` field; `username,password,first_name,last_name,class_name` columns).
- `GET /api/admin/students/`, `PATCH /api/admin/students/{id}/` — manage school-owned student accounts.
- `GET /api/admin/students/{id}/performance/` — view a school-owned student's overall, subject, and topic performance. Areas are labelled Strength (80%+), Building (50–79%), or Needs support (below 50%) based on scored attempts.
- `POST /api/admin/students/{id}/reset-password/` — set a temporary password for a school-owned student.
- `GET|POST /api/admin/classes/` — manage school-owned class groups.
- `GET /api/admin/reports/?class_id={id}&subject_id={id}` — school-admin performance summary with optional class/subject filters.

The Django admin is the initial content-entry interface and supports subjects, topics, MCQs, theory questions, schools, and term subscriptions.
