# Student Performance Management System - Sri Lanka

## Original Problem Statement
Build a Student Performance Management System with MySQL, professional light blue theme, with features:
- Index No format: S0001 (Sri Lankan localization)
- Subjects: Maths, Science, English, Tamil, ICT
- Pre-loaded 500+ students and 20+ teachers with Sri Lankan names (+94 phone codes)
- AI 3-Term Prediction using Linear Regression (scikit-learn)
- Red Alert for students predicted below 35% in Term 3
- PDF and Excel export
- Bulk Import functionality
- No "Made with Emergent" branding
- Remove bell icon and average score card from teacher dashboard
- Show only phone number with call icon (remove email)
- Grade 12 & 13 categorized by streams (Bio, Maths, Commerce, Engineering Technology, Bio Technology, Arts)

## User Personas
1. **Admin** - Manages students, teachers, views class distribution reports
2. **Teacher** - Views at-risk students, enters marks, uploads worksheets for performance levels
3. **Student** - Views personal performance, marks, predictions

## Core Requirements (Implemented)
- [x] MySQL database (MariaDB)
- [x] Authentication with JWT (password eye icon)
- [x] Admin Dashboard with class distribution table (sorted Grade 1-13)
- [x] Student Management (CRUD, pagination, search, filters)
- [x] Teacher Management (CRUD)
- [x] Marks Entry (Term 1, 2, 3 for 5 subjects)
- [x] Attendance Tracking (calendar picker)
- [x] AI Predictions using Linear Regression (scikit-learn)
- [x] At-Risk Students page organized by Grade and Division
- [x] Teacher Dashboard (no bell icon, no average score card)
- [x] Student Dashboard with personal performance
- [x] PDF Export (reportlab)
- [x] Excel Export (xlsxwriter)
- [x] Bulk Import (Excel/CSV support)
- [x] Light blue professional theme
- [x] Sri Lankan names and phone numbers (+94)
- [x] "Made with Emergent" badge removed
- [x] Index Numbers in S0001 format
- [x] Marks as positive integers (no decimals)
- [x] Performance Levels: Level 1 (>70%), Level 2 (40-70%), Level 3 (<40%)
- [x] Worksheets page with student notes and file uploads
- [x] Grade 12 & 13 stream categorization in Admin dashboard

## Technology Stack
- **Backend**: FastAPI, Python, MySQL (MariaDB)
- **Frontend**: React, Tailwind CSS, Shadcn/UI, Recharts
- **AI/ML**: scikit-learn (Linear Regression)
- **Export**: reportlab (PDF), xlsxwriter (Excel)

## Credentials
- Admin: admin@school.com / admin123
- Teacher: teacher1@school.lk / teacher123
- Student: student1@school.lk / student123

## Data Summary
- 500 Students with Sri Lankan names
- 20 Teachers (4 per subject)
- Marks for 5 subjects × 3 terms
- Grade 12 & 13 students with streams assigned

## What's Been Implemented (March 2026)
1. Full MySQL schema with users, students, teachers, marks, attendance, predictions, worksheets, student_notes
2. Authentication system with JWT tokens
3. Complete admin dashboard with class distribution table (sorted Grade 1-13)
4. Grade 12 & 13 show stream breakdown (Bio, Maths, Commerce, etc.)
5. Student and Teacher CRUD with pagination
6. Marks entry and attendance tracking
7. Linear Regression predictions for Term 3
8. Red alert system for at-risk students (< 35%)
9. Teacher dashboard with 2 stat cards only (Total Students, At-Risk Students)
10. Student dashboard with personal performance
11. PDF and Excel export functionality
12. Bulk import with Excel/CSV support
13. **Worksheets page (NEW LAYOUT):**
    - Filter by Grade, Division, Term
    - Student list with individual columns per row:
      - Index No, Student Name, Marks, Level badge
      - Description/Notes text input
      - Upload Worksheet file input
      - Save button per student
    - "Save All" button for batch operations
    - Files stored per student/term/subject
    - Removed old worksheet form and list sections

## SQL Export
- Located at: /app/school_db.sql (731KB)

## API Endpoints (Key)
- POST /api/auth/login - User authentication
- GET /api/dashboard/stats - Admin dashboard stats
- GET /api/class-students/performance - Get students with marks, levels, and worksheet info
- POST /api/students/{id}/worksheet - Save note and/or file for individual student
- POST /api/students/notes/bulk - Bulk save notes
- GET /api/worksheets - Get worksheets
- POST /api/worksheets - Upload worksheet
- GET /api/at-risk-students - Get at-risk students

## Next Action Items
1. Increase student count to 3500 (use /app/scripts/seed_3500_students.py)
2. Increase teacher count to 101
3. Add email notifications for at-risk students
4. Add more sample attendance data

## Future Enhancements
1. Parent/guardian portal with notifications
2. SMS alerts for at-risk students
3. Report cards generation
4. Subject-wise performance comparison
5. Teacher assignment to classes
