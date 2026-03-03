#!/usr/bin/env python3
"""Seed script for 3500 students distributed across grades 1-13 with A/L streams"""

import random
import hashlib
import mysql.connector

# Sri Lankan names
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

GRADES = ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8", 
          "Grade 9", "Grade 10", "Grade 11", "Grade 12", "Grade 13"]
SECTIONS = ["A", "B", "C", "D"]
AL_STREAMS = ["Bio", "Maths", "Commerce", "Engineering Technology", "Bio Technology", "Arts"]
SUBJECTS = ["Maths", "Science", "English", "Tamil", "ICT"]

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_phone():
    return f"+947{random.randint(0, 9)}{random.randint(1000000, 9999999)}"

def generate_username(first_name, phone):
    return f"{first_name}{phone[-2:]}"

# Distribution: ~270 students per grade for grades 1-11, ~175 per stream for grades 12-13
# Total: 11 grades * 270 = 2970 + 6 streams * 2 grades * ~45 = 540 = 3510 (approx 3500)

GRADE_DISTRIBUTION = {
    "Grade 1": 270, "Grade 2": 270, "Grade 3": 270, "Grade 4": 270, "Grade 5": 270,
    "Grade 6": 270, "Grade 7": 270, "Grade 8": 270, "Grade 9": 270, "Grade 10": 270, "Grade 11": 270,
}
# For Grade 12 & 13, distribute across streams
AL_DISTRIBUTION = {
    "Grade 12": {"Bio": 40, "Maths": 45, "Commerce": 40, "Engineering Technology": 35, "Bio Technology": 30, "Arts": 40},
    "Grade 13": {"Bio": 40, "Maths": 45, "Commerce": 40, "Engineering Technology": 35, "Bio Technology": 30, "Arts": 40}
}

