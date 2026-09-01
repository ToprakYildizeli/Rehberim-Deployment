# Rehberim

**A coaching and study-tracking platform for guidance counselors, students, and parents.**

Version 1.0.0 · Django REST API + React web client + two Flutter mobile apps

---

Turkish high-school students preparing for the university entrance exam (YKS) work
with a guidance counselor who plans their week, tracks what they actually studied,
reviews mock-exam results, and reports progress to parents. Most of that happens on
paper or in spreadsheets. Rehberim moves the whole loop into one system: the
counselor builds a weekly program, the student marks work as done from their phone,
the counselor reviews and **approves** the week, and only then does the parent see it.

Everything each role sees is derived from one shared API — there is no second source
of truth and no screen that invents its own data.

## Repository layout

```
Rehberim/
├── backend/                     Django 6 + DRF — the API and all business logic
│   ├── Django/
│   │   ├── accounts/            identity: User + Counselor/Student/Parent profiles
│   │   ├── Rehberim/            domain: programs, exams, topics, library, calendar
│   │   └── Django/              settings, root urls
│   ├── docs/                    versioned API contracts + roadmap
│   └── docker-compose.yml
└── frontend/
    ├── rehberim_koc/            React + Vite — counselor web app
    ├── rehberim_ogrenci/        Flutter — student mobile app
    └── rehberim_veli/           Flutter — parent mobile app
```

Web is **counselor-only**; students and parents use the mobile apps. All three
clients talk to the same `/api/` surface over JWT.

## Tech stack

| Layer | Choice |
|---|---|
| API | Django 6.0 · Django REST Framework 3.17 · Python 3.14 |
| Auth | `djangorestframework-simplejwt` (access + refresh, blacklist on logout) |
| Database | SQLite in development · PostgreSQL targeted for production |
| Counselor web | React 19 + Vite, CSS Modules, axios |
| Mobile | Flutter (student and parent apps) |
| Dependencies | Pipenv (backend) · npm (web) · pub (mobile) |
| Dev environment | Docker Compose (one command for the backend) |

## What it does

**Counselor (web).** Dashboard of pending actions derived from live data · student
roster with the invite code students use to connect · per-student detail with
books, mock exams, program history, topic mastery and achievements · a drag-and-drop
weekly program board with reusable templates and recurring routines · a calendar of
meetings and exam dates.

**Student (mobile).** Today's program and tasks · library of books with per-topic
progress · mock-exam entry · personal goals · topic mastery.

**Parent (mobile).** Read-only view of the child's mock exams with per-subject
breakdown, **approved** weekly programs and their adherence percentages, topic
progress, weekly study hours, and the shared calendar.

## Engineering notes

The parts that were more interesting than CRUD:

**Three-role authorization, enforced twice.** Every list endpoint narrows its
queryset by role, and every detail endpoint re-checks with an object-level
permission — so a counselor only ever reaches their own students, a student only
their own data, and a parent only their children's. Accounts link through
invite codes: students join a counselor with the counselor's code, and parents join
a child with the child's id plus that child's counselor's code. The
counselor's code is unique and **immutable** — enforced in `save()`, not by
convention.

**Approval as a seal.** When a counselor approves a finished week, the program
locks: the student can no longer edit its tasks, and only then does the week become
visible to the parent. Adherence statistics are computed from approved weeks only,
so a student cannot retroactively tick boxes and move their own numbers.

**Adherence measured in minutes, not checkboxes.** A 20-minute review and a
3-hour mock exam should not weigh the same, so the compliance percentage is
`completed minutes / planned minutes` over blocks that count as study — external
commitments (school, practice, appointments) occupy the calendar but are excluded.
Programs without times fall back to task count and say so in a `basis` field.

**Flexible program windows.** A week is not necessarily seven days: a counselor who
missed Monday can open a five-day program starting in the past. Windows carry a
`day_count`, overlapping ranges for one student are rejected, and narrowing a window
that would orphan a task is refused with an explanation rather than silently
dropping work.

**Routines without a routine model.** A recurring program is not a separate entity —
attaching a student to a program template and enabling `auto_apply` makes that
template their routine, and its tasks materialize into each new week automatically.
One model, two behaviors, no duplicated scheduling logic.

**Derived, not stored.** Mock-exam nets are computed server-side from the
correct/wrong counts the student enters (`net = correct − wrong/4`), so the client
cannot submit an inconsistent score. Achievements are likewise evaluated on every
request instead of being persisted, so changing a threshold or deleting an exam can
never leave a stale badge behind.

**Contracts before code.** Each domain has a versioned contract in
[`backend/docs/`](./backend/docs/) that three clients read from. Endpoint and field
changes go through the contract first; breaking changes bump a major version and say
exactly what moved.

## Running it

### Backend

```bash
cd backend
docker compose up --build          # installs deps, migrates, serves on :8000
```

Or without Docker:

```bash
cd backend/Django
pipenv install && pipenv shell
python manage.py migrate
python manage.py runserver
```

- API root — <http://127.0.0.1:8000/api/>
- Admin — <http://127.0.0.1:8000/admin/> (`python manage.py createsuperuser`)
- Sample data — `python manage.py seed_mockdata`

### Counselor web

```bash
cd frontend/rehberim_koc
cp .env.example .env               # VITE_API_BASE_URL, no hardcoded host
npm install
npm run dev                        # → http://localhost:5173/
```

### Mobile apps

```bash
cd frontend/rehberim_ogrenci       # or rehberim_veli
flutter pub get
flutter run
```

The backend must be running first — the clients are thin and hold no data of their
own.

## Tests

```bash
cd backend/Django && python manage.py test
```

311 API tests covering role permissions, approval rules, adherence and statistics
maths, exam derivation, scheduling edge cases, and the account-linking flows.

## Production readiness

The application logic is complete for v1; deployment configuration is deliberately
still in development mode and is the next piece of work:

- [ ] `SECRET_KEY` moved to the environment, `DEBUG=False`, `ALLOWED_HOSTS` filled
- [ ] PostgreSQL instead of SQLite
- [ ] Production `CORS_ALLOWED_ORIGINS`, static-file serving
- [ ] Locale set to `tr` / `Europe/Istanbul`

## Documentation

| Document | Scope |
|---|---|
| [`backend/docs/roadmap.md`](./backend/docs/roadmap.md) | Phase-by-phase plan and what shipped when |
| [`backend/docs/auth-contract.md`](./backend/docs/auth-contract.md) | Identity, tokens, registration, account linking (v2.0) |
| [`backend/docs/program-contract.md`](./backend/docs/program-contract.md) | Programs, tasks, templates, routines, approval, adherence (v3.6) |
| [`backend/docs/exam-contract.md`](./backend/docs/exam-contract.md) | Mock exams and net calculation |
| [`backend/docs/topics-contract.md`](./backend/docs/topics-contract.md) | Topic catalogue and 1–5 mastery levels |
| [`backend/docs/library-contract.md`](./backend/docs/library-contract.md) | Book library |
| [`backend/docs/goals-calendar-contract.md`](./backend/docs/goals-calendar-contract.md) | Goals and calendar |
| [`backend/docs/achievements-contract.md`](./backend/docs/achievements-contract.md) | Counselor-owned achievement definitions |

Contracts and in-code documentation are written in Turkish, matching the team and
the product's users.

## Team

Built by a four-person team — two on backend, two on frontend — as a university
project. Product scope in [`backend/Rehberim MVP.pdf`](./backend/Rehberim%20MVP.pdf).
