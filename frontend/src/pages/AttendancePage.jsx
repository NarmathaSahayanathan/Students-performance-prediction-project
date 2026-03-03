import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import { DashboardLayout } from "./DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Label } from "../components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Badge } from "../components/ui/badge";
import { Calendar } from "../components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "../components/ui/popover";
import { toast } from "sonner";
import { Save, Calendar as CalendarIcon, Loader2, Check, X, Clock } from "lucide-react";
import { format } from "date-fns";

const GRADES = ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12", "Grade 13"];
const SECTIONS = ["A", "B", "C", "D"];

export default function AttendancePage() {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [grade, setGrade] = useState("");
  const [section, setSection] = useState("");
  const [date, setDate] = useState(new Date());
  const [attendance, setAttendance] = useState({});

  const fetchStudents = async () => {
    if (!grade || !section) return;
    setLoading(true);
    try {
      const response = await axios.get(`${API}/students?grade=${grade}&section=${section}&limit=100`);
      setStudents(response.data.students);
      
      const dateStr = format(date, "yyyy-MM-dd");
      const attResponse = await axios.get(`${API}/attendance?date=${dateStr}&grade=${grade}&section=${section}`);
      const attMap = {};
      attResponse.data.forEach(a => { attMap[a.student_id] = a.status; });
      setAttendance(attMap);
    } catch (error) { toast.error("Failed to fetch data"); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchStudents(); }, [grade, section, date]);

  const handleStatusChange = (studentId, status) => {
    setAttendance(prev => ({ ...prev, [studentId]: status }));
  };

  const handleSaveAll = async () => {
    setSaving(true);
    try {
      const dateStr = format(date, "yyyy-MM-dd");
      const entries = Object.entries(attendance)
        .filter(([_, status]) => status)
        .map(([studentId, status]) => ({ student_id: parseInt(studentId), date: dateStr, status }));
      
      if (entries.length === 0) { toast.error("No attendance to save"); setSaving(false); return; }
      
      await axios.post(`${API}/attendance/bulk`, entries);
      toast.success(`Saved attendance for ${entries.length} students`);
    } catch (error) { toast.error("Failed to save attendance"); }
    finally { setSaving(false); }
  };

  const markAllPresent = () => {
    const newAttendance = {};
    students.forEach(s => { newAttendance[s.id] = "present"; });
    setAttendance(newAttendance);
  };

  const getStatusBadge = (status) => {
    if (status === "present") return <Badge className="status-present">Present</Badge>;
    if (status === "absent") return <Badge className="status-absent">Absent</Badge>;
    if (status === "late") return <Badge className="status-late">Late</Badge>;
    return <Badge variant="outline">Not Set</Badge>;
  };

  return (
    <DashboardLayout title="Attendance">
      <div className="space-y-6 animate-fade-in" data-testid="attendance-page">
        <Card className="border-0 shadow-sm">
          <CardHeader><CardTitle className="text-lg">Select Class & Date</CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <Label>Grade</Label>
                <Select value={grade} onValueChange={setGrade}>
                  <SelectTrigger data-testid="select-grade"><SelectValue placeholder="Select grade" /></SelectTrigger>
                  <SelectContent>{GRADES.map(g => <SelectItem key={g} value={g}>{g}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div>
                <Label>Section</Label>
                <Select value={section} onValueChange={setSection}>
                  <SelectTrigger data-testid="select-section"><SelectValue placeholder="Select section" /></SelectTrigger>
                  <SelectContent>{SECTIONS.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div>
                <Label>Date</Label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="outline" className="w-full justify-start font-normal" data-testid="date-picker-btn">
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {format(date, "PPP")}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar mode="single" selected={date} onSelect={(d) => d && setDate(d)} initialFocus />
                  </PopoverContent>
                </Popover>
              </div>
            </div>
          </CardContent>
        </Card>

        {grade && section && (
          <Card className="border-0 shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg">{grade} {section} - {format(date, "EEEE, MMMM d, yyyy")}</CardTitle>
              <div className="flex gap-2">
                <Button variant="outline" onClick={markAllPresent} data-testid="mark-all-present-btn">Mark All Present</Button>
                <Button onClick={handleSaveAll} disabled={saving} className="bg-sky-500 hover:bg-sky-600" data-testid="save-attendance-btn">
                  {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                  Save Attendance
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              {loading ? <div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 animate-spin text-sky-500" /></div> : (
                <Table>
                  <TableHeader><TableRow className="bg-slate-50">
                    <TableHead>Index No</TableHead><TableHead>Student Name</TableHead><TableHead>Status</TableHead><TableHead>Actions</TableHead>
                  </TableRow></TableHeader>
                  <TableBody>
                    {students.map((student) => (
                      <TableRow key={student.id} data-testid={`attendance-row-${student.id}`}>
                        <TableCell className="font-medium">{student.index_no}</TableCell>
                        <TableCell>{student.first_name} {student.last_name}</TableCell>
                        <TableCell>{getStatusBadge(attendance[student.id])}</TableCell>
                        <TableCell>
                          <div className="flex gap-1">
                            <Button size="sm" variant={attendance[student.id] === "present" ? "default" : "outline"} className={attendance[student.id] === "present" ? "bg-green-500 hover:bg-green-600" : ""} onClick={() => handleStatusChange(student.id, "present")} data-testid={`present-btn-${student.id}`}>
                              <Check className="w-4 h-4" />
                            </Button>
                            <Button size="sm" variant={attendance[student.id] === "absent" ? "default" : "outline"} className={attendance[student.id] === "absent" ? "bg-red-500 hover:bg-red-600" : ""} onClick={() => handleStatusChange(student.id, "absent")} data-testid={`absent-btn-${student.id}`}>
                              <X className="w-4 h-4" />
                            </Button>
                            <Button size="sm" variant={attendance[student.id] === "late" ? "default" : "outline"} className={attendance[student.id] === "late" ? "bg-amber-500 hover:bg-amber-600" : ""} onClick={() => handleStatusChange(student.id, "late")} data-testid={`late-btn-${student.id}`}>
                              <Clock className="w-4 h-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                    {students.length === 0 && <TableRow><TableCell colSpan={4} className="text-center py-8 text-slate-500">No students found</TableCell></TableRow>}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}
