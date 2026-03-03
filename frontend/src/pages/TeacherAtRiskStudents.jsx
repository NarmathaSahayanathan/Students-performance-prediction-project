import { useState, useEffect } from "react";
import axios from "axios";
import { API, useAuth } from "../App";
import { DashboardLayout } from "./DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Badge } from "../components/ui/badge";
import { AlertTriangle, Loader2, TrendingDown, Phone } from "lucide-react";
import { toast } from "sonner";

const GRADES = ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12", "Grade 13"];
const SECTIONS = ["A", "B", "C", "D"];

export default function TeacherAtRiskStudents() {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [gradeFilter, setGradeFilter] = useState("");
  const [sectionFilter, setSectionFilter] = useState("");
  const [teacherSubject, setTeacherSubject] = useState("");
  const { user } = useAuth();

  useEffect(() => { fetchTeacherInfo(); }, []);
  useEffect(() => { if (teacherSubject) fetchAtRisk(); }, [gradeFilter, sectionFilter, teacherSubject]);

  const fetchTeacherInfo = async () => {
    try {
      const response = await axios.get(`${API}/teacher/dashboard`);
      setTeacherSubject(response.data.teacher?.subject || "");
    } catch (error) { console.error(error); }
  };

  const fetchAtRisk = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ subject: teacherSubject });
      if (gradeFilter && gradeFilter !== "all") params.append("grade", gradeFilter);
      if (sectionFilter && sectionFilter !== "all") params.append("section", sectionFilter);
      const response = await axios.get(`${API}/at-risk-students?${params}`);
      setStudents(response.data);
    } catch (error) { toast.error("Failed to fetch at-risk students"); }
    finally { setLoading(false); }
  };

  // Group students by Grade and Section
  const groupedStudents = students.reduce((acc, student) => {
    const key = `${student.grade} - ${student.section}`;
    if (!acc[key]) acc[key] = [];
    acc[key].push(student);
    return acc;
  }, {});

  // Sort the keys
  const sortedKeys = Object.keys(groupedStudents).sort((a, b) => {
    const gradeA = parseInt(a.match(/\d+/)?.[0] || 0);
    const gradeB = parseInt(b.match(/\d+/)?.[0] || 0);
    if (gradeA !== gradeB) return gradeA - gradeB;
    return a.localeCompare(b);
  });

  return (
    <DashboardLayout title="At-Risk Students">
      <div className="space-y-6 animate-fade-in" data-testid="teacher-at-risk-page">
        {/* Alert Banner */}
        <Card className="border-0 shadow-sm bg-red-50 border-l-4 border-l-red-500">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center alert-pulse">
              <AlertTriangle className="w-6 h-6 text-red-500" />
            </div>
            <div>
              <h3 className="font-semibold text-red-800">Students Requiring Attention - {teacherSubject}</h3>
              <p className="text-sm text-red-600">These students are predicted to score below 35% in Term 3.</p>
            </div>
            <div className="ml-auto">
              <Badge className="bg-red-500 text-white text-lg px-4 py-2">{students.length}</Badge>
            </div>
          </CardContent>
        </Card>

        {/* Filters */}
        <Card className="border-0 shadow-sm">
          <CardContent className="p-4">
            <div className="flex flex-wrap gap-4">
              <div className="w-48">
                <Select value={gradeFilter || "all"} onValueChange={(v) => setGradeFilter(v === "all" ? "" : v)}>
                  <SelectTrigger data-testid="grade-filter"><SelectValue placeholder="All Grades" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Grades</SelectItem>
                    {GRADES.map(g => <SelectItem key={g} value={g}>{g}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="w-48">
                <Select value={sectionFilter || "all"} onValueChange={(v) => setSectionFilter(v === "all" ? "" : v)}>
                  <SelectTrigger data-testid="section-filter"><SelectValue placeholder="All Sections" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Sections</SelectItem>
                    {SECTIONS.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* At-Risk Students Grouped by Grade and Section */}
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="w-8 h-8 animate-spin text-sky-500" />
          </div>
        ) : sortedKeys.length === 0 ? (
          <Card className="border-0 shadow-sm">
            <CardContent className="p-8 text-center text-slate-500">
              No at-risk students found for {teacherSubject}
            </CardContent>
          </Card>
        ) : (
          sortedKeys.map(key => (
            <Card key={key} className="border-0 shadow-sm">
              <CardHeader className="bg-red-50 border-b border-red-100">
                <CardTitle className="text-lg flex items-center gap-2">
                  <TrendingDown className="w-5 h-5 text-red-500" />
                  {key}
                  <Badge className="ml-2 bg-red-500 text-white">{groupedStudents[key].length}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-slate-50">
                      <TableHead>Index No</TableHead>
                      <TableHead>Student Name</TableHead>
                      <TableHead>Term 1</TableHead>
                      <TableHead>Term 2</TableHead>
                      <TableHead>Predicted Term 3</TableHead>
                      <TableHead>Contact</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {groupedStudents[key].map((student, idx) => (
                      <TableRow key={`${student.id}-${idx}`} className="hover:bg-red-50/50">
                        <TableCell className="font-medium">{student.index_no}</TableCell>
                        <TableCell>{student.first_name} {student.last_name}</TableCell>
                        <TableCell>{student.term1_marks ?? '-'}</TableCell>
                        <TableCell>{student.term2_marks ?? '-'}</TableCell>
                        <TableCell>
                          <span className="font-bold text-red-600 flex items-center gap-1">
                            <AlertTriangle className="w-4 h-4" />
                            {student.predicted_term3}%
                          </span>
                        </TableCell>
                        <TableCell>
                          {student.phone && (
                            <a href={`tel:${student.phone}`} className="text-sky-500 hover:text-sky-600 flex items-center gap-1">
                              <Phone className="w-4 h-4" />
                              <span className="text-sm">{student.phone}</span>
                            </a>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </DashboardLayout>
  );
}
