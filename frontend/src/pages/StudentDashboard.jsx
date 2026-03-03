import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { API, useAuth } from "../App";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { Button } from "../components/ui/button";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from "recharts";
import { GraduationCap, TrendingUp, Calendar, LogOut, CheckCircle2, XCircle, Clock, Download, FileText, Upload, Check, Loader2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";

export default function StudentDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [worksheets, setWorksheets] = useState([]);
  const [submitting, setSubmitting] = useState(null);
  const fileInputRefs = useRef({});
  const { logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => { fetchDashboard(); fetchWorksheets(); }, []);

  const fetchDashboard = async () => {
    try {
      const response = await axios.get(`${API}/student/dashboard`);
      setData(response.data);
    } catch (error) { toast.error("Failed to load dashboard"); }
    finally { setLoading(false); }
  };

  const fetchWorksheets = async () => {
    try {
      const response = await axios.get(`${API}/student/worksheets`);
      setWorksheets(response.data.worksheets || []);
    } catch (error) { console.error("Failed to load worksheets"); }
  };

  const handleDownload = async (ws) => {
    try {
      const response = await axios.get(`${API}/student/worksheets/${ws.id}/download`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', ws.file_name);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success("Downloaded");
    } catch (error) { toast.error("Failed to download worksheet"); }
  };

  const handleSubmit = async (wsId, file) => {
    if (!file) return;
    setSubmitting(wsId);
    try {
      const formData = new FormData();
      formData.append("file", file);
      await axios.post(`${API}/student/worksheets/${wsId}/submit`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      toast.success("Submission uploaded");
      fetchWorksheets();
    } catch (error) { toast.error("Failed to upload submission"); }
    finally { setSubmitting(null); }
  };

  const handleLogout = () => { logout(); navigate("/login"); };

  const handleExportPDF = async () => {
    if (!data?.student?.id) return;
    try {
      const response = await axios.get(`${API}/export/performance/pdf/${data.student.id}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${data.student.index_no}_performance.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success("PDF exported");
    } catch (error) { toast.error("Failed to export PDF"); }
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center bg-slate-50"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-500"></div></div>;

  const student = data?.student;
  const marksBySubject = {};
  data?.marks?.forEach(m => {
    if (!marksBySubject[m.subject]) marksBySubject[m.subject] = {};
    marksBySubject[m.subject][m.term] = m.marks;
  });
  const chartData = Object.entries(marksBySubject).map(([subject, terms]) => ({
    subject,
    term1: terms[1] || 0,
    term2: terms[2] || 0,
    term3: terms[3] || 0,
  }));

  const attendance = data?.attendance || { present: 0, absent: 0, late: 0, total: 0 };
  const attendanceRate = attendance.total > 0 ? Math.round((attendance.present / attendance.total) * 100) : 0;

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-4 md:px-8 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-sky-500 flex items-center justify-center">
              <GraduationCap className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-800">Student Dashboard</h1>
              <p className="text-sm text-slate-500">Welcome, {student?.first_name}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="outline" onClick={handleExportPDF} data-testid="export-pdf-btn"><Download className="w-4 h-4 mr-2" />Export PDF</Button>
            <Button variant="ghost" onClick={handleLogout} data-testid="logout-btn"><LogOut className="w-4 h-4 mr-2" />Logout</Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-4 md:p-8 space-y-6" data-testid="student-dashboard">
        {/* Student Info */}
        <Card className="border-0 shadow-sm">
          <CardContent className="p-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div><p className="text-sm text-slate-500">Index No</p><p className="font-semibold text-lg">{student?.index_no}</p></div>
              <div><p className="text-sm text-slate-500">Name</p><p className="font-semibold text-lg">{student?.first_name} {student?.last_name}</p></div>
              <div><p className="text-sm text-slate-500">Grade & Section</p><p className="font-semibold text-lg">{student?.grade} - {student?.section}</p></div>
              <div><p className="text-sm text-slate-500">Attendance Rate</p><p className="font-semibold text-lg">{attendanceRate}%</p></div>
            </div>
          </CardContent>
        </Card>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="border-0 shadow-sm"><CardContent className="p-4 flex items-center gap-4">
            <div className="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center"><CheckCircle2 className="w-5 h-5 text-green-500" /></div>
            <div><p className="text-2xl font-bold">{attendance.present || 0}</p><p className="text-sm text-slate-500">Present</p></div>
          </CardContent></Card>
          <Card className="border-0 shadow-sm"><CardContent className="p-4 flex items-center gap-4">
            <div className="w-10 h-10 rounded-lg bg-red-50 flex items-center justify-center"><XCircle className="w-5 h-5 text-red-500" /></div>
            <div><p className="text-2xl font-bold">{attendance.absent || 0}</p><p className="text-sm text-slate-500">Absent</p></div>
          </CardContent></Card>
          <Card className="border-0 shadow-sm"><CardContent className="p-4 flex items-center gap-4">
            <div className="w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center"><Clock className="w-5 h-5 text-amber-500" /></div>
            <div><p className="text-2xl font-bold">{attendance.late || 0}</p><p className="text-sm text-slate-500">Late</p></div>
          </CardContent></Card>
          <Card className="border-0 shadow-sm"><CardContent className="p-4 flex items-center gap-4">
            <div className="w-10 h-10 rounded-lg bg-sky-50 flex items-center justify-center"><Calendar className="w-5 h-5 text-sky-500" /></div>
            <div><p className="text-2xl font-bold">{attendance.total || 0}</p><p className="text-sm text-slate-500">Total Days</p></div>
          </CardContent></Card>
        </div>

        {/* Performance Chart */}
        <Card className="border-0 shadow-sm">
          <CardHeader><CardTitle className="text-lg flex items-center gap-2"><TrendingUp className="w-5 h-5 text-sky-500" />Term Performance</CardTitle></CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="subject" tick={{ fill: '#64748b', fontSize: 12 }} />
                  <YAxis tick={{ fill: '#64748b', fontSize: 12 }} domain={[0, 100]} />
                  <Bar dataKey="term1" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="term2" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="term3" fill="#14b8a6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="flex justify-center gap-8 mt-4 pt-4 border-t border-slate-100">
              <div className="flex items-center gap-2"><div className="w-4 h-4 rounded bg-sky-500"></div><span className="text-sm text-slate-600">Term 1</span></div>
              <div className="flex items-center gap-2"><div className="w-4 h-4 rounded bg-cyan-500"></div><span className="text-sm text-slate-600">Term 2</span></div>
              <div className="flex items-center gap-2"><div className="w-4 h-4 rounded bg-teal-500"></div><span className="text-sm text-slate-600">Term 3</span></div>
            </div>
          </CardContent>
        </Card>

        {/* Marks Table */}
        <Card className="border-0 shadow-sm">
          <CardHeader><CardTitle className="text-lg">Detailed Marks</CardTitle></CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader><TableRow className="bg-slate-50">
                <TableHead>Subject</TableHead><TableHead>Term 1</TableHead><TableHead>Term 2</TableHead><TableHead>Term 3</TableHead>
              </TableRow></TableHeader>
              <TableBody>
                {['Maths', 'Science', 'English', 'Tamil', 'ICT'].map(subject => {
                  const terms = marksBySubject[subject] || {};
                  return (
                    <TableRow key={subject}>
                      <TableCell className="font-medium">{subject}</TableCell>
                      <TableCell>{terms[1] ?? '-'}</TableCell>
                      <TableCell>{terms[2] ?? '-'}</TableCell>
                      <TableCell>{terms[3] ?? '-'}</TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
        {/* Worksheets */}
        <Card className="border-0 shadow-sm">
          <CardHeader><CardTitle className="text-lg flex items-center gap-2"><FileText className="w-5 h-5 text-sky-500" />My Worksheets</CardTitle></CardHeader>
          <CardContent className="p-0">
            {worksheets.length === 0 ? (
              <div className="p-8 text-center text-slate-500">No worksheets assigned yet</div>
            ) : (
              <Table>
                <TableHeader><TableRow className="bg-slate-50">
                  <TableHead>Subject</TableHead>
                  <TableHead>Term</TableHead>
                  <TableHead>Note</TableHead>
                  <TableHead>Worksheet</TableHead>
                  <TableHead>Submit</TableHead>
                  <TableHead>Submission</TableHead>
                </TableRow></TableHeader>
                <TableBody>
                  {worksheets.map(ws => (
                    <TableRow key={ws.id}>
                      <TableCell className="font-medium">{ws.subject}</TableCell>
                      <TableCell>Term {ws.term}</TableCell>
                      <TableCell className="text-slate-500 text-sm">{ws.note || '-'}</TableCell>
                      <TableCell>
                        <Button variant="outline" size="sm" onClick={() => handleDownload(ws)}>
                          <Download className="w-4 h-4 mr-1" />Download
                        </Button>
                      </TableCell>
                      <TableCell>
                        <div className="relative">
                          <input
                            ref={el => fileInputRefs.current[ws.id] = el}
                            type="file"
                            accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx"
                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                            onChange={(e) => { if (e.target.files?.[0]) handleSubmit(ws.id, e.target.files[0]); }}
                          />
                          <Button variant="outline" size="sm" disabled={submitting === ws.id} className="pointer-events-none">
                            {submitting === ws.id ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Upload className="w-4 h-4 mr-1" />}
                            Upload
                          </Button>
                        </div>
                      </TableCell>
                      <TableCell>
                        {ws.submission_file_name ? (
                          <span className="flex items-center gap-1 text-green-600 text-sm">
                            <Check className="w-4 h-4" />{ws.submission_file_name}
                          </span>
                        ) : <span className="text-slate-400 text-sm">Not submitted</span>}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
