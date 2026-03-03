from fastapi import FastAPI, APIRouter, HTTPException, Depends, Query, Response, Form, File, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import mysql.connector
from mysql.connector import pooling
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import random
import numpy as np
from sklearn.linear_model import LinearRegression
from jose import jwt
import hashlib
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import xlsxwriter
from fastapi.middleware.cors import CORSMiddleware

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MySQL connection pool
MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'school_db')

# Create connection pool
dbconfig = {
    "host": MYSQL_HOST,
    "user": MYSQL_USER,
    "password": MYSQL_PASSWORD,
    "database": MYSQL_DATABASE
}

connection_pool = None

def get_db_connection():
    global connection_pool
    if connection_pool is None:
        try:
            connection_pool = pooling.MySQLConnectionPool(
                pool_name="school_pool",
                pool_size=10,
                **dbconfig
            )
        except Exception as e:
            logging.error(f"Failed to create connection pool: {e}")
            return None
    try:
        return connection_pool.get_connection()
    except Exception as e:
        logging.error(f"Failed to get connection: {e}")
        return None

# JWT settings
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# Simple password hashing using SHA256
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

security = HTTPBearer()

# Create the main app
app = FastAPI(title="Student Performance Management System")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
api_router = APIRouter(prefix="/api")

# Pydantic Models
class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class StudentCreate(BaseModel):
    index_no: str
    first_name: str
    last_name: str
    email: str
    phone: str
    grade: str
    section: str

class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    grade: Optional[str] = None
    section: Optional[str] = None

class TeacherCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    subject: str

class TeacherUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    subject: Optional[str] = None

class MarkEntry(BaseModel):
    student_id: int
    subject: str
    term: int
    marks: float

class AttendanceEntry(BaseModel):
    student_id: int
    date: str
    status: str

class BulkStudentImport(BaseModel):
    students: List[StudentCreate]

class BulkTeacherImport(BaseModel):
    teachers: List[TeacherCreate]

# Sri Lankan names for data generation
SL_FIRST_NAMES = [
    "Kavindu", "Sahan", "Tharindu", "Dilshan", "Kasun", "Nuwan", "Chamara", "Ashan", "Rukshan", "Dinesh",
    "Amaya", "Sachini", "Ishara", "Kavindi", "Nethmi", "Hiruni", "Tharushi", "Dinusha", "Hasini", "Lakshika",
    "Malith", "Chamod", "Shehan", "Ravindu", "Lakmal", "Janith", "Supun", "Pasan", "Gayan", "Dilan",
    "Sanduni", "Nimasha", "Dilini", "Rashmi", "Gayani", "Sithara", "Ashani", "Thilini", "Pavithra", "Chamodi",
    "Sampath", "Nipun", "Hansaka", "Tharaka", "Lasith", "Chamika", "Ashen", "Dulaj", "Ruwani", "Maheshi",
    "Indika", "Pradeep", "Suresh", "Ramesh", "Nimal", "Gamini", "Ajith", "Saman", "Rohan", "Kumara",
    "Sanjeewa", "Thilak", "Bandara", "Ruwan", "Chanaka", "Wasantha", "Nalin", "Prasad", "Eranga", "Chathura"
]

SL_LAST_NAMES = [
    "Perera", "Silva", "Fernando", "Jayasuriya", "Wickramasinghe", "Gunasekara", "Dissanayake", "Rathnayake",
    "Bandara", "Kumara", "Wijesinghe", "Rajapaksa", "Senanayake", "Karunaratne", "Mendis", "Liyanage",
    "Herath", "Samaraweera", "Gamage", "Jayawardena", "Abeysekara", "Ekanayake", "Weerasinghe", "Amarasinghe",
    "Pathirana", "Gunawardena", "Ranasinghe", "Senaratne", "Karunanayake", "Thilakaratne", "Peiris", "De Mel"
]

SUBJECTS = ["Maths", "Science", "English", "Tamil", "ICT"]
GRADES = ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12", "Grade 13"]
SECTIONS = ["A", "B", "C", "D"]
AL_STREAMS = ["Bio", "Maths", "Commerce", "Engineering Technology", "Bio Technology", "Arts"]

def generate_username(first_name: str, phone: str) -> str:
    """Generate username as FirstName + Last 2 digits of Phone"""
    last_two = phone[-2:] if len(phone) >= 2 else "00"
    return f"{first_name}{last_two}"

def generate_phone():
    """Generate Sri Lankan phone number"""
    return f"+947{random.randint(0, 9)}{random.randint(1000000, 9999999)}"

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

# Initialize database
def init_database():
    try:
        # Connect without database first
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        cursor = conn.cursor()
        
        # Create database if not exists
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE}")
        cursor.execute(f"USE {MYSQL_DATABASE}")
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                phone VARCHAR(20),
                role ENUM('admin', 'teacher', 'student') NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create students table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                index_no VARCHAR(50) UNIQUE NOT NULL,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                phone VARCHAR(20),
                grade VARCHAR(20) NOT NULL,
                section VARCHAR(10) NOT NULL,
                stream VARCHAR(50) DEFAULT NULL,
                user_id INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            )
        """)
        
        # Create teachers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teachers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                phone VARCHAR(20),
                subject VARCHAR(50) NOT NULL,
                user_id INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            )
        """)
        
        # Create marks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS marks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                subject VARCHAR(50) NOT NULL,
                term INT NOT NULL,
                marks FLOAT NOT NULL,
                entered_by INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY (entered_by) REFERENCES users(id) ON DELETE SET NULL,
                UNIQUE KEY unique_mark (student_id, subject, term)
            )
        """)
        
        # Create attendance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                date DATE NOT NULL,
                status ENUM('present', 'absent', 'late') NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                UNIQUE KEY unique_attendance (student_id, date)
            )
        """)
        
        # Create predictions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                subject VARCHAR(50) NOT NULL,
                predicted_term3 FLOAT NOT NULL,
                is_at_risk BOOLEAN DEFAULT FALSE,
                calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                UNIQUE KEY unique_prediction (student_id, subject)
            )
        """)
        
        # Create worksheets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS worksheets (
                id INT AUTO_INCREMENT PRIMARY KEY,
                teacher_id INT NOT NULL,
                subject VARCHAR(50) NOT NULL,
                tier VARCHAR(10) NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                file_path VARCHAR(500) DEFAULT NULL,
                file_name VARCHAR(255) DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Create student_notes table for worksheet notes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_notes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                teacher_id INT NOT NULL,
                subject VARCHAR(50) NOT NULL,
                term INT NOT NULL,
                note TEXT,
                file_path VARCHAR(500) DEFAULT NULL,
                file_name VARCHAR(255) DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE KEY unique_student_note (student_id, subject, term)
            )
        """)

        # Add submission and download-tracking columns to student_notes if not present
        try:
            cursor.execute("ALTER TABLE student_notes ADD COLUMN submission_file_path VARCHAR(500) DEFAULT NULL")
            cursor.execute("ALTER TABLE student_notes ADD COLUMN submission_file_name VARCHAR(255) DEFAULT NULL")
            conn.commit()
        except Exception:
            pass  # Columns already exist
        try:
            cursor.execute("ALTER TABLE student_notes ADD COLUMN downloaded_at TIMESTAMP NULL DEFAULT NULL")
            conn.commit()
        except Exception:
            pass  # Column already exists

        conn.commit()

        # Check if admin exists
        cursor.execute("SELECT id FROM users WHERE email = 'admin@school.com'")
        if not cursor.fetchone():
            # Create admin user
            admin_password = hash_password("admin123")
            cursor.execute("""
                INSERT INTO users (username, email, password, first_name, last_name, phone, role)
                VALUES ('Admin00', 'admin@school.com', %s, 'Admin', 'User', '+94700000000', 'admin')
            """, (admin_password,))
            conn.commit()
            logging.info("Admin user created successfully")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Database initialization error: {e}")
        return False