def main():
    print("Connecting to database...")
    conn = mysql.connector.connect(host='localhost', user='root', password='root', database='school_db')
    cursor = conn.cursor()
    
    # Clear existing data
    print("Clearing existing data...")
    cursor.execute("DELETE FROM predictions")
    cursor.execute("DELETE FROM attendance")
    cursor.execute("DELETE FROM marks")
    cursor.execute("DELETE FROM students")
    cursor.execute("DELETE FROM teachers")
    cursor.execute("DELETE FROM users WHERE role != 'admin'")
    conn.commit()
    
    student_index = 1
    students_data = []
    users_data = []
    
    # Generate students for grades 1-11
    print("Generating students for Grades 1-11...")
    for grade, count in GRADE_DISTRIBUTION.items():
        for i in range(count):
            first_name = random.choice(SL_FIRST_NAMES)
            last_name = random.choice(SL_LAST_NAMES)
            phone = generate_phone()
            username = generate_username(first_name, phone) + str(student_index)
            email = f"student{student_index}@school.lk"
            index_no = f"S{str(student_index).zfill(4)}"
            section = random.choice(SECTIONS)
            password = hash_password("student123")
            
            users_data.append((username, email, password, first_name, last_name, phone, 'student'))
            students_data.append({
                'index_no': index_no,
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'phone': phone,
                'grade': grade,
                'section': section,
                'stream': None
            })
            student_index += 1
    
    # Generate students for grades 12-13 with streams
    print("Generating students for Grades 12-13 with A/L streams...")
    for grade, streams in AL_DISTRIBUTION.items():
        for stream, count in streams.items():
            for i in range(count):
                first_name = random.choice(SL_FIRST_NAMES)
                last_name = random.choice(SL_LAST_NAMES)
                phone = generate_phone()
                username = generate_username(first_name, phone) + str(student_index)
                email = f"student{student_index}@school.lk"
                index_no = f"S{str(student_index).zfill(4)}"
                section = random.choice(SECTIONS)
                password = hash_password("student123")
                
                users_data.append((username, email, password, first_name, last_name, phone, 'student'))
                students_data.append({
                    'index_no': index_no,
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'phone': phone,
                    'grade': grade,
                    'section': section,
                    'stream': stream
                })
                student_index += 1
    
    print(f"Total students to create: {len(students_data)}")
    
    # Insert users
    print("Inserting student users...")
    cursor.executemany('''
        INSERT INTO users (username, email, password, first_name, last_name, phone, role)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', users_data)
    conn.commit()
    
    # Get user IDs
    print("Mapping user IDs...")
    cursor.execute("SELECT id, email FROM users WHERE role = 'student' ORDER BY id")
    user_map = {row[1]: row[0] for row in cursor.fetchall()}
    
    # Insert students
    print("Inserting students...")
    students_with_userid = []
    for s in students_data:
        user_id = user_map.get(s['email'])
        students_with_userid.append((
            s['index_no'], s['first_name'], s['last_name'], s['email'],
            s['phone'], s['grade'], s['section'], s['stream'], user_id
        ))
    
    cursor.executemany('''
        INSERT INTO students (index_no, first_name, last_name, email, phone, grade, section, stream, user_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', students_with_userid)
    conn.commit()
    
    # Generate teachers
    print("Generating 101 teachers...")
    teachers_data = []
    teachers_users = []
    for i in range(101):
        first_name = random.choice(SL_FIRST_NAMES)
        last_name = random.choice(SL_LAST_NAMES)
        phone = generate_phone()
        username = generate_username(first_name, phone) + f"T{i}"
        email = f"teacher{i+1}@school.lk"
        subject = SUBJECTS[i % len(SUBJECTS)]
        password = hash_password("teacher123")
        
        teachers_users.append((username, email, password, first_name, last_name, phone, 'teacher'))
        teachers_data.append((first_name, last_name, email, phone, subject))
    
    cursor.executemany('''
        INSERT INTO users (username, email, password, first_name, last_name, phone, role)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', teachers_users)
    conn.commit()
    
    cursor.execute("SELECT id, email FROM users WHERE role = 'teacher' ORDER BY id")
    teacher_user_map = {row[1]: row[0] for row in cursor.fetchall()}
    
    teachers_with_userid = []
    for t in teachers_data:
        user_id = teacher_user_map.get(t[2])
        teachers_with_userid.append(t + (user_id,))
    
    cursor.executemany('''
        INSERT INTO teachers (first_name, last_name, email, phone, subject, user_id)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', teachers_with_userid)
    conn.commit()
    
    # Generate marks
    print("Generating marks...")
    cursor.execute("SELECT id FROM students")
    student_ids = [row[0] for row in cursor.fetchall()]
    
    marks_data = []
    for student_id in student_ids:
        for subject in SUBJECTS:
            base = random.uniform(30, 90)
            for term in range(1, 4):
                marks = max(0, min(100, base + random.uniform(-10, 10) + term * 2))
                marks_data.append((student_id, subject, term, round(marks, 1)))
    
    # Insert in batches
    batch_size = 10000
    for i in range(0, len(marks_data), batch_size):
        cursor.executemany('''
            INSERT INTO marks (student_id, subject, term, marks)
            VALUES (%s, %s, %s, %s)
        ''', marks_data[i:i+batch_size])
        conn.commit()
        print(f"  Inserted {min(i+batch_size, len(marks_data))}/{len(marks_data)} marks")
    
    # Calculate predictions
    print("Calculating predictions...")
    import numpy as np
    from sklearn.linear_model import LinearRegression
    
    cursor.execute('''
        SELECT s.id, m.subject, m.term, m.marks 
        FROM students s 
        JOIN marks m ON s.id = m.student_id 
        ORDER BY s.id, m.subject, m.term
    ''')
    rows = cursor.fetchall()
    
    predictions_map = {}
    for row in rows:
        key = (row[0], row[1])
        if key not in predictions_map:
            predictions_map[key] = {}
        predictions_map[key][row[2]] = row[3]
    
    prediction_data = []
    for (student_id, subject), terms in predictions_map.items():
        term1 = terms.get(1)
        term2 = terms.get(2)
        if term1 and term2:
            X = np.array([[1], [2]])
            y = np.array([term1, term2])
            model = LinearRegression()
            model.fit(X, y)
            predicted = float(max(0, min(100, round(model.predict([[3]])[0], 1))))
            is_at_risk = bool(predicted < 35)
            prediction_data.append((student_id, subject, predicted, is_at_risk))
    
    # Insert predictions in batches
    for i in range(0, len(prediction_data), batch_size):
        cursor.executemany('''
            INSERT INTO predictions (student_id, subject, predicted_term3, is_at_risk)
            VALUES (%s, %s, %s, %s)
        ''', prediction_data[i:i+batch_size])
        conn.commit()
    
    print("\n=== SUMMARY ===")
    cursor.execute("SELECT COUNT(*) FROM students")
    print(f"Total Students: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM teachers")
    print(f"Total Teachers: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM marks")
    print(f"Total Marks: {cursor.fetchone()[0]}")
    cursor.execute("SELECT SUM(is_at_risk) FROM predictions")
    print(f"At-Risk Students: {cursor.fetchone()[0]}")
    
    print("\nGrade Distribution:")
    cursor.execute('''
        SELECT grade, stream, COUNT(*) as cnt 
        FROM students 
        GROUP BY grade, stream 
        ORDER BY FIELD(grade, 'Grade 1','Grade 2','Grade 3','Grade 4','Grade 5','Grade 6','Grade 7','Grade 8','Grade 9','Grade 10','Grade 11','Grade 12','Grade 13'), stream
    ''')
    for row in cursor.fetchall():
        if row[1]:
            print(f"  {row[0]} - {row[1]}: {row[2]}")
        else:
            print(f"  {row[0]}: {row[2]}")
    
    cursor.close()
    conn.close()
    print("\nDone!")

if __name__ == "__main__":
    main()
