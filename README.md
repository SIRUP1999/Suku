# Suku

A mobile-friendly, multi-tenant study platform for Ghanaian junior high schools. It includes school-scoped accounts, syllabus content management, mixed objective and written-work practice, worked feedback, and student/admin progress views. Subjects and content are data-driven.

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

3. Open `http://localhost:5173`. A school administrator can register a school and receives a school code; the school remains pending until a platform administrator approves it and sets up a subscription. Students can sign up with an active school's code, their name, username, password, and Grade 7, 8, or 9. Students and school staff sign in with their school's code, username, and password. English, Mathematics, and Science subjects are seeded automatically; the mathematics syllabus topics and starter question bank for Grades 7–9 are also seeded. Use Django admin at `http://localhost:8000/admin/` to approve schools, configure subscriptions, and add or edit content. For now, activation is an admin-controlled status; Paystack checkout and webhooks are intentionally not simulated.

The `.env.example` is for local development only. Production defaults to `DEBUG=false`, requires a strong `SECRET_KEY` of at least 50 characters and a PostgreSQL `DATABASE_URL`, redirects HTTP to HTTPS, enables secure cookies, and emits one-year HSTS. Configure `ALLOWED_HOSTS`, `DATABASE_URL`, and CORS for your deployment. If TLS terminates at a trusted load balancer, set `USE_X_FORWARDED_PROTO=true` only when the application cannot be reached except through that proxy. HSTS preload is enabled by default in production; ensure every subdomain supports HTTPS before deployment. Login throttling uses Redis when `CACHE_URL` is set; otherwise production uses Django's shared database cache, which must be initialized with `python manage.py createcachetable`. To use PostgreSQL locally, start `docker compose up -d db` and set `DATABASE_URL=postgres://suku:suku-dev-password@localhost:5432/suku`.

## Initial workflows

- School admins create instructor accounts, classes and student accounts in batches, and view score/progress summaries filterable by class, grade and subject. Instructors can view read-only reports and individual student performance for their own school only.
- Student accounts can be deactivated/reactivated and have passwords reset by their school admin. Only active accounts use paid seats. CSV imports are limited to 200 students and 2 MB; include `username,password,first_name,last_name,grade` and optionally `class_name`, create classes first, and remove CSV files containing temporary passwords after importing.
- Student usernames are unique within a school, not across all schools. Login uses school slug/code plus username. Login throttling allows 300 requests per IP per minute while limiting each school-code/username pair to 10 per minute.
- Access JWTs expire after 15 minutes and refresh JWTs after 7 days. The web client stores tokens in local storage for this v1.
- Mathematics students choose Grade 7, 8, or 9, then a syllabus topic. Each seeded mathematics topic has objective and written-work questions; students show written-work solutions on paper, select an answer, and see the correct answer and worked solution after submitting.
- Mathematics learning is arranged by Grade 7–9 syllabus topic. Each regular topic has a lesson followed by separate Objective Practice (40 A–D questions) and Theory Practice (10 longer problems). Students work through theory questions on paper, choose an A–D answer in Suku, and then review a child-friendly worked solution and mark guide. A separate Paper 2-inspired practice set has six original multi-step problems; students choose four and follow the same paper-working, A–D, worked-solution process. These are original practice materials, not official WAEC questions or reproduced past-paper questions; confirm syllabus alignment with the current NaCCA curriculum before using them as an official scheme of work.
- Theory answers can optionally be checked from a PDF using Gemini. Configure `GEMINI_API_KEY` on the backend only; never put the key in frontend code or send it in chat. The question flow works without a key, and PDF checking reports that it is unavailable until configured. PDFs are size-limited, sent to Gemini only after the student requests a check, and not retained by Suku after checking. Tell students not to include names or other personal details in uploaded work. A Gemini consumer subscription may not include API access or quota; check Google's current AI Studio API terms, free-tier availability, model limits, and region eligibility before enabling this feature.
- Each student, attempt, and subscription belongs to one school. Content can be shared globally across schools; school performance endpoints always scope data to the signed-in admin's school.

Term subscriptions support explicit dates and seats; Paystack confirmation and automatic renewal/expiry processing remain a later integration.

## API overview

- `POST /api/auth/login/` — obtain JWT tokens; inactive/pending school users cannot log in.
- `GET /api/auth/me/` — signed-in user profile.
- `GET /api/subjects/`, `GET /api/subjects/{id}/topics/?grade=7` (optional grade filter)
- `GET /api/topics/{id}/questions/` — question prompts/options only.
- `POST /api/attempts/` — submit an objective or written-work answer choice and receive correctness, the right answer, and worked solution.
- `POST /api/attempts/{id}/work-check/` — optionally upload a PDF (`work` field) for Gemini feedback on a theory attempt; requires the backend `GEMINI_API_KEY`.
- `GET /api/progress/` — student's own history and summary.
- `POST /api/admin/students/bulk-create/` — school-admin batch provisioning.
- `POST /api/auth/register-school/` and `POST /api/auth/register-student/` — public school and student registration.
- `POST /api/admin/students/import/` — multipart CSV import (`file` field; `username,password,first_name,last_name,grade` and optional `class_name` columns).
- `POST /api/admin/teachers/` — create an instructor for the signed-in admin's school.
- `GET /api/admin/students/`, `PATCH /api/admin/students/{id}/` — manage school-owned student accounts.
- `GET /api/admin/students/{id}/performance/` — view a school-owned student's overall, subject, and topic performance. Areas are labelled Strength (80%+), Building (50–79%), or Needs support (below 50%) based on scored attempts.
- `POST /api/admin/students/{id}/reset-password/` — set a temporary password for a school-owned student.
- `GET|POST /api/admin/classes/` — manage school-owned class groups.
- `GET /api/admin/reports/?class_id={id}&subject_id={id}` — school-admin performance summary with optional class/subject filters.

The Django admin is the initial content-entry interface and supports subjects, grade/term topics, MCQs, theory questions, schools, and term subscriptions.