def seed_data():
    """Generate sample data for students and teachers"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check if data already seeded
        cursor.execute("SELECT COUNT(*) FROM students")
        student_count = cursor.fetchone()[0]
        if student_count >= 100:
            cursor.close()
            conn.close()
            return True
        
        # Clear existing data for fresh seed
        cursor.execute("DELETE FROM predictions")
        cursor.execute("DELETE FROM attendance")
        cursor.execute("DELETE FROM marks")
        cursor.execute("DELETE FROM students")
        cursor.execute("DELETE FROM teachers")
        cursor.execute("DELETE FROM users WHERE role != 'admin'")
        conn.commit()
        
        # Generate 500 students (reduced for faster startup)
        students_data = []
        students_user_data = []
        
        for i in range(500):
            first_name = random.choice(SL_FIRST_NAMES)
            last_name = random.choice(SL_LAST_NAMES)
            phone = generate_phone()
            username = generate_username(first_name, phone)
            email = f"student{i+1}@school.lk"
            index_no = f"S{str(i+1).zfill(4)}"
            grade = random.choice(GRADES)
            section = random.choice(SECTIONS)
            password = hash_password("student123")
            
            students_user_data.append((username + str(i), email, password, first_name, last_name, phone, 'student'))
            students_data.append((index_no, first_name, last_name, email, phone, grade, section))
        
        # Insert student users
        cursor.executemany("""
            INSERT INTO users (username, email, password, first_name, last_name, phone, role)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, students_user_data)
        conn.commit()
        
        # Get user IDs
        cursor.execute("SELECT id, email FROM users WHERE role = 'student' ORDER BY id")
        user_map = {row[1]: row[0] for row in cursor.fetchall()}
        
        # Insert students with user_id
        students_with_userid = []
        for i, student in enumerate(students_data):
            user_id = user_map.get(student[2])
            students_with_userid.append(student + (user_id,))
        
        cursor.executemany("""
            INSERT INTO students (index_no, first_name, last_name, email, phone, grade, section, user_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, students_with_userid)
        conn.commit()
        
        # Generate 20 teachers (reduced for faster startup)
        teachers_data = []
        teachers_user_data = []
        
        for i in range(20):
            first_name = random.choice(SL_FIRST_NAMES)
            last_name = random.choice(SL_LAST_NAMES)
            phone = generate_phone()
            username = generate_username(first_name, phone)
            email = f"teacher{i+1}@school.lk"
            subject = SUBJECTS[i % len(SUBJECTS)]
            password = hash_password("teacher123")
            
            teachers_user_data.append((username + f"T{i}", email, password, first_name, last_name, phone, 'teacher'))
            teachers_data.append((first_name, last_name, email, phone, subject))
        
        # Insert teacher users
        cursor.executemany("""
            INSERT INTO users (username, email, password, first_name, last_name, phone, role)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, teachers_user_data)
        conn.commit()
        
        # Get teacher user IDs
        cursor.execute("SELECT id, email FROM users WHERE role = 'teacher' ORDER BY id")
        teacher_user_map = {row[1]: row[0] for row in cursor.fetchall()}
        
        # Insert teachers with user_id
        teachers_with_userid = []
        for teacher in teachers_data:
            user_id = teacher_user_map.get(teacher[2])
            teachers_with_userid.append(teacher + (user_id,))
        
        cursor.executemany("""
            INSERT INTO teachers (first_name, last_name, email, phone, subject, user_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, teachers_with_userid)
        conn.commit()
        
        # Generate marks for all students
        cursor.execute("SELECT id FROM students")
        student_ids = [row[0] for row in cursor.fetchall()]
        
        marks_data = []
        for student_id in student_ids:
            for subject in SUBJECTS:
                # Generate realistic marks
                base_performance = random.uniform(30, 90)
                for term in range(1, 4):
                    variation = random.uniform(-10, 10)
                    marks = max(0, min(100, base_performance + variation + (term * 2)))  # Slight improvement trend
                    marks_data.append((student_id, subject, term, int(round(marks))))
        
        cursor.executemany("""
            INSERT INTO marks (student_id, subject, term, marks)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE marks = VALUES(marks)
        """, marks_data)
        conn.commit()
        
        # Generate attendance
        attendance_data = []
        today = datetime.now().date()
        for student_id in student_ids[:50]:  # Sample attendance for first 50 students
            for days_ago in range(30):
                date = today - timedelta(days=days_ago)
                if date.weekday() < 5:  # Only weekdays
                    status = random.choices(['present', 'absent', 'late'], weights=[85, 10, 5])[0]
                    attendance_data.append((student_id, date, status))
        
        cursor.executemany("""
            INSERT INTO attendance (student_id, date, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status)
        """, attendance_data)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        # Calculate predictions
        calculate_all_predictions()
        
        logging.info("Seed data generated successfully")
        return True
    except Exception as e:
        logging.error(f"Seed data error: {e}")
        return False

def calculate_prediction(term1_marks: float, term2_marks: float) -> float:
    """Use linear regression to predict Term 3 marks"""
    if term1_marks is None or term2_marks is None:
        return None
    
    # Simple linear regression with 2 points
    X = np.array([[1], [2]])
    y = np.array([term1_marks, term2_marks])
    
    model = LinearRegression()
    model.fit(X, y)
    
    # Predict term 3
    predicted = model.predict([[3]])[0]
    return int(max(0, min(100, round(predicted))))

def calculate_all_predictions():
    """Calculate predictions for all students"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get all students with their marks
        cursor.execute("""
            SELECT s.id as student_id, m.subject, m.term, m.marks
            FROM students s
            LEFT JOIN marks m ON s.id = m.student_id
            ORDER BY s.id, m.subject, m.term
        """)
        
        rows = cursor.fetchall()
        
        # Group by student and subject
        predictions = {}
        for row in rows:
            if row['subject']:
                key = (row['student_id'], row['subject'])
                if key not in predictions:
                    predictions[key] = {}
                predictions[key][row['term']] = row['marks']
        
        # Calculate predictions
        prediction_data = []
        for (student_id, subject), terms in predictions.items():
            term1 = terms.get(1)
            term2 = terms.get(2)
            if term1 is not None and term2 is not None:
                predicted = calculate_prediction(term1, term2)
                if predicted is not None:
                    is_at_risk = bool(predicted < 35)  # Convert to Python bool
                    prediction_data.append((student_id, subject, float(predicted), is_at_risk))
        
        # Insert predictions
        cursor.executemany("""
            INSERT INTO predictions (student_id, subject, predicted_term3, is_at_risk)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                predicted_term3 = VALUES(predicted_term3),
                is_at_risk = VALUES(is_at_risk),
                calculated_at = CURRENT_TIMESTAMP
        """, prediction_data)
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        logging.error(f"Prediction calculation error: {e}")

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Student Performance Management System API"}

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(user_login: UserLogin):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, username, email, password, first_name, last_name, phone, role
            FROM users WHERE email = %s OR username = %s
        """, (user_login.email, user_login.email))
        
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user or not verify_password(user_login.password, user['password']):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        token = create_access_token({
            "sub": str(user['id']),
            "email": user['email'],
            "role": user['role']
        })
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user['id'],
                "username": user['username'],
                "email": user['email'],
                "first_name": user['first_name'],
                "last_name": user['last_name'],
                "role": user['role']
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@api_router.get("/auth/me")
async def get_current_user(token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, username, email, first_name, last_name, phone, role
            FROM users WHERE id = %s
        """, (token_data['sub'],))
        
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Get user error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user")

