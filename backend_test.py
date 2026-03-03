#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class StudentPerformanceAPITester:
    def __init__(self, base_url="https://edutrack-lk.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.teacher_token = None
        self.student_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
            self.failed_tests.append(f"{name}: {details}")

    def make_request(self, method, endpoint, data=None, token=None, expect_status=200):
        """Make HTTP request with error handling"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            
            success = response.status_code == expect_status
            return success, response.json() if success else response.text, response.status_code
        except Exception as e:
            return False, str(e), 0

    def test_root_endpoint(self):
        """Test API root endpoint"""
        success, data, status = self.make_request('GET', '')
        self.log_test("API Root Endpoint", success and "Student Performance Management System API" in str(data))

    def test_admin_login(self):
        """Test admin login"""
        success, data, status = self.make_request(
            'POST', 'auth/login',
            {"email": "admin@school.com", "password": "admin123"}
        )
        if success and 'access_token' in data:
            self.admin_token = data['access_token']
            user_role = data.get('user', {}).get('role')
            self.log_test("Admin Login", user_role == 'admin')
        else:
            self.log_test("Admin Login", False, f"Status: {status}, Data: {data}")

    def test_teacher_login(self):
        """Test teacher login"""
        success, data, status = self.make_request(
            'POST', 'auth/login',
            {"email": "teacher1@school.lk", "password": "teacher123"}
        )
        if success and 'access_token' in data:
            self.teacher_token = data['access_token']
            user_role = data.get('user', {}).get('role')
            self.log_test("Teacher Login", user_role == 'teacher')
        else:
            self.log_test("Teacher Login", False, f"Status: {status}, Data: {data}")

    def test_student_login(self):
        """Test student login"""
        success, data, status = self.make_request(
            'POST', 'auth/login',
            {"email": "student1@school.lk", "password": "student123"}
        )
        if success and 'access_token' in data:
            self.student_token = data['access_token']
            user_role = data.get('user', {}).get('role')
            self.log_test("Student Login", user_role == 'student')
        else:
            self.log_test("Student Login", False, f"Status: {status}, Data: {data}")

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        if not self.admin_token:
            self.log_test("Dashboard Stats", False, "No admin token")
            return
        
        success, data, status = self.make_request('GET', 'dashboard/stats', token=self.admin_token)
        if success:
            required_fields = ['total_students', 'total_teachers', 'at_risk_students', 'attendance_rate']
            has_all_fields = all(field in data for field in required_fields)
            self.log_test("Dashboard Stats", has_all_fields)
        else:
            self.log_test("Dashboard Stats", False, f"Status: {status}")

    def test_students_list(self):
        """Test students list endpoint"""
        if not self.admin_token:
            self.log_test("Students List", False, "No admin token")
            return
        
        success, data, status = self.make_request('GET', 'students', token=self.admin_token)
        if success:
            has_students = 'students' in data and len(data['students']) > 0
            has_pagination = 'total' in data and 'page' in data
            self.log_test("Students List", has_students and has_pagination)
        else:
            self.log_test("Students List", False, f"Status: {status}")

    def test_teachers_list(self):
        """Test teachers list endpoint"""
        if not self.admin_token:
            self.log_test("Teachers List", False, "No admin token")
            return
        
        success, data, status = self.make_request('GET', 'teachers', token=self.admin_token)
        if success:
            has_teachers = 'teachers' in data and len(data['teachers']) > 0
            has_pagination = 'total' in data and 'page' in data
            self.log_test("Teachers List", has_teachers and has_pagination)
        else:
            self.log_test("Teachers List", False, f"Status: {status}")

    def test_at_risk_students(self):
        """Test at-risk students endpoint"""
        if not self.admin_token:
            self.log_test("At-Risk Students", False, "No admin token")
            return
        
        success, data, status = self.make_request('GET', 'at-risk-students', token=self.admin_token)
        if success:
            # Should return list of at-risk students
            is_list = isinstance(data, list)
            self.log_test("At-Risk Students", is_list)
        else:
            self.log_test("At-Risk Students", False, f"Status: {status}")

    def test_marks_endpoint(self):
        """Test marks endpoint"""
        if not self.admin_token:
            self.log_test("Marks Endpoint", False, "No admin token")
            return
        
        success, data, status = self.make_request('GET', 'marks', token=self.admin_token)
        if success:
            is_list = isinstance(data, list)
            self.log_test("Marks Endpoint", is_list)
        else:
            self.log_test("Marks Endpoint", False, f"Status: {status}")

    def test_attendance_endpoint(self):
        """Test attendance endpoint"""
        if not self.admin_token:
            self.log_test("Attendance Endpoint", False, "No admin token")
            return
        
        success, data, status = self.make_request('GET', 'attendance', token=self.admin_token)
        if success:
            is_list = isinstance(data, list)
            self.log_test("Attendance Endpoint", is_list)
        else:
            self.log_test("Attendance Endpoint", False, f"Status: {status}")

    def test_predictions_endpoint(self):
        """Test predictions endpoint"""
        if not self.admin_token:
            self.log_test("Predictions Endpoint", False, "No admin token")
            return
        
        success, data, status = self.make_request('GET', 'predictions', token=self.admin_token)
        if success:
            is_list = isinstance(data, list)
            self.log_test("Predictions Endpoint", is_list)
        else:
            self.log_test("Predictions Endpoint", False, f"Status: {status}")

    def test_dropdown_endpoints(self):
        """Test dropdown data endpoints"""
        endpoints = ['dropdown/grades', 'dropdown/sections', 'dropdown/subjects']
        for endpoint in endpoints:
            success, data, status = self.make_request('GET', endpoint)
            is_list = isinstance(data, list) and len(data) > 0
            self.log_test(f"Dropdown {endpoint.split('/')[-1].title()}", is_list)

    def test_student_dashboard(self):
        """Test student dashboard endpoint"""
        if not self.student_token:
            self.log_test("Student Dashboard", False, "No student token")
            return
        
        success, data, status = self.make_request('GET', 'student/dashboard', token=self.student_token)
        if success:
            has_student = 'student' in data
            has_marks = 'marks' in data
            has_predictions = 'predictions' in data
            self.log_test("Student Dashboard", has_student and has_marks and has_predictions)
        else:
            self.log_test("Student Dashboard", False, f"Status: {status}")

    def test_teacher_dashboard(self):
        """Test teacher dashboard endpoint"""
        if not self.teacher_token:
            self.log_test("Teacher Dashboard", False, "No teacher token")
            return
        
        success, data, status = self.make_request('GET', 'teacher/dashboard', token=self.teacher_token)
        if success:
            has_teacher = 'teacher' in data
            has_stats = 'class_stats' in data
            self.log_test("Teacher Dashboard", has_teacher and has_stats)
        else:
            self.log_test("Teacher Dashboard", False, f"Status: {status}")

    def test_export_endpoints(self):
        """Test export endpoints (PDF/Excel)"""
        if not self.admin_token:
            self.log_test("Export Endpoints", False, "No admin token")
            return
        
        # Test PDF export
        success, data, status = self.make_request('GET', 'export/students/pdf', token=self.admin_token, expect_status=200)
        self.log_test("PDF Export", success)
        
        # Test Excel export
        success, data, status = self.make_request('GET', 'export/students/excel', token=self.admin_token, expect_status=200)
        self.log_test("Excel Export", success)

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Student Performance Management System API Tests")
        print("=" * 60)
        
        # Basic connectivity
        self.test_root_endpoint()
        
        # Authentication tests
        self.test_admin_login()
        self.test_teacher_login()
        self.test_student_login()
        
        # Admin endpoints
        self.test_dashboard_stats()
        self.test_students_list()
        self.test_teachers_list()
        self.test_at_risk_students()
        self.test_marks_endpoint()
        self.test_attendance_endpoint()
        self.test_predictions_endpoint()
        
        # Dropdown data
        self.test_dropdown_endpoints()
        
        # Role-specific dashboards
        self.test_student_dashboard()
        self.test_teacher_dashboard()
        
        # Export functionality
        self.test_export_endpoints()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.failed_tests:
            print("\n❌ Failed Tests:")
            for failure in self.failed_tests:
                print(f"  - {failure}")
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"\n✨ Success Rate: {success_rate:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = StudentPerformanceAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())