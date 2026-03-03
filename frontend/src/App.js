import { useState, useEffect, createContext, useContext } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import { Toaster, toast } from "sonner";

// Pages
import LoginPage from "./pages/LoginPage";
import AdminDashboard from "./pages/AdminDashboard";
import StudentManagement from "./pages/StudentManagement";
import TeacherManagement from "./pages/TeacherManagement";
import MarksEntry from "./pages/MarksEntry";
import AttendancePage from "./pages/AttendancePage";
import StudentDashboard from "./pages/StudentDashboard";
import TeacherDashboard from "./pages/TeacherDashboard";
import ReportsPage from "./pages/ReportsPage";
import BulkImportPage from "./pages/BulkImportPage";
import AtRiskStudents from "./pages/AtRiskStudents";
import TeacherAtRiskStudents from "./pages/TeacherAtRiskStudents";
import WorksheetsPage from "./pages/WorksheetsPage";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
      fetchUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { access_token, user: userData } = response.data;
      localStorage.setItem("token", access_token);
      axios.defaults.headers.common["Authorization"] = `Bearer ${access_token}`;
      setToken(access_token);
      setUser(userData);
      toast.success("Login successful!");
      return userData;
    } catch (error) {
      toast.error(error.response?.data?.detail || "Login failed");
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    delete axios.defaults.headers.common["Authorization"];
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Protected Route Component
const ProtectedRoute = ({ children, allowedRoles }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-500"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    // Redirect to appropriate dashboard based on role
    if (user.role === "admin") return <Navigate to="/admin" replace />;
    if (user.role === "teacher") return <Navigate to="/teacher" replace />;
    if (user.role === "student") return <Navigate to="/student" replace />;
    return <Navigate to="/login" replace />;
  }

  return children;
};

// Redirect based on role
const RoleBasedRedirect = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-500"></div>
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;
  
  if (user.role === "admin") return <Navigate to="/admin" replace />;
  if (user.role === "teacher") return <Navigate to="/teacher" replace />;
  if (user.role === "student") return <Navigate to="/student" replace />;
  
  return <Navigate to="/login" replace />;
};

function App() {
  return (
    <div className="App">
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            
            {/* Admin Routes */}
            <Route path="/admin" element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <AdminDashboard />
              </ProtectedRoute>
            } />
            <Route path="/admin/students" element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <StudentManagement />
              </ProtectedRoute>
            } />
            <Route path="/admin/teachers" element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <TeacherManagement />
              </ProtectedRoute>
            } />
            <Route path="/admin/marks" element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <MarksEntry />
              </ProtectedRoute>
            } />
            <Route path="/admin/attendance" element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <AttendancePage />
              </ProtectedRoute>
            } />
            <Route path="/admin/reports" element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <ReportsPage />
              </ProtectedRoute>
            } />
            <Route path="/admin/import" element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <BulkImportPage />
              </ProtectedRoute>
            } />
            <Route path="/admin/at-risk" element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <AtRiskStudents />
              </ProtectedRoute>
            } />
            
            {/* Teacher Routes */}
            <Route path="/teacher" element={
              <ProtectedRoute allowedRoles={["teacher"]}>
                <TeacherDashboard />
              </ProtectedRoute>
            } />
            <Route path="/teacher/marks" element={
              <ProtectedRoute allowedRoles={["teacher"]}>
                <MarksEntry />
              </ProtectedRoute>
            } />
            <Route path="/teacher/attendance" element={
              <ProtectedRoute allowedRoles={["teacher"]}>
                <AttendancePage />
              </ProtectedRoute>
            } />
            <Route path="/teacher/at-risk" element={
              <ProtectedRoute allowedRoles={["teacher"]}>
                <TeacherAtRiskStudents />
              </ProtectedRoute>
            } />
            <Route path="/teacher/worksheets" element={
              <ProtectedRoute allowedRoles={["teacher"]}>
                <WorksheetsPage />
              </ProtectedRoute>
            } />
            
            {/* Student Routes */}
            <Route path="/student" element={
              <ProtectedRoute allowedRoles={["student"]}>
                <StudentDashboard />
              </ProtectedRoute>
            } />
            
            {/* Root redirect */}
            <Route path="/" element={<RoleBasedRedirect />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
        <Toaster position="top-right" richColors />
      </AuthProvider>
    </div>
  );
}

export default App;