# Dashboard Stats
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get total counts
        cursor.execute("SELECT COUNT(*) as count FROM students")
        total_students = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM teachers")
        total_teachers = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM predictions WHERE is_at_risk = TRUE")
        at_risk_students = cursor.fetchone()['count']
        
        # Get average marks by subject
        cursor.execute("""
            SELECT subject, AVG(marks) as avg_marks
            FROM marks WHERE term = 3
            GROUP BY subject
        """)
        subject_averages = cursor.fetchall()
        
        # Get grade distribution with streams for Grade 12 & 13
        cursor.execute("""
            SELECT 
                grade,
                stream,
                COUNT(*) as count
            FROM students
            GROUP BY grade, stream
            ORDER BY 
                CASE 
                    WHEN grade = 'Grade 1' THEN 1
                    WHEN grade = 'Grade 2' THEN 2
                    WHEN grade = 'Grade 3' THEN 3
                    WHEN grade = 'Grade 4' THEN 4
                    WHEN grade = 'Grade 5' THEN 5
                    WHEN grade = 'Grade 6' THEN 6
                    WHEN grade = 'Grade 7' THEN 7
                    WHEN grade = 'Grade 8' THEN 8
                    WHEN grade = 'Grade 9' THEN 9
                    WHEN grade = 'Grade 10' THEN 10
                    WHEN grade = 'Grade 11' THEN 11
                    WHEN grade = 'Grade 12' THEN 12
                    WHEN grade = 'Grade 13' THEN 13
                    ELSE 99
                END,
                stream
        """)
        raw_distribution = cursor.fetchall()
        
        # Process grade distribution - combine grades without streams, separate streams for 12 & 13
        grade_distribution = []
        for row in raw_distribution:
            grade = row['grade']
            stream = row['stream']
            count = row['count']
            
            if grade in ['Grade 12', 'Grade 13'] and stream:
                grade_distribution.append({
                    'grade': f"{grade} - {stream}",
                    'count': count
                })
            else:
                # Check if this grade already exists in distribution
                existing = next((g for g in grade_distribution if g['grade'] == grade), None)
                if existing:
                    existing['count'] += count
                else:
                    grade_distribution.append({
                        'grade': grade,
                        'count': count
                    })
        
        # Get recent attendance rate
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN status = 'present' THEN 1 END) * 100.0 / COUNT(*) as attendance_rate
            FROM attendance
            WHERE date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        """)
        result = cursor.fetchone()
        attendance_rate = round(result['attendance_rate'], 1) if result['attendance_rate'] else 0
        
        cursor.close()
        conn.close()
        
        return {
            "total_students": total_students,
            "total_teachers": total_teachers,
            "at_risk_students": at_risk_students,
            "attendance_rate": attendance_rate,
            "subject_averages": subject_averages,
            "grade_distribution": grade_distribution
        }
    except Exception as e:
        logging.error(f"Dashboard stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard stats")

# Students CRUD
@api_router.get("/students")
async def get_students(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str = None,
    grade: str = None,
    section: str = None,
    at_risk: bool = None,
    token_data: dict = Depends(verify_token)
):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        where_clauses = []
        params = []
        
        if search:
            where_clauses.append("(s.first_name LIKE %s OR s.last_name LIKE %s OR s.index_no LIKE %s)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        
        if grade:
            where_clauses.append("s.grade = %s")
            params.append(grade)
        
        if section:
            where_clauses.append("s.section = %s")
            params.append(section)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Get total count
        cursor.execute(f"SELECT COUNT(*) as count FROM students s WHERE {where_sql}", params)
        total = cursor.fetchone()['count']
        
        offset = (page - 1) * limit
        
        # Get students with risk status
        cursor.execute(f"""
            SELECT 
                s.*,
                COALESCE(MAX(p.is_at_risk), FALSE) as is_at_risk,
                GROUP_CONCAT(DISTINCT CASE WHEN p.is_at_risk THEN p.subject END) as at_risk_subjects
            FROM students s
            LEFT JOIN predictions p ON s.id = p.student_id
            WHERE {where_sql}
            GROUP BY s.id
            {"HAVING is_at_risk = TRUE" if at_risk else ""}
            ORDER BY s.index_no
            LIMIT %s OFFSET %s
        """, params + [limit, offset])
        
        students = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "students": students,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    except Exception as e:
        logging.error(f"Get students error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get students")

@api_router.get("/students/{student_id}")
async def get_student(student_id: int, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
        student = cursor.fetchone()
        
        if not student:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Get marks
        cursor.execute("""
            SELECT subject, term, marks FROM marks WHERE student_id = %s
            ORDER BY subject, term
        """, (student_id,))
        marks = cursor.fetchall()
        
        # Get predictions
        cursor.execute("""
            SELECT subject, predicted_term3, is_at_risk FROM predictions WHERE student_id = %s
        """, (student_id,))
        predictions = cursor.fetchall()
        
        # Get attendance
        cursor.execute("""
            SELECT date, status FROM attendance WHERE student_id = %s
            ORDER BY date DESC LIMIT 30
        """, (student_id,))
        attendance = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            **student,
            "marks": marks,
            "predictions": predictions,
            "attendance": attendance
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Get student error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get student")

@api_router.post("/students")
async def create_student(student: StudentCreate, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Create user account for student
        username = generate_username(student.first_name, student.phone)
        password = hash_password("student123")
        
        cursor.execute("""
            INSERT INTO users (username, email, password, first_name, last_name, phone, role)
            VALUES (%s, %s, %s, %s, %s, %s, 'student')
        """, (username, student.email, password, student.first_name, student.last_name, student.phone))
        
        user_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO students (index_no, first_name, last_name, email, phone, grade, section, user_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (student.index_no, student.first_name, student.last_name, student.email, 
              student.phone, student.grade, student.section, user_id))
        
        student_id = cursor.lastrowid
        conn.commit()
        
        cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
        new_student = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return new_student
    except Exception as e:
        logging.error(f"Create student error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create student")

@api_router.put("/students/{student_id}")
async def update_student(student_id: int, student: StudentUpdate, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        update_fields = []
        params = []
        
        for field, value in student.model_dump(exclude_none=True).items():
            update_fields.append(f"{field} = %s")
            params.append(value)
        
        if update_fields:
            params.append(student_id)
            cursor.execute(f"""
                UPDATE students SET {', '.join(update_fields)} WHERE id = %s
            """, params)
            conn.commit()
        
        cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
        updated_student = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return updated_student
    except Exception as e:
        logging.error(f"Update student error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update student")

@api_router.delete("/students/{student_id}")
async def delete_student(student_id: int, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "Student deleted successfully"}
    except Exception as e:
        logging.error(f"Delete student error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete student")

# Teachers CRUD
@api_router.get("/teachers")
async def get_teachers(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str = None,
    subject: str = None,
    token_data: dict = Depends(verify_token)
):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        where_clauses = []
        params = []
        
        if search:
            where_clauses.append("(first_name LIKE %s OR last_name LIKE %s OR email LIKE %s)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        
        if subject:
            where_clauses.append("subject = %s")
            params.append(subject)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        cursor.execute(f"SELECT COUNT(*) as count FROM teachers WHERE {where_sql}", params)
        total = cursor.fetchone()['count']
        
        offset = (page - 1) * limit
        
        cursor.execute(f"""
            SELECT * FROM teachers WHERE {where_sql}
            ORDER BY first_name, last_name
            LIMIT %s OFFSET %s
        """, params + [limit, offset])
        
        teachers = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "teachers": teachers,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    except Exception as e:
        logging.error(f"Get teachers error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get teachers")

@api_router.get("/teachers/{teacher_id}")
async def get_teacher(teacher_id: int, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM teachers WHERE id = %s", (teacher_id,))
        teacher = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")
        
        return teacher
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Get teacher error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get teacher")

@api_router.post("/teachers")
async def create_teacher(teacher: TeacherCreate, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Create user account for teacher
        username = generate_username(teacher.first_name, teacher.phone)
        password = hash_password("teacher123")
        
        cursor.execute("""
            INSERT INTO users (username, email, password, first_name, last_name, phone, role)
            VALUES (%s, %s, %s, %s, %s, %s, 'teacher')
        """, (username, teacher.email, password, teacher.first_name, teacher.last_name, teacher.phone))
        
        user_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO teachers (first_name, last_name, email, phone, subject, user_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (teacher.first_name, teacher.last_name, teacher.email, teacher.phone, teacher.subject, user_id))
        
        teacher_id = cursor.lastrowid
        conn.commit()
        
        cursor.execute("SELECT * FROM teachers WHERE id = %s", (teacher_id,))
        new_teacher = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return new_teacher
    except Exception as e:
        logging.error(f"Create teacher error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create teacher")

@api_router.put("/teachers/{teacher_id}")
async def update_teacher(teacher_id: int, teacher: TeacherUpdate, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        update_fields = []
        params = []
        
        for field, value in teacher.model_dump(exclude_none=True).items():
            update_fields.append(f"{field} = %s")
            params.append(value)
        
        if update_fields:
            params.append(teacher_id)
            cursor.execute(f"""
                UPDATE teachers SET {', '.join(update_fields)} WHERE id = %s
            """, params)
            conn.commit()
        
        cursor.execute("SELECT * FROM teachers WHERE id = %s", (teacher_id,))
        updated_teacher = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return updated_teacher
    except Exception as e:
        logging.error(f"Update teacher error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update teacher")

@api_router.delete("/teachers/{teacher_id}")
async def delete_teacher(teacher_id: int, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM teachers WHERE id = %s", (teacher_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "Teacher deleted successfully"}
    except Exception as e:
        logging.error(f"Delete teacher error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete teacher")

# Marks
@api_router.get("/marks")
async def get_marks(
    student_id: int = None,
    subject: str = None,
    term: int = None,
    token_data: dict = Depends(verify_token)
):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        where_clauses = []
        params = []
        
        if student_id:
            where_clauses.append("m.student_id = %s")
            params.append(student_id)
        
        if subject:
            where_clauses.append("m.subject = %s")
            params.append(subject)
        
        if term:
            where_clauses.append("m.term = %s")
            params.append(term)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        cursor.execute(f"""
            SELECT m.*, s.index_no, s.first_name, s.last_name, s.grade, s.section
            FROM marks m
            JOIN students s ON m.student_id = s.id
            WHERE {where_sql}
            ORDER BY s.index_no, m.subject, m.term
        """, params)
        
        marks = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return marks
    except Exception as e:
        logging.error(f"Get marks error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get marks")

@api_router.post("/marks")
async def save_marks(mark: MarkEntry, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            INSERT INTO marks (student_id, subject, term, marks, entered_by)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE marks = VALUES(marks), entered_by = VALUES(entered_by)
        """, (mark.student_id, mark.subject, mark.term, mark.marks, token_data['sub']))
        
        conn.commit()
        
        # Recalculate prediction for this student/subject
        cursor.execute("""
            SELECT term, marks FROM marks 
            WHERE student_id = %s AND subject = %s
            ORDER BY term
        """, (mark.student_id, mark.subject))
        
        term_marks = {row['term']: row['marks'] for row in cursor.fetchall()}
        
        if 1 in term_marks and 2 in term_marks:
            predicted = calculate_prediction(term_marks[1], term_marks[2])
            is_at_risk = predicted < 35
            
            cursor.execute("""
                INSERT INTO predictions (student_id, subject, predicted_term3, is_at_risk)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    predicted_term3 = VALUES(predicted_term3),
                    is_at_risk = VALUES(is_at_risk),
                    calculated_at = CURRENT_TIMESTAMP
            """, (mark.student_id, mark.subject, predicted, is_at_risk))
            conn.commit()
        
        cursor.close()
        conn.close()
        
        return {"message": "Marks saved successfully"}
    except Exception as e:
        logging.error(f"Save marks error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save marks")

