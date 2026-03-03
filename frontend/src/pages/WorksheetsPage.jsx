import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { API, useAuth } from "../App";
import { DashboardLayout } from "./DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Badge } from "../components/ui/badge";
import { toast } from "sonner";
import { Upload, FileText, Loader2, Save, Users, TrendingUp, TrendingDown, Minus, Check, X } from "lucide-react";

const GRADES = ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12", "Grade 13"];
const SECTIONS = ["A", "B", "C", "D"];

export default function WorksheetsPage() {
  const [students, setStudents] = useState([]);
  const [studentNotes, setStudentNotes] = useState({});
  const [studentFiles, setStudentFiles] = useState({});
  const [uploadingStudent, setUploadingStudent] = useState(null);
  const [loadingStudents, setLoadingStudents] = useState(false);
  const [savingAll, setSavingAll] = useState(false);
  const [teacherSubject, setTeacherSubject] = useState("");
  const [grade, setGrade] = useState("");
  const [section, setSection] = useState("");
  const [term, setTerm] = useState("1");
  const fileInputRefs = useRef({});

  useEffect(() => { 
    fetchTeacherInfo();
  }, []);

  useEffect(() => {
    if (grade && section && term) {
      fetchStudentsWithPerformance();
    }
  }, [grade, section, term, teacherSubject]);

  const fetchTeacherInfo = async () => {
    try {
      const response = await axios.get(`${API}/teacher/dashboard`);
      setTeacherSubject(response.data.teacher?.subject || "");
    } catch (error) { console.error(error); }
  };

  const fetchStudentsWithPerformance = async () => {
    if (!teacherSubject) return;
    setLoadingStudents(true);
    try {
      const response = await axios.get(`${API}/class-students/performance?grade=${grade}&section=${section}&term=${term}&subject=${teacherSubject}`);
      setStudents(response.data.students || []);
      
      // Load existing notes and files
      const notesMap = {};
      const filesMap = {};
      (response.data.students || []).forEach(s => {
        if (s.note) notesMap[s.id] = s.note;
        if (s.worksheet_file) filesMap[s.id] = { name: s.worksheet_file, uploaded: true };
      });
      setStudentNotes(notesMap);
      setStudentFiles(filesMap);
    } catch (error) { 
      console.error(error);
      setStudents([]);
    }
    finally { setLoadingStudents(false); }
  };

  const getPerformanceLevel = (marks, predicted) => {
    const score = predicted || marks || 0;
    if (score > 70) return { level: 1, label: "Level 1", color: "bg-green-500" };
    if (score >= 40) return { level: 2, label: "Level 2", color: "bg-amber-500" };
    return { level: 3, label: "Level 3", color: "bg-red-500" };
  };

  const getLevelBadge = (level) => {
    switch (level?.toString()) {
      case "1":
        return <Badge className="bg-green-500 text-white flex items-center gap-1"><TrendingUp className="w-3 h-3" />Level 1</Badge>;
      case "2":
        return <Badge className="bg-amber-500 text-white flex items-center gap-1"><Minus className="w-3 h-3" />Level 2</Badge>;
      case "3":
        return <Badge className="bg-red-500 text-white flex items-center gap-1"><TrendingDown className="w-3 h-3" />Level 3</Badge>;
      default:
        return <Badge variant="secondary">Unknown</Badge>;
    }
  };

  const handleFileChange = (studentId, e) => {
    const file = e.target.files?.[0];
    if (file) {
      setStudentFiles(prev => ({ ...prev, [studentId]: { file, name: file.name, uploaded: false } }));
    }
  };

  const handleSaveStudent = async (studentId) => {
    const note = studentNotes[studentId] || "";
    const fileData = studentFiles[studentId];
    
    setUploadingStudent(studentId);
    try {
      const formData = new FormData();
      formData.append("note", note);
      formData.append("term", term);
      formData.append("subject", teacherSubject);
      
      if (fileData?.file) {
        formData.append("file", fileData.file);
      }

      await axios.post(`${API}/students/${studentId}/worksheet`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      
      // Mark file as uploaded
      if (fileData?.file) {
        setStudentFiles(prev => ({ 
          ...prev, 
          [studentId]: { ...prev[studentId], uploaded: true, file: null } 
        }));
      }
      
      toast.success("Saved successfully");
    } catch (error) {
      toast.error("Failed to save");
      console.error(error);
    } finally {
      setUploadingStudent(null);
    }
  };

  const handleSaveAll = async () => {
    setSavingAll(true);
    let savedCount = 0;
    let errorCount = 0;

    for (const student of students) {
      const note = studentNotes[student.id];
      const fileData = studentFiles[student.id];
      
      // Only save if there's a note or a new file
      if (note || (fileData && !fileData.uploaded && fileData.file)) {
        try {
          const formData = new FormData();
          formData.append("note", note || "");
          formData.append("term", term);
          formData.append("subject", teacherSubject);
          
          if (fileData?.file && !fileData.uploaded) {
            formData.append("file", fileData.file);
          }

          await axios.post(`${API}/students/${student.id}/worksheet`, formData, {
            headers: { "Content-Type": "multipart/form-data" }
          });
          
          // Mark file as uploaded
          if (fileData?.file) {
            setStudentFiles(prev => ({ 
              ...prev, 
              [student.id]: { ...prev[student.id], uploaded: true, file: null } 
            }));
          }
          
          savedCount++;
        } catch (error) {
          errorCount++;
          console.error(`Error saving for student ${student.id}:`, error);
        }
      }
    }

    setSavingAll(false);
    
    if (savedCount > 0) {
      toast.success(`Saved ${savedCount} student records`);
    }
    if (errorCount > 0) {
      toast.error(`Failed to save ${errorCount} records`);
    }
    if (savedCount === 0 && errorCount === 0) {
      toast.info("No changes to save");
    }
  };

  const clearFile = (studentId) => {
    setStudentFiles(prev => {
      const updated = { ...prev };
      delete updated[studentId];
      return updated;
    });
    if (fileInputRefs.current[studentId]) {
      fileInputRefs.current[studentId].value = "";
    }
  };

  return (
    <DashboardLayout title="Worksheets">
      <div className="space-y-6 animate-fade-in" data-testid="worksheets-page">
        {/* Info Banner */}
        <Card className="border-0 shadow-sm bg-sky-50 border-l-4 border-l-sky-500">
          <CardContent className="p-4">
            <h3 className="font-semibold text-sky-800">Performance-Based Worksheets - {teacherSubject}</h3>
            <p className="text-sm text-sky-600 mt-1">
              Add notes and upload worksheets for individual students based on their performance levels:
            </p>
            <div className="flex flex-wrap gap-4 mt-3">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                <span className="text-sm text-slate-600"><strong>Level 1:</strong> Marks &gt; 70% (Advanced)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-amber-500"></div>
                <span className="text-sm text-slate-600"><strong>Level 2:</strong> Marks 40% - 70% (Intermediate)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500"></div>
                <span className="text-sm text-slate-600"><strong>Level 3:</strong> Marks &lt; 40% (Needs Support)</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Grade/Section/Term Selection */}
        <Card className="border-0 shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Users className="w-5 h-5 text-sky-500" />
              Select Class to View Students
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label>Grade</Label>
                <Select value={grade} onValueChange={setGrade}>
                  <SelectTrigger data-testid="select-grade"><SelectValue placeholder="Select grade" /></SelectTrigger>
                  <SelectContent>
                    {GRADES.map(g => <SelectItem key={g} value={g}>{g}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Division</Label>
                <Select value={section} onValueChange={setSection}>
                  <SelectTrigger data-testid="select-section"><SelectValue placeholder="Select division" /></SelectTrigger>
                  <SelectContent>
                    {SECTIONS.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                  </SelectContent>
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

        {/* Students List with Individual Worksheet Upload */}
        {grade && section && (
          <Card className="border-0 shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg">{grade} - {section} Students (Term {term})</CardTitle>
              <Button 
                onClick={handleSaveAll} 
                disabled={savingAll}
                className="bg-sky-500 hover:bg-sky-600"
                data-testid="save-all-btn"
              >
                {savingAll ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                Save All
              </Button>
            </CardHeader>
            <CardContent className="p-0">
              {loadingStudents ? (
                <div className="flex items-center justify-center h-32">
                  <Loader2 className="w-6 h-6 animate-spin text-sky-500" />
                </div>
              ) : students.length === 0 ? (
                <div className="p-8 text-center text-slate-500">
                  No students found for {grade} - {section}
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-slate-50">
                        <TableHead className="w-24">Index No</TableHead>
                        <TableHead className="w-40">Student Name</TableHead>
                        <TableHead className="w-24 text-center">Term {term} Marks</TableHead>
                        <TableHead className="w-24">Level</TableHead>
                        <TableHead className="w-64">Description / Notes</TableHead>
                        <TableHead className="w-56">Upload Worksheet</TableHead>
                        <TableHead className="w-24 text-center">Action</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {students.map((student) => {
                        const perf = getPerformanceLevel(student.marks, student.predicted);
                        const fileData = studentFiles[student.id];
                        const isUploading = uploadingStudent === student.id;
                        
                        return (
                          <TableRow key={student.id} className="hover:bg-slate-50">
                            <TableCell className="font-medium">{student.index_no}</TableCell>
                            <TableCell>{student.first_name} {student.last_name}</TableCell>
                            <TableCell className="font-semibold text-center">{student.marks ?? '-'}</TableCell>
                            <TableCell>{getLevelBadge(perf.level)}</TableCell>
                            <TableCell>
                              <Input
                                value={studentNotes[student.id] || ""}
                                onChange={(e) => setStudentNotes(prev => ({ ...prev, [student.id]: e.target.value }))}
                                placeholder="Add note for this student..."
                                className="w-full"
                                data-testid={`note-input-${student.id}`}
                              />
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                {fileData?.uploaded ? (
                                  <div className="flex items-center gap-2 text-green-600 text-sm">
                                    <FileText className="w-4 h-4" />
                                    <span className="truncate max-w-32">{fileData.name}</span>
                                    <Check className="w-4 h-4" />
                                  </div>
                                ) : fileData?.file ? (
                                  <div className="flex items-center gap-2 text-sky-600 text-sm">
                                    <FileText className="w-4 h-4" />
                                    <span className="truncate max-w-32">{fileData.name}</span>
                                    <button onClick={() => clearFile(student.id)} className="text-red-500 hover:text-red-700">
                                      <X className="w-4 h-4" />
                                    </button>
                                  </div>
                                ) : (
                                  <div className="relative">
                                    <input
                                      ref={el => fileInputRefs.current[student.id] = el}
                                      type="file"
                                      onChange={(e) => handleFileChange(student.id, e)}
                                      accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx"
                                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                      data-testid={`file-input-${student.id}`}
                                    />
                                    <Button variant="outline" size="sm" className="pointer-events-none">
                                      <Upload className="w-4 h-4 mr-1" />
                                      Choose File
                                    </Button>
                                  </div>
                                )}
                              </div>
                            </TableCell>
                            <TableCell className="text-center">
                              <Button
                                size="sm"
                                onClick={() => handleSaveStudent(student.id)}
                                disabled={isUploading}
                                className="bg-sky-500 hover:bg-sky-600"
                                data-testid={`save-btn-${student.id}`}
                              >
                                {isUploading ? (
                                  <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                  <Save className="w-4 h-4" />
                                )}
                              </Button>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}
