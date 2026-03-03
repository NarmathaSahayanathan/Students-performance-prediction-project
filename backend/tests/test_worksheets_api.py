"""
Backend API Tests for Student Performance Management System
Focus: Worksheets, Notes, and Authentication features
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_CREDS = {"email": "admin@school.com", "password": "admin123"}
TEACHER_CREDS = {"email": "teacher1@school.lk", "password": "teacher123"}
STUDENT_CREDS = {"email": "student1@school.lk", "password": "student123"}


class TestAuthentication:
    """Test login for all user roles"""
    
    def test_admin_login(self):
        """Admin login with admin@school.com / admin123"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "admin"
        assert data["user"]["email"] == "admin@school.com"
    
    def test_teacher_login(self):
        """Teacher login with teacher1@school.lk / teacher123"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER_CREDS)
        assert response.status_code == 200, f"Teacher login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "teacher"
        assert data["user"]["email"] == "teacher1@school.lk"
    
    def test_student_login(self):
        """Student login with student1@school.lk / student123"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=STUDENT_CREDS)
        assert response.status_code == 200, f"Student login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "student"
        assert data["user"]["email"] == "student1@school.lk"
    
    def test_invalid_login(self):
        """Invalid credentials should return 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401


class TestTeacherDashboard:
    """Test teacher dashboard API"""
    
    @pytest.fixture
    def teacher_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER_CREDS)
        return response.json()["access_token"]
    
    def test_teacher_dashboard_loads(self, teacher_token):
        """Teacher dashboard should return teacher info and class stats"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.get(f"{BASE_URL}/api/teacher/dashboard", headers=headers)
        assert response.status_code == 200, f"Teacher dashboard failed: {response.text}"
        data = response.json()
        
        # Verify teacher info
        assert "teacher" in data
        assert data["teacher"]["email"] == "teacher1@school.lk"
        assert "subject" in data["teacher"]
        
        # Verify class stats
        assert "class_stats" in data
        assert "at_risk_students" in data


class TestClassStudentsPerformance:
    """Test class students performance API for worksheets page"""
    
    @pytest.fixture
    def teacher_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER_CREDS)
        return response.json()["access_token"]
    
    def test_get_class_students_performance(self, teacher_token):
        """GET /api/class-students/performance - filter by Grade and Section"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.get(
            f"{BASE_URL}/api/class-students/performance",
            params={"grade": "Grade 1", "section": "A", "term": "1", "subject": "Maths"},
            headers=headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "students" in data
        # Verify students list structure
        if len(data["students"]) > 0:
            student = data["students"][0]
            assert "id" in student
            assert "index_no" in student
            assert "first_name" in student
            assert "last_name" in student
            # Marks should be integers (no decimals)
            if student.get("marks") is not None:
                assert isinstance(student["marks"], (int, float))
                # Check if marks are displayed as integers
                assert student["marks"] == int(student["marks"]), "Marks should be integers"
    
    def test_class_students_different_grades(self, teacher_token):
        """Test filtering by different grades"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        for grade in ["Grade 5", "Grade 10"]:
            response = requests.get(
                f"{BASE_URL}/api/class-students/performance",
                params={"grade": grade, "section": "B", "term": "2", "subject": "Maths"},
                headers=headers
            )
            assert response.status_code == 200, f"Failed for {grade}: {response.text}"