@api_router.post("/marks/bulk")
async def save_bulk_marks(marks: List[MarkEntry], token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor()
        
        marks_data = [(m.student_id, m.subject, m.term, m.marks, token_data['sub']) for m in marks]
        
        cursor.executemany("""
            INSERT INTO marks (student_id, subject, term, marks, entered_by)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE marks = VALUES(marks), entered_by = VALUES(entered_by)
        """, marks_data)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Recalculate all predictions
        calculate_all_predictions()
        
        return {"message": f"Saved {len(marks)} marks successfully"}
    except Exception as e:
        logging.error(f"Bulk marks error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save marks")

# Attendance
@api_router.get("/attendance")
async def get_attendance(
    student_id: int = None,
    date: str = None,
    grade: str = None,
    section: str = None,
    token_data: dict = Depends(verify_token)
):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        where_clauses = []
        params = []
        
        if student_id:
            where_clauses.append("a.student_id = %s")
            params.append(student_id)
        
        if date:
            where_clauses.append("a.date = %s")
            params.append(date)
        
        if grade:
            where_clauses.append("s.grade = %s")
            params.append(grade)
        
        if section:
            where_clauses.append("s.section = %s")
            params.append(section)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        cursor.execute(f"""
            SELECT a.*, s.index_no, s.first_name, s.last_name, s.grade, s.section
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            WHERE {where_sql}
            ORDER BY a.date DESC, s.index_no
            LIMIT 1000
        """, params)
        
        attendance = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return attendance
    except Exception as e:
        logging.error(f"Get attendance error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get attendance")

@api_router.post("/attendance")
async def save_attendance(entry: AttendanceEntry, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO attendance (student_id, date, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status)
        """, (entry.student_id, entry.date, entry.status))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "Attendance saved successfully"}
    except Exception as e:
        logging.error(f"Save attendance error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save attendance")

@api_router.post("/attendance/bulk")
async def save_bulk_attendance(entries: List[AttendanceEntry], token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor()
        
        attendance_data = [(e.student_id, e.date, e.status) for e in entries]
        
        cursor.executemany("""
            INSERT INTO attendance (student_id, date, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status)
        """, attendance_data)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": f"Saved {len(entries)} attendance records successfully"}
    except Exception as e:
        logging.error(f"Bulk attendance error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save attendance")

# Predictions
@api_router.get("/predictions")
async def get_predictions(
    at_risk_only: bool = False,
    subject: str = None,
    grade: str = None,
    token_data: dict = Depends(verify_token)
):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        where_clauses = []
        params = []
        
        if at_risk_only:
            where_clauses.append("p.is_at_risk = TRUE")
        
        if subject:
            where_clauses.append("p.subject = %s")
            params.append(subject)
        
        if grade:
            where_clauses.append("s.grade = %s")
            params.append(grade)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        cursor.execute(f"""
            SELECT p.*, s.index_no, s.first_name, s.last_name, s.grade, s.section
            FROM predictions p
            JOIN students s ON p.student_id = s.id
            WHERE {where_sql}
            ORDER BY p.predicted_term3 ASC
        """, params)
        
        predictions = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return predictions
    except Exception as e:
        logging.error(f"Get predictions error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get predictions")

@api_router.post("/predictions/recalculate")
async def recalculate_predictions(token_data: dict = Depends(verify_token)):
    calculate_all_predictions()
    return {"message": "Predictions recalculated successfully"}

# At-Risk Students
@api_router.get("/at-risk-students")
async def get_at_risk_students(
    grade: str = None,
    section: str = None,
    subject: str = None,
    token_data: dict = Depends(verify_token)
):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        where_clauses = ["p.is_at_risk = TRUE"]
        params = []
        
        if grade:
            where_clauses.append("s.grade = %s")
            params.append(grade)
        
        if section:
            where_clauses.append("s.section = %s")
            params.append(section)
        
        if subject:
            where_clauses.append("p.subject = %s")
            params.append(subject)
        
        where_sql = " AND ".join(where_clauses)
        
        cursor.execute(f"""
            SELECT 
                s.id, s.index_no, s.first_name, s.last_name, s.grade, s.section, s.phone, s.email,
                p.subject, p.predicted_term3,
                (SELECT marks FROM marks WHERE student_id = s.id AND subject = p.subject AND term = 1) as term1_marks,
                (SELECT marks FROM marks WHERE student_id = s.id AND subject = p.subject AND term = 2) as term2_marks
            FROM predictions p
            JOIN students s ON p.student_id = s.id
            WHERE {where_sql}
            ORDER BY p.predicted_term3 ASC, s.index_no
        """, params)
        
        at_risk = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return at_risk
    except Exception as e:
        logging.error(f"Get at-risk students error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get at-risk students")

# Bulk Import
@api_router.post("/import/students")
async def import_students(data: BulkStudentImport, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor()
        imported = 0
        errors = []
        
        for student in data.students:
            try:
                username = generate_username(student.first_name, student.phone)
                password = hash_password("student123")
                
                cursor.execute("""
                    INSERT INTO users (username, email, password, first_name, last_name, phone, role)
                    VALUES (%s, %s, %s, %s, %s, %s, 'student')
                """, (username, student.email, password, student.first_name, student.last_name, student.phone))
                
                user_id = cursor.lastrowid
                
                cursor.execute("""
                    INSERT INTO students (index_no, first_name, last_name, email, phone, grade, section, user_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (student.index_no, student.first_name, student.last_name, student.email,
                      student.phone, student.grade, student.section, user_id))
                
                imported += 1
            except Exception as e:
                errors.append(f"Error importing {student.index_no}: {str(e)}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"imported": imported, "errors": errors}
    except Exception as e:
        logging.error(f"Import students error: {e}")
        raise HTTPException(status_code=500, detail="Failed to import students")

@api_router.post("/import/teachers")
async def import_teachers(data: BulkTeacherImport, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor()
        imported = 0
        errors = []
        
        for teacher in data.teachers:
            try:
                username = generate_username(teacher.first_name, teacher.phone)
                password = hash_password("teacher123")
                
                cursor.execute("""
                    INSERT INTO users (username, email, password, first_name, last_name, phone, role)
                    VALUES (%s, %s, %s, %s, %s, %s, 'teacher')
                """, (username, teacher.email, password, teacher.first_name, teacher.last_name, teacher.phone))
                
                user_id = cursor.lastrowid
                
                cursor.execute("""
                    INSERT INTO teachers (first_name, last_name, email, phone, subject, user_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (teacher.first_name, teacher.last_name, teacher.email, teacher.phone, teacher.subject, user_id))
                
                imported += 1
            except Exception as e:
                errors.append(f"Error importing {teacher.email}: {str(e)}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"imported": imported, "errors": errors}
    except Exception as e:
        logging.error(f"Import teachers error: {e}")
        raise HTTPException(status_code=500, detail="Failed to import teachers")

# Export Reports
@api_router.get("/export/students/pdf")
async def export_students_pdf(
    grade: str = None,
    section: str = None,
    token_data: dict = Depends(verify_token)
):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        where_clauses = []
        params = []
        
        if grade:
            where_clauses.append("grade = %s")
            params.append(grade)
        
        if section:
            where_clauses.append("section = %s")
            params.append(section)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        cursor.execute(f"""
            SELECT index_no, first_name, last_name, email, phone, grade, section
            FROM students WHERE {where_sql}
            ORDER BY index_no
        """, params)
        
        students = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Generate PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        
        styles = getSampleStyleSheet()
        elements.append(Paragraph("Student Report", styles['Title']))
        elements.append(Spacer(1, 20))
        
        # Table data
        data = [['Index No', 'Name', 'Email', 'Phone', 'Grade', 'Section']]
        for s in students:
            data.append([
                s['index_no'],
                f"{s['first_name']} {s['last_name']}",
                s['email'],
                s['phone'],
                s['grade'],
                s['section']
            ])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0ea5e9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        buffer.seek(0)
        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=students_report.pdf"}
        )
    except Exception as e:
        logging.error(f"Export PDF error: {e}")
        raise HTTPException(status_code=500, detail="Failed to export PDF")

@api_router.get("/export/students/excel")
async def export_students_excel(
    grade: str = None,
    section: str = None,
    token_data: dict = Depends(verify_token)
):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        where_clauses = []
        params = []
        
        if grade:
            where_clauses.append("grade = %s")
            params.append(grade)
        
        if section:
            where_clauses.append("section = %s")
            params.append(section)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        cursor.execute(f"""
            SELECT index_no, first_name, last_name, email, phone, grade, section
            FROM students WHERE {where_sql}
            ORDER BY index_no
        """, params)
        
        students = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Generate Excel
        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffer)
        worksheet = workbook.add_worksheet('Students')
        
        # Header format
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#0ea5e9',
            'font_color': 'white',
            'border': 1
        })
        
        # Headers
        headers = ['Index No', 'First Name', 'Last Name', 'Email', 'Phone', 'Grade', 'Section']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Data
        for row, student in enumerate(students, 1):
            worksheet.write(row, 0, student['index_no'])
            worksheet.write(row, 1, student['first_name'])
            worksheet.write(row, 2, student['last_name'])
            worksheet.write(row, 3, student['email'])
            worksheet.write(row, 4, student['phone'])
            worksheet.write(row, 5, student['grade'])
            worksheet.write(row, 6, student['section'])
        
        workbook.close()
        buffer.seek(0)
        
        return Response(
            content=buffer.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=students_report.xlsx"}
        )
    except Exception as e:
        logging.error(f"Export Excel error: {e}")
        raise HTTPException(status_code=500, detail="Failed to export Excel")

@api_router.get("/export/performance/pdf/{student_id}")
async def export_student_performance_pdf(student_id: int, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get student details
        cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
        student = cursor.fetchone()
        
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Get marks
        cursor.execute("""
            SELECT subject, term, marks FROM marks 
            WHERE student_id = %s ORDER BY subject, term
        """, (student_id,))
        marks = cursor.fetchall()
        
        # Get predictions
        cursor.execute("""
            SELECT subject, predicted_term3, is_at_risk FROM predictions 
            WHERE student_id = %s
        """, (student_id,))
        predictions = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Generate PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        
        styles = getSampleStyleSheet()
        elements.append(Paragraph("Student Performance Report", styles['Title']))
        elements.append(Spacer(1, 20))
        
        # Student info
        elements.append(Paragraph(f"<b>Index No:</b> {student['index_no']}", styles['Normal']))
        elements.append(Paragraph(f"<b>Name:</b> {student['first_name']} {student['last_name']}", styles['Normal']))
        elements.append(Paragraph(f"<b>Grade:</b> {student['grade']} - {student['section']}", styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Marks table
        elements.append(Paragraph("<b>Term Marks</b>", styles['Heading2']))
        
        # Organize marks by subject
        marks_by_subject = {}
        for m in marks:
            if m['subject'] not in marks_by_subject:
                marks_by_subject[m['subject']] = {}
            marks_by_subject[m['subject']][m['term']] = m['marks']
        
        # Get predictions by subject
        pred_by_subject = {p['subject']: p for p in predictions}
        
        data = [['Subject', 'Term 1', 'Term 2', 'Term 3', 'Predicted', 'Status']]
        for subject in ['Maths', 'Science', 'English', 'Tamil', 'ICT']:
            term_marks = marks_by_subject.get(subject, {})
            pred = pred_by_subject.get(subject, {})
            status = 'At Risk' if pred.get('is_at_risk') else 'On Track'
            data.append([
                subject,
                term_marks.get(1, '-'),
                term_marks.get(2, '-'),
                term_marks.get(3, '-'),
                pred.get('predicted_term3', '-'),
                status
            ])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0ea5e9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        buffer.seek(0)
        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={student['index_no']}_performance.pdf"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Export performance PDF error: {e}")
        raise HTTPException(status_code=500, detail="Failed to export PDF")

# Dropdown data
@api_router.get("/dropdown/grades")
async def get_grades():
    return GRADES

@api_router.get("/dropdown/sections")
async def get_sections():
    return SECTIONS

@api_router.get("/dropdown/subjects")
async def get_subjects():
    return SUBJECTS

# Student Dashboard API
@api_router.get("/student/dashboard")
async def get_student_dashboard(token_data: dict = Depends(verify_token)):
    if token_data['role'] != 'student':
        raise HTTPException(status_code=403, detail="Access denied")
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get student by user_id
        cursor.execute("""
            SELECT * FROM students WHERE user_id = %s
        """, (token_data['sub'],))
        student = cursor.fetchone()
        
        if not student:
            raise HTTPException(status_code=404, detail="Student record not found")
        
        # Get marks
        cursor.execute("""
            SELECT subject, term, marks FROM marks WHERE student_id = %s
            ORDER BY subject, term
        """, (student['id'],))
        marks = cursor.fetchall()
        
        # Get predictions
        cursor.execute("""
            SELECT subject, predicted_term3, is_at_risk FROM predictions WHERE student_id = %s
        """, (student['id'],))
        predictions = cursor.fetchall()
        
        # Get attendance summary
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present,
                SUM(CASE WHEN status = 'absent' THEN 1 ELSE 0 END) as absent,
                SUM(CASE WHEN status = 'late' THEN 1 ELSE 0 END) as late
            FROM attendance WHERE student_id = %s
        """, (student['id'],))
        attendance = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return {
            "student": student,
            "marks": marks,
            "predictions": predictions,
            "attendance": attendance
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Student dashboard error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard")

# Teacher Dashboard API
@api_router.get("/teacher/dashboard")
async def get_teacher_dashboard(token_data: dict = Depends(verify_token)):
    if token_data['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Access denied")
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get teacher info
        cursor.execute("""
            SELECT * FROM teachers WHERE user_id = %s
        """, (token_data['sub'],))
        teacher = cursor.fetchone()
        
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher record not found")
        
        # Get at-risk students for teacher's subject
        cursor.execute("""
            SELECT 
                s.id, s.index_no, s.first_name, s.last_name, s.grade, s.section,
                p.predicted_term3, p.is_at_risk
            FROM predictions p
            JOIN students s ON p.student_id = s.id
            WHERE p.subject = %s AND p.is_at_risk = TRUE
            ORDER BY p.predicted_term3 ASC
            LIMIT 50
        """, (teacher['subject'],))
        at_risk = cursor.fetchall()
        
        # Get class performance stats
        cursor.execute("""
            SELECT 
                s.grade,
                COUNT(DISTINCT s.id) as total_students,
                AVG(m.marks) as avg_marks,
                SUM(CASE WHEN p.is_at_risk THEN 1 ELSE 0 END) as at_risk_count
            FROM students s
            LEFT JOIN marks m ON s.id = m.student_id AND m.subject = %s
            LEFT JOIN predictions p ON s.id = p.student_id AND p.subject = %s
            GROUP BY s.grade
        """, (teacher['subject'], teacher['subject']))
        class_stats = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "teacher": teacher,
            "at_risk_students": at_risk,
            "class_stats": class_stats
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Teacher dashboard error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard")

# Student Performance API for Worksheets Page
@api_router.get("/class-students/performance")
async def get_students_with_performance(
    grade: str = Query(...),
    section: str = Query(...),
    term: str = Query(...),
    subject: str = Query(...),
    token_data: dict = Depends(verify_token)
):
    """Get students in a class with their marks and performance levels"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        term_int = int(term)
        
        # Get students with their marks for the specified term and subject
        cursor.execute("""
            SELECT
                s.id, s.index_no, s.first_name, s.last_name, s.phone,
                CAST(ROUND(COALESCE(m.marks, 0)) AS SIGNED) as marks,
                CAST(ROUND(COALESCE(p.predicted_term3, 0)) AS SIGNED) as predicted,
                sn.id as note_id,
                sn.note,
                sn.file_name as worksheet_file,
                sn.downloaded_at,
                sn.submission_file_name
            FROM students s
            LEFT JOIN marks m ON s.id = m.student_id AND m.subject = %s AND m.term = %s
            LEFT JOIN predictions p ON s.id = p.student_id AND p.subject = %s
            LEFT JOIN student_notes sn ON s.id = sn.student_id AND sn.subject = %s AND sn.term = %s
            WHERE s.grade = %s AND s.section = %s
            ORDER BY s.index_no
        """, (subject, term_int, subject, subject, term_int, grade, section))
        
        students = cursor.fetchall()
        cursor.close()
        conn.close()

        for s in students:
            if s.get('downloaded_at'):
                s['downloaded_at'] = s['downloaded_at'].isoformat()

        return {"students": students}
    except Exception as e:
        logging.error(f"Get students performance error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get students")

@api_router.post("/class-students/worksheet")
async def upload_common_worksheet(
    grade: str = Form(...),
    section: str = Form(...),
    term: str = Form(...),
    subject: str = Form(...),
    file: UploadFile = File(...),
    token_data: dict = Depends(verify_token)
):
    """Upload one worksheet file for all students in a class"""
    if token_data['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Only teachers can upload worksheets")

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)
        term_int = int(term)

        cursor.execute(
            "SELECT id FROM students WHERE grade = %s AND section = %s ORDER BY index_no",
            (grade, section)
        )
        students = cursor.fetchall()

        if not students:
            raise HTTPException(status_code=404, detail="No students found for this class")

        # Save the file once, shared across all students
        upload_dir = "/app/uploads/student_worksheets"
        os.makedirs(upload_dir, exist_ok=True)

        file_name = file.filename
        safe_grade = grade.replace(' ', '_')
        file_path = f"{upload_dir}/common_{safe_grade}_{section}_{term}_{subject}_{file_name}"

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        for student in students:
            cursor.execute("""
                INSERT INTO student_notes (student_id, teacher_id, subject, term, note, file_path, file_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    file_path = VALUES(file_path),
                    file_name = VALUES(file_name),
                    updated_at = CURRENT_TIMESTAMP
            """, (student['id'], token_data['sub'], subject, term_int, "", file_path, file_name))

        conn.commit()
        cursor.close()
        conn.close()

        return {"message": f"Worksheet uploaded for {len(students)} students", "count": len(students), "file_name": file_name}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Common worksheet upload error: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload worksheet")

# Student Notes API
class StudentNoteCreate(BaseModel):
    note: str
    term: int
    subject: str

@api_router.post("/students/{student_id}/notes")
async def save_student_note(
    student_id: int,
    note_data: StudentNoteCreate,
    token_data: dict = Depends(verify_token)
):
    """Save a note for a specific student"""
    if token_data['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Only teachers can add notes")
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor()
        
        # Use REPLACE to insert or update
        cursor.execute("""
            REPLACE INTO student_notes (student_id, teacher_id, subject, term, note)
            VALUES (%s, %s, %s, %s, %s)
        """, (student_id, token_data['sub'], note_data.subject, note_data.term, note_data.note))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "Note saved successfully"}
    except Exception as e:
        logging.error(f"Save student note error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save note")

# Student Worksheet Upload API (individual per student)
@api_router.post("/students/{student_id}/worksheet")
async def save_student_worksheet(
    student_id: int,
    note: str = Form(""),
    term: str = Form(...),
    subject: str = Form(...),
    file: UploadFile = File(None),
    token_data: dict = Depends(verify_token)
):
    """Save note and/or worksheet file for a specific student"""
    if token_data['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Only teachers can upload worksheets")
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor()
        term_int = int(term)
        
        file_path = None
        file_name = None
        
        # Handle file upload
        if file and file.filename:
            upload_dir = "/app/uploads/student_worksheets"
            os.makedirs(upload_dir, exist_ok=True)
            
            file_name = file.filename
            file_path = f"{upload_dir}/{student_id}_{term}_{subject}_{file.filename}"
            
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
        
        # Save or update note and file info
        cursor.execute("""
            INSERT INTO student_notes (student_id, teacher_id, subject, term, note, file_path, file_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                note = VALUES(note),
                file_path = COALESCE(VALUES(file_path), file_path),
                file_name = COALESCE(VALUES(file_name), file_name),
                updated_at = CURRENT_TIMESTAMP
        """, (student_id, token_data['sub'], subject, term_int, note, file_path, file_name))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "Saved successfully", "file_uploaded": file_name is not None}
    except Exception as e:
        logging.error(f"Save student worksheet error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save")

class BulkNoteItem(BaseModel):
    student_id: int
    note: str
    term: int
    subject: str

@api_router.post("/students/notes/bulk")
async def save_bulk_notes(
    notes: List[BulkNoteItem],
    token_data: dict = Depends(verify_token)
):
    """Save multiple student notes at once"""
    if token_data['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Only teachers can add notes")
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor()
        
        for note_item in notes:
            cursor.execute("""
                REPLACE INTO student_notes (student_id, teacher_id, subject, term, note)
                VALUES (%s, %s, %s, %s, %s)
            """, (note_item.student_id, token_data['sub'], note_item.subject, note_item.term, note_item.note))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": f"Saved {len(notes)} notes successfully"}
    except Exception as e:
        logging.error(f"Save bulk notes error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save notes")

# Student Worksheet Download/Submit APIs
@api_router.get("/student/worksheets")
async def get_student_worksheets(token_data: dict = Depends(verify_token)):
    """Get all worksheets assigned to the logged-in student by teachers"""
    if token_data['role'] != 'student':
        raise HTTPException(status_code=403, detail="Access denied")

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id FROM students WHERE user_id = %s
        """, (token_data['sub'],))
        student = cursor.fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        cursor.execute("""
            SELECT sn.id, sn.subject, sn.term, sn.note, sn.file_name, sn.file_path,
                   sn.submission_file_name, sn.updated_at
            FROM student_notes sn
            WHERE sn.student_id = %s AND sn.file_path IS NOT NULL
            ORDER BY sn.term, sn.subject
        """, (student['id'],))
        worksheets = cursor.fetchall()

        for w in worksheets:
            if w.get('updated_at'):
                w['updated_at'] = w['updated_at'].isoformat()

        cursor.close()
        conn.close()
        return {"worksheets": worksheets}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Get student worksheets error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get worksheets")


@api_router.get("/student/worksheets/{note_id}/download")
async def download_student_worksheet(note_id: int, token_data: dict = Depends(verify_token)):
    """Download a worksheet file assigned to the student"""
    if token_data['role'] != 'student':
        raise HTTPException(status_code=403, detail="Access denied")

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id FROM students WHERE user_id = %s", (token_data['sub'],))
        student = cursor.fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        cursor.execute("""
            SELECT file_path, file_name FROM student_notes
            WHERE id = %s AND student_id = %s AND file_path IS NOT NULL
        """, (note_id, student['id']))
        note = cursor.fetchone()

        if not note:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Worksheet not found")

        # Record that the student has downloaded the worksheet
        cursor.execute(
            "UPDATE student_notes SET downloaded_at = CURRENT_TIMESTAMP WHERE id = %s",
            (note_id,)
        )
        conn.commit()
        cursor.close()
        conn.close()

        from fastapi.responses import FileResponse
        return FileResponse(note['file_path'], filename=note['file_name'], media_type='application/octet-stream')
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Download student worksheet error: {e}")
        raise HTTPException(status_code=500, detail="Failed to download worksheet")


@api_router.post("/student/worksheets/{note_id}/submit")
async def submit_student_worksheet(
    note_id: int,
    file: UploadFile = File(...),
    token_data: dict = Depends(verify_token)
):
    """Upload a student's submission for a worksheet"""
    if token_data['role'] != 'student':
        raise HTTPException(status_code=403, detail="Access denied")

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id FROM students WHERE user_id = %s", (token_data['sub'],))
        student = cursor.fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        cursor.execute("""
            SELECT id FROM student_notes WHERE id = %s AND student_id = %s
        """, (note_id, student['id']))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Worksheet not found")

        upload_dir = "/app/uploads/student_submissions"
        os.makedirs(upload_dir, exist_ok=True)

        file_name = file.filename
        file_path = f"{upload_dir}/{student['id']}_{note_id}_{file_name}"

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        cursor.execute("""
            UPDATE student_notes SET submission_file_path = %s, submission_file_name = %s
            WHERE id = %s AND student_id = %s
        """, (file_path, file_name, note_id, student['id']))

        conn.commit()
        cursor.close()
        conn.close()

        return {"message": "Submission uploaded successfully", "file_name": file_name}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Submit student worksheet error: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload submission")

@api_router.get("/student-notes/{note_id}/submission/download")
async def download_student_submission(note_id: int, token_data: dict = Depends(verify_token)):
    """Teacher downloads a student's submitted worksheet"""
    if token_data['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Only teachers can access submissions")

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT sn.submission_file_path, sn.submission_file_name
            FROM student_notes sn
            WHERE sn.id = %s AND sn.submission_file_path IS NOT NULL
        """, (note_id,))
        note = cursor.fetchone()
        cursor.close()
        conn.close()

        if not note:
            raise HTTPException(status_code=404, detail="Submission not found")

        from fastapi.responses import FileResponse
        return FileResponse(note['submission_file_path'], filename=note['submission_file_name'], media_type='application/octet-stream')
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Download submission error: {e}")
        raise HTTPException(status_code=500, detail="Failed to download submission")

# Worksheets API
class WorksheetCreate(BaseModel):
    tier: str
    title: str
    description: str
    subject: str

@api_router.get("/worksheets")
async def get_worksheets(token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get teacher's subject if teacher role
        if token_data['role'] == 'teacher':
            cursor.execute("SELECT subject FROM teachers WHERE user_id = %s", (token_data['sub'],))
            teacher = cursor.fetchone()
            if teacher:
                cursor.execute("""
                    SELECT * FROM worksheets WHERE subject = %s
                    ORDER BY created_at DESC
                """, (teacher['subject'],))
            else:
                cursor.execute("SELECT * FROM worksheets ORDER BY created_at DESC")
        else:
            cursor.execute("SELECT * FROM worksheets ORDER BY created_at DESC")
        
        worksheets = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Convert datetime to string
        for w in worksheets:
            if w.get('created_at'):
                w['created_at'] = w['created_at'].isoformat()
        
        return worksheets
    except Exception as e:
        logging.error(f"Get worksheets error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get worksheets")

@api_router.post("/worksheets")
async def create_worksheet(
    tier: str = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    subject: str = Form(...),
    file: UploadFile = File(None),
    token_data: dict = Depends(verify_token)
):
    if token_data['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Only teachers can create worksheets")
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor()
        
        file_path = None
        file_name = None
        
        if file and file.filename:
            # Save file
            import os
            upload_dir = "/app/uploads/worksheets"
            os.makedirs(upload_dir, exist_ok=True)
            
            file_name = file.filename
            file_path = f"{upload_dir}/{token_data['sub']}_{file.filename}"
            
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
        
        cursor.execute("""
            INSERT INTO worksheets (teacher_id, subject, tier, title, description, file_path, file_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (token_data['sub'], subject, tier, title, description, file_path, file_name))
        
        conn.commit()
        worksheet_id = cursor.lastrowid
        cursor.close()
        conn.close()
        
        return {"id": worksheet_id, "message": "Worksheet created successfully"}
    except Exception as e:
        logging.error(f"Create worksheet error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create worksheet")

@api_router.delete("/worksheets/{worksheet_id}")
async def delete_worksheet(worksheet_id: int, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get worksheet to delete file
        cursor.execute("SELECT file_path FROM worksheets WHERE id = %s", (worksheet_id,))
        worksheet = cursor.fetchone()
        
        if worksheet and worksheet.get('file_path'):
            import os
            if os.path.exists(worksheet['file_path']):
                os.remove(worksheet['file_path'])
        
        cursor.execute("DELETE FROM worksheets WHERE id = %s", (worksheet_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "Worksheet deleted successfully"}
    except Exception as e:
        logging.error(f"Delete worksheet error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete worksheet")

@api_router.get("/worksheets/{worksheet_id}/download")
async def download_worksheet(worksheet_id: int, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT file_path, file_name FROM worksheets WHERE id = %s", (worksheet_id,))
        worksheet = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not worksheet or not worksheet.get('file_path'):
            raise HTTPException(status_code=404, detail="File not found")
        
        from fastapi.responses import FileResponse
        return FileResponse(
            worksheet['file_path'],
            filename=worksheet['file_name'],
            media_type='application/octet-stream'
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Download worksheet error: {e}")
        raise HTTPException(status_code=500, detail="Failed to download worksheet")

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

import asyncio
import threading

def run_seed_data_background():
    """Run seed_data in background thread"""
    try:
        seed_data()
        logger.info("Seed data completed")
    except Exception as e:
        logger.error(f"Seed data error: {e}")

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Student Performance Management System...")
    if init_database():
        logger.info("Database initialized successfully")
        # Run seed data in background thread
        thread = threading.Thread(target=run_seed_data_background)
        thread.daemon = True
        thread.start()
    else:
        logger.error("Failed to initialize database")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")
