import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import { DashboardLayout } from "./DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { Users, GraduationCap, CheckCircle2, Loader2 } from "lucide-react";

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`);
      setStats(response.data);
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout title="Dashboard">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-12 h-12 animate-spin text-sky-500" />
        </div>
      </DashboardLayout>
    );
  }

  const statCards = [
    { 
      title: "Total Students", 
      value: stats?.total_students || 0, 
      icon: Users, 
      color: "bg-sky-500",
      bgColor: "bg-sky-50"
    },
    { 
      title: "Total Teachers", 
      value: stats?.total_teachers || 0, 
      icon: GraduationCap, 
      color: "bg-emerald-500",
      bgColor: "bg-emerald-50"
    },
    { 
      title: "Attendance Rate", 
      value: `${stats?.attendance_rate || 0}%`, 
      icon: CheckCircle2, 
      color: "bg-amber-500",
      bgColor: "bg-amber-50"
    },
  ];

  // Process grade distribution data for the table
  const gradeData = stats?.grade_distribution || [];

  return (
    <DashboardLayout title="Dashboard">
      <div className="space-y-8 animate-fade-in" data-testid="admin-dashboard">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {statCards.map((stat, index) => (
            <Card key={index} className="card-hover border-0 shadow-sm" data-testid={`stat-card-${stat.title.toLowerCase().replace(/\s+/g, '-')}`}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-500">{stat.title}</p>
                    <p className="text-3xl font-bold text-slate-800 mt-1">{stat.value}</p>
                  </div>
                  <div className={`w-12 h-12 rounded-xl ${stat.bgColor} flex items-center justify-center`}>
                    <stat.icon className={`w-6 h-6 ${stat.color.replace('bg-', 'text-')}`} />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Students by Class Table */}
        <Card className="border-0 shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-slate-800">
              Students by Class
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead className="font-semibold">Class/Grade</TableHead>
                  <TableHead className="font-semibold text-right">Number of Students</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {gradeData.length > 0 ? (
                  gradeData.map((item, index) => (
                    <TableRow key={index} className="hover:bg-slate-50">
                      <TableCell className="font-medium">{item.grade}</TableCell>
                      <TableCell className="text-right">{item.count}</TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={2} className="text-center py-8 text-slate-500">
                      No class data available
                    </TableCell>
                  </TableRow>
                )}
                {gradeData.length > 0 && (
                  <TableRow className="bg-sky-50 font-semibold">
                    <TableCell>Total</TableCell>
                    <TableCell className="text-right">
                      {gradeData.reduce((sum, item) => sum + item.count, 0)}
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
