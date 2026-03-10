# Student Performance Management System (SPMS)

A web-based student performance management system built for Sri Lankan schools, featuring marks tracking, attendance management, AI-powered grade predictions, and worksheet distribution.

## Tech Stack
- **Frontend**: React, Tailwind CSS, Shadcn/UI, Recharts
- **Backend**: FastAPI (Python)
- **Database**: MySQL
- **ML**: scikit-learn (Linear Regression for Term 3 predictions)

## Setup
Run `start.ps1` in PowerShell to start all services, or manually:

1. Start MySQL service
2. Import `school_db.sql` into MySQL
3. Activate Python virtual environment and run `python backend/server.py`
4. In `frontend/`, run `yarn install && yarn start`

## Credentials
- Admin: admin@school.com / admin123
- Teacher: teacher1@school.lk / teacher123
- Student: student1@school.lk / student123