class TestStudentNotes:
    """Test student notes API for worksheets page"""
    
    @pytest.fixture
    def teacher_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER_CREDS)
        return response.json()["access_token"]
    
    @pytest.fixture
    def student_id(self, teacher_token):
        """Get a valid student ID for testing"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.get(
            f"{BASE_URL}/api/class-students/performance",
            params={"grade": "Grade 1", "section": "A", "term": "1", "subject": "Maths"},
            headers=headers
        )
        students = response.json().get("students", [])
        if students:
            return students[0]["id"]
        return None
    
    def test_save_student_note(self, teacher_token, student_id):
        """POST /api/students/{id}/notes - save note for a student"""
        if not student_id:
            pytest.skip("No student found for testing")
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        note_data = {
            "note": "TEST_Note: Student needs extra practice in algebra",
            "term": 1,
            "subject": "Maths"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/students/{student_id}/notes",
            json=note_data,
            headers=headers
        )
        assert response.status_code == 200, f"Failed to save note: {response.text}"
        data = response.json()
        assert "message" in data
    
    def test_note_persists(self, teacher_token, student_id):
        """Verify note persists after saving"""
        if not student_id:
            pytest.skip("No student found for testing")
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        # Save a note
        note_text = "TEST_Persistent note for verification"
        requests.post(
            f"{BASE_URL}/api/students/{student_id}/notes",
            json={"note": note_text, "term": 1, "subject": "Maths"},
            headers=headers
        )
        
        # Fetch students and verify note is there
        response = requests.get(
            f"{BASE_URL}/api/class-students/performance",
            params={"grade": "Grade 1", "section": "A", "term": "1", "subject": "Maths"},
            headers=headers
        )
        students = response.json().get("students", [])
        student = next((s for s in students if s["id"] == student_id), None)
        
        if student:
            assert student.get("note") == note_text, "Note should persist"
    
    def test_bulk_notes_save(self, teacher_token, student_id):
        """POST /api/students/notes/bulk - save multiple notes at once"""
        if not student_id:
            pytest.skip("No student found for testing")
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        notes_data = [
            {"student_id": student_id, "note": "TEST_Bulk note 1", "term": 1, "subject": "Maths"}
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/students/notes/bulk",
            json=notes_data,
            headers=headers
        )
        assert response.status_code == 200, f"Failed to save bulk notes: {response.text}"


class TestWorksheets:
    """Test worksheets CRUD API"""
    
    @pytest.fixture
    def teacher_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER_CREDS)
        return response.json()["access_token"]
    
    def test_get_worksheets(self, teacher_token):
        """GET /api/worksheets - list all worksheets"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.get(f"{BASE_URL}/api/worksheets", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
    
    def test_upload_worksheet(self, teacher_token):
        """POST /api/worksheets - upload a worksheet with Level and description"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        form_data = {
            "tier": "1",  # Level 1
            "title": "TEST_Advanced Problem Solving",
            "description": "TEST_Worksheet for advanced students with marks > 70%",
            "subject": "Maths",
            "grade": "Grade 5",
            "section": "A",
            "term": "1"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/worksheets",
            data=form_data,
            headers=headers
        )
        assert response.status_code == 200, f"Failed to upload worksheet: {response.text}"
        data = response.json()
        assert "id" in data
        assert "message" in data  # API returns id and message
        
        # Cleanup - delete the test worksheet
        worksheet_id = data["id"]
        requests.delete(f"{BASE_URL}/api/worksheets/{worksheet_id}", headers=headers)
    
    def test_worksheet_levels(self, teacher_token):
        """Test all three worksheet levels (Level 1, 2, 3)"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        levels = [
            ("1", "Level 1 - Advanced"),
            ("2", "Level 2 - Intermediate"),
            ("3", "Level 3 - Needs Support")
        ]
        
        created_ids = []
        for tier, description in levels:
            form_data = {
                "tier": tier,
                "title": f"TEST_{description}",
                "description": f"TEST_Worksheet for {description}",
                "subject": "Maths"
            }
            response = requests.post(
                f"{BASE_URL}/api/worksheets",
                data=form_data,
                headers=headers
            )
            assert response.status_code == 200, f"Failed for {description}: {response.text}"
            created_ids.append(response.json()["id"])
        
        # Cleanup
        for wid in created_ids:
            requests.delete(f"{BASE_URL}/api/worksheets/{wid}", headers=headers)
    
    def test_delete_worksheet(self, teacher_token):
        """DELETE /api/worksheets/{id} - delete a worksheet"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        # Create a worksheet first
        form_data = {
            "tier": "2",
            "title": "TEST_To Be Deleted",
            "description": "TEST_This worksheet will be deleted",
            "subject": "Maths"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/worksheets",
            data=form_data,
            headers=headers
        )
        worksheet_id = create_response.json()["id"]
        
        # Delete it
        delete_response = requests.delete(
            f"{BASE_URL}/api/worksheets/{worksheet_id}",
            headers=headers
        )
        assert delete_response.status_code == 200, f"Failed to delete: {delete_response.text}"


class TestMarksAsIntegers:
    """Verify marks are displayed as integers (no decimals)"""
    
    @pytest.fixture
    def teacher_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER_CREDS)
        return response.json()["access_token"]
    
    def test_marks_are_integers_in_students_list(self, teacher_token):
        """Marks in student list should be integers"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.get(
            f"{BASE_URL}/api/class-students/performance",
            params={"grade": "Grade 1", "section": "A", "term": "1", "subject": "Maths"},
            headers=headers
        )
        students = response.json().get("students", [])
        
        for student in students:
            marks = student.get("marks")
            if marks is not None:
                # Marks should be whole numbers
                assert marks == int(marks), f"Marks {marks} should be integer for student {student['index_no']}"
    
    def test_marks_are_integers_in_student_detail(self, teacher_token):
        """Marks in student detail should be integers"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        # Get a student ID first
        response = requests.get(f"{BASE_URL}/api/students", headers=headers)
        students = response.json().get("students", [])
        if not students:
            pytest.skip("No students found")
        
        student_id = students[0]["id"]
        
        # Get student detail
        detail_response = requests.get(
            f"{BASE_URL}/api/students/{student_id}",
            headers=headers
        )
        assert detail_response.status_code == 200
        data = detail_response.json()
        
        for mark in data.get("marks", []):
            if mark.get("marks") is not None:
                assert mark["marks"] == int(mark["marks"]), f"Marks should be integers"


class TestDashboardStats:
    """Test dashboard stats API"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        return response.json()["access_token"]
    
    def test_dashboard_stats(self, admin_token):
        """Dashboard stats should return total students and at-risk count"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "total_students" in data
        assert "at_risk_students" in data
        assert "total_teachers" in data
        assert data["total_students"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
