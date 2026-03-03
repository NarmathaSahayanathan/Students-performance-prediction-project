import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import { DashboardLayout } from "./DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { toast } from "sonner";
import { Save, Search, Loader2 } from "lucide-react";

const SUBJECTS = ["Maths", "Science", "English", "Tamil", "ICT"];
const GRADES = ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12", "Grade 13"];
const SECTIONS = ["A", "B", "C", "D"];

export default function MarksEntry() {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [grade, setGrade] = useState("");
  const [section, setSection] = useState("");
  const [subject, setSubject] = useState("");
  const [term, setTerm] = useState("");
  const [marks, setMarks] = useState({});

  const fetchStudents = async () => {
    if (!grade || !section) return;
    setLoading(true);
    try {
      const response = await axios.get(`${API}/students?grade=${grade}&section=${section}&limit=100`);
      setStudents(response.data.students);
      
      // Fetch existing marks
      if (subject && term) {
        const marksResponse = await axios.get(`${API}/marks?subject=${subject}&term=${term}`);
        const marksMap = {};
        marksResponse.data.forEach(m => { marksMap[m.student_id] = m.marks; });
        setMarks(marksMap);
      }
    } catch (error) { toast.error("Failed to fetch students"); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchStudents(); }, [grade, section, subject, term]);

  const handleMarkChange = (studentId, value) => {
    const numValue = parseFloat(value);
    if (value === "" || (numValue >= 0 && numValue <= 100)) {
      setMarks(prev => ({ ...prev, [studentId]: value === "" ? "" : numValue }));
    }
  };

  const handleSaveAll = async () => {
    if (!subject || !term) { toast.error("Please select subject and term"); return; }
    setSaving(true);
    try {
      const marksData = Object.entries(marks)
        .filter(([_, value]) => value !== "" && value !== undefined)
        .map(([studentId, value]) => ({ student_id: parseInt(studentId), subject, term: parseInt(term), marks: value }));
      
      if (marksData.length === 0) { toast.error("No marks to save"); setSaving(false); return; }
      
      await axios.post(`${API}/marks/bulk`, marksData);
      toast.success(`Saved ${marksData.length} marks successfully`);
    } catch (error) { toast.error("Failed to save marks"); }
    finally { setSaving(false); }
  };

  return (
    <DashboardLayout title="Marks Entry">
      <div className="space-y-6 animate-fade-in" data-testid="marks-entry">
        <Card className="border-0 shadow-sm">
          <CardHeader><CardTitle className="text-lg">Select Class & Subject</CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
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
                <Label>Subject</Label>
                <Select value={subject} onValueChange={setSubject}>
                  <SelectTrigger data-testid="select-subject"><SelectValue placeholder="Select subject" /></SelectTrigger>
                  <SelectContent>{SUBJECTS.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div>
                <Label>Term</Label>
                <Select value={term} onValueChange={setTerm}>
                  <SelectTrigger data-testid="select-term"><SelectValue placeholder="Select term" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">Term 1</SelectItem>
                    <SelectItem value="2">Term 2</SelectItem>
                    <SelectItem value="3">Term 3</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {grade && section && (
          <Card className="border-0 shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg">Students - {grade} {section}</CardTitle>
              <Button onClick={handleSaveAll} disabled={saving || !subject || !term} className="bg-sky-500 hover:bg-sky-600" data-testid="save-marks-btn">
                {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                Save All Marks
              </Button>
            </CardHeader>
            <CardContent className="p-0">
              {loading ? <div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 animate-spin text-sky-500" /></div> : (
                <Table>
                  <TableHeader><TableRow className="bg-slate-50">
                    <TableHead>Index No</TableHead><TableHead>Student Name</TableHead><TableHead className="w-32">Marks (0-100)</TableHead>
                  </TableRow></TableHeader>
                  <TableBody>
                    {students.map((student) => (
                      <TableRow key={student.id} data-testid={`marks-row-${student.id}`}>
                        <TableCell className="font-medium">{student.index_no}</TableCell>
                        <TableCell>{student.first_name} {student.last_name}</TableCell>
                        <TableCell>
                          <input
                            type="text"
                            inputMode="numeric"
                            pattern="[0-9]*"
                            value={marks[student.id] ?? ""}
                            onChange={(e) => handleMarkChange(student.id, e.target.value)}
                            className="w-24 h-10 px-3 rounded-md border border-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
                            placeholder="0-100"
                            disabled={!subject || !term}
                            data-testid={`marks-input-${student.id}`}
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                    {students.length === 0 && <TableRow><TableCell colSpan={3} className="text-center py-8 text-slate-500">No students found</TableCell></TableRow>}
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
