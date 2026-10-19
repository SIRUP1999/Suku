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

3. Open `http://localhost:5173`. The English, Mathematics, and Science subject records are seeded automatically; use Django admin at `http://localhost:8000/admin/` to create a school, attach a School Admin user to it, activate the school after confirming payment, and add topics/questions. For now, activation is an admin-controlled status; Paystack checkout and webhooks are intentionally not simulated.

Copy `.env.example` to `.env` and configure secrets/database settings for deployment. The backend reads environment variables directly. To use PostgreSQL locally, start `docker compose up -d db` and set `DATABASE_URL=postgres://suku:suku-dev-password@localhost:5432/suku`.

## Initial workflows

- Admins sign in, create classes and student accounts in batches, and view score/progress summaries filterable by class and subject.
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
- `GET|POST /api/admin/classes/` — manage school-owned class groups.
- `GET /api/admin/reports/?class_id={id}&subject_id={id}` — school-admin performance summary with optional class/subject filters.

The Django admin is the initial content-entry interface and supports subjects, topics, MCQs, theory questions, schools, and term subscriptions.
