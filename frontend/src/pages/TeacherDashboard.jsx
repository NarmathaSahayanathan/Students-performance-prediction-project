import { useState, useEffect } from "react";
import axios from "axios";
import { API, useAuth } from "../App";
import { DashboardLayout } from "./DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Legend } from "recharts";
import { Users, BookOpen, Loader2 } from "lucide-react";

const GRADES = ["", "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12", "Grade 13"];

export default function TeacherDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => { fetchDashboard(); }, []);

  const fetchDashboard = async () => {
    try {
      const response = await axios.get(`${API}/teacher/dashboard`);
      setData(response.data);
    } catch (error) { console.error("Failed to load dashboard"); }
    finally { setLoading(false); }
  };

  if (loading) return <DashboardLayout title="Teacher Dashboard"><div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 animate-spin text-sky-500" /></div></DashboardLayout>;

  const teacher = data?.teacher;
  const classStats = data?.class_stats || [];
  
  const chartData = classStats.map(c => ({
    grade: c.grade?.replace('Grade ', 'G'),
    "Average Marks": Math.round(c.avg_marks || 0),
    "At-Risk Count": c.at_risk_count || 0
  }));

  const totalStudents = classStats.reduce((sum, c) => sum + (c.total_students || 0), 0);
  const totalAtRisk = data?.at_risk_students?.length || 0;

  return (
    <DashboardLayout title="Teacher Dashboard">
      <div className="space-y-6 animate-fade-in" data-testid="teacher-dashboard">
        {/* Teacher Info */}
        <Card className="border-0 shadow-sm bg-gradient-to-r from-sky-500 to-sky-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center">
                <BookOpen className="w-8 h-8" />
              </div>
              <div>
                <h2 className="text-2xl font-bold">{teacher?.first_name} {teacher?.last_name}</h2>
                <p className="text-sky-100">{teacher?.subject} Teacher</p>
                <p className="text-sm text-sky-100">{teacher?.email}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Stats - Only 2 cards now */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="border-0 shadow-sm">
            <CardContent className="p-6 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-sky-50 flex items-center justify-center">
                <Users className="w-6 h-6 text-sky-500" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Total Students</p>
                <p className="text-2xl font-bold">{totalStudents}</p>
              </div>
            </CardContent>
          </Card>
          <Card className="border-0 shadow-sm">
            <CardContent className="p-6 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-red-50 flex items-center justify-center">
                <svg className="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div>
                <p className="text-sm text-slate-500">At-Risk Students</p>
                <p className="text-2xl font-bold text-red-600">{totalAtRisk}</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Performance by Grade - Increased height, no tooltip */}
        <Card className="border-0 shadow-sm">
          <CardHeader><CardTitle className="text-lg">Performance by Grade - {teacher?.subject}</CardTitle></CardHeader>
          <CardContent>
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="grade" tick={{ fill: '#64748b', fontSize: 12 }} />
                  <YAxis tick={{ fill: '#64748b', fontSize: 12 }} />
                  <Bar dataKey="Average Marks" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="At-Risk Count" fill="#ef4444" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            {/* Custom Legend */}
            <div className="flex justify-center gap-8 mt-4 pt-4 border-t border-slate-100">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-sky-500"></div>
                <span className="text-sm text-slate-600">Average Marks</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-red-500"></div>
                <span className="text-sm text-slate-600">At-Risk Students</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
