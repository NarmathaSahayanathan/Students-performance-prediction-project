import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import { DashboardLayout } from "./DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Badge } from "../components/ui/badge";
import { AlertTriangle, Loader2, TrendingDown, Phone } from "lucide-react";
import { toast } from "sonner";

const GRADES = ["", "Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11"];
const SUBJECTS = ["", "Maths", "Science", "English", "Tamil", "ICT"];

export default function AtRiskStudents() {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [gradeFilter, setGradeFilter] = useState("");
  const [subjectFilter, setSubjectFilter] = useState("");

  useEffect(() => { fetchAtRisk(); }, [gradeFilter, subjectFilter]);

  const fetchAtRisk = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (gradeFilter) params.append("grade", gradeFilter);
      if (subjectFilter) params.append("subject", subjectFilter);
      const response = await axios.get(`${API}/at-risk-students?${params}`);
      setStudents(response.data);
    } catch (error) { toast.error("Failed to fetch at-risk students"); }
    finally { setLoading(false); }
  };

  return (
    <DashboardLayout title="At-Risk Students">
      <div className="space-y-6 animate-fade-in" data-testid="at-risk-page">
        {/* Alert Banner */}
        <Card className="border-0 shadow-sm bg-red-50 border-l-4 border-l-red-500">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center alert-pulse">
              <AlertTriangle className="w-6 h-6 text-red-500" />
            </div>
            <div>
              <h3 className="font-semibold text-red-800">Students Requiring Attention</h3>
              <p className="text-sm text-red-600">These students are predicted to score below 35% in Term 3 based on their Term 1 and Term 2 performance.</p>
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
                    {GRADES.slice(1).map(g => <SelectItem key={g} value={g}>{g}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="w-48">
                <Select value={subjectFilter || "all"} onValueChange={(v) => setSubjectFilter(v === "all" ? "" : v)}>
                  <SelectTrigger data-testid="subject-filter"><SelectValue placeholder="All Subjects" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Subjects</SelectItem>
                    {SUBJECTS.slice(1).map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* At-Risk Students Table */}
        <Card className="border-0 shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <TrendingDown className="w-5 h-5 text-red-500" />
              At-Risk Students List
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {loading ? <div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 animate-spin text-sky-500" /></div> : (
              <Table>
                <TableHeader><TableRow className="bg-red-50">
                  <TableHead>Index No</TableHead>
                  <TableHead>Student Name</TableHead>
                  <TableHead>Grade</TableHead>
                  <TableHead>Subject</TableHead>
                  <TableHead>Term 1</TableHead>
                  <TableHead>Term 2</TableHead>
                  <TableHead>Predicted T3</TableHead>
                  <TableHead>Contact</TableHead>
                </TableRow></TableHeader>
                <TableBody>
                  {students.map((student, idx) => (
                    <TableRow key={`${student.id}-${student.subject}-${idx}`} className="hover:bg-red-50/50" data-testid={`at-risk-row-${student.id}`}>
                      <TableCell className="font-medium">{student.index_no}</TableCell>
                      <TableCell>{student.first_name} {student.last_name}</TableCell>
                      <TableCell>{student.grade} - {student.section}</TableCell>
                      <TableCell><Badge variant="secondary">{student.subject}</Badge></TableCell>
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
                  {students.length === 0 && <TableRow><TableCell colSpan={8} className="text-center py-8 text-slate-500">No at-risk students found</TableCell></TableRow>}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
