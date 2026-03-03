import { useState, useRef } from "react";
import axios from "axios";
import { API } from "../App";
import { DashboardLayout } from "./DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { toast } from "sonner";
import { Upload, Plus, Trash2, Loader2, Users, GraduationCap } from "lucide-react";
import * as XLSX from "xlsx";

const GRADES = ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12", "Grade 13"];
const SECTIONS = ["A", "B", "C", "D"];
const SUBJECTS = ["Maths", "Science", "English", "Tamil", "ICT"];

export default function BulkImportPage() {
  const [activeTab, setActiveTab] = useState("students");
  const [students, setStudents] = useState([{ index_no: "", first_name: "", last_name: "", email: "", phone: "+94", grade: "", section: "" }]);
  const [teachers, setTeachers] = useState([{ first_name: "", last_name: "", email: "", phone: "+94", subject: "" }]);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef(null);

  const addStudentRow = () => {
    setStudents([...students, { index_no: "", first_name: "", last_name: "", email: "", phone: "+94", grade: "", section: "" }]);
  };

  const addTeacherRow = () => {
    setTeachers([...teachers, { first_name: "", last_name: "", email: "", phone: "+94", subject: "" }]);
  };

  const removeStudentRow = (index) => {
    if (students.length > 1) setStudents(students.filter((_, i) => i !== index));
  };

  const removeTeacherRow = (index) => {
    if (teachers.length > 1) setTeachers(teachers.filter((_, i) => i !== index));
  };

  const updateStudent = (index, field, value) => {
    const updated = [...students];
    updated[index][field] = value;
    setStudents(updated);
  };

  const updateTeacher = (index, field, value) => {
    const updated = [...teachers];
    updated[index][field] = value;
    setTeachers(updated);
  };

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const data = new Uint8Array(event.target.result);
        const workbook = XLSX.read(data, { type: "array" });
        const sheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];
        const jsonData = XLSX.utils.sheet_to_json(worksheet);

        if (activeTab === "students") {
          const mappedData = jsonData.map(row => ({
            index_no: row["Index No"] || row["index_no"] || "",
            first_name: row["First Name"] || row["first_name"] || "",
            last_name: row["Last Name"] || row["last_name"] || "",
            email: row["Email"] || row["email"] || "",
            phone: row["Phone"] || row["phone"] || "+94",
            grade: row["Grade"] || row["grade"] || "",
            section: row["Section"] || row["section"] || ""
          }));
          setStudents(mappedData.length > 0 ? mappedData : students);
          toast.success(`Loaded ${mappedData.length} students from file`);
        } else {
          const mappedData = jsonData.map(row => ({
            first_name: row["First Name"] || row["first_name"] || "",
            last_name: row["Last Name"] || row["last_name"] || "",
            email: row["Email"] || row["email"] || "",
            phone: row["Phone"] || row["phone"] || "+94",
            subject: row["Subject"] || row["subject"] || ""
          }));
          setTeachers(mappedData.length > 0 ? mappedData : teachers);
          toast.success(`Loaded ${mappedData.length} teachers from file`);
        }
      } catch (error) {
        toast.error("Failed to parse file");
      }
    };
    reader.readAsArrayBuffer(file);
  };

  const handleImportStudents = async () => {
    const validStudents = students.filter(s => s.index_no && s.first_name && s.last_name && s.email && s.grade && s.section);
    if (validStudents.length === 0) { toast.error("No valid students to import"); return; }
    
    setLoading(true);
    try {
      const response = await axios.post(`${API}/import/students`, { students: validStudents });
      toast.success(`Imported ${response.data.imported} students`);
      if (response.data.errors?.length > 0) {
        response.data.errors.forEach(err => toast.error(err));
      }
      setStudents([{ index_no: "", first_name: "", last_name: "", email: "", phone: "+94", grade: "", section: "" }]);
    } catch (error) { toast.error("Import failed"); }
    finally { setLoading(false); }
  };

  const handleImportTeachers = async () => {
    const validTeachers = teachers.filter(t => t.first_name && t.last_name && t.email && t.subject);
    if (validTeachers.length === 0) { toast.error("No valid teachers to import"); return; }
    
    setLoading(true);
    try {
      const response = await axios.post(`${API}/import/teachers`, { teachers: validTeachers });
      toast.success(`Imported ${response.data.imported} teachers`);
      setTeachers([{ first_name: "", last_name: "", email: "", phone: "+94", subject: "" }]);
    } catch (error) { toast.error("Import failed"); }
    finally { setLoading(false); }
  };

  return (
    <DashboardLayout title="Bulk Import">
      <div className="space-y-6 animate-fade-in" data-testid="bulk-import-page">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full max-w-md grid-cols-2">
            <TabsTrigger value="students" className="flex items-center gap-2" data-testid="students-tab">
              <Users className="w-4 h-4" /> Students
            </TabsTrigger>
            <TabsTrigger value="teachers" className="flex items-center gap-2" data-testid="teachers-tab">
              <GraduationCap className="w-4 h-4" /> Teachers
            </TabsTrigger>
          </TabsList>

          <TabsContent value="students" className="mt-6">
            <Card className="border-0 shadow-sm">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-lg">Import Students</CardTitle>
                <div className="flex gap-2">
                  <input type="file" ref={fileInputRef} onChange={handleFileUpload} accept=".xlsx,.xls,.csv" className="hidden" />
                  <Button variant="outline" onClick={() => fileInputRef.current?.click()} data-testid="upload-file-btn">
                    <Upload className="w-4 h-4 mr-2" /> Upload Excel/CSV
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2 font-medium">Index No</th>
                        <th className="text-left p-2 font-medium">First Name</th>
                        <th className="text-left p-2 font-medium">Last Name</th>
                        <th className="text-left p-2 font-medium">Email</th>
                        <th className="text-left p-2 font-medium">Phone</th>
                        <th className="text-left p-2 font-medium">Grade</th>
                        <th className="text-left p-2 font-medium">Section</th>
                        <th className="p-2"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {students.map((student, index) => (
                        <tr key={index} className="border-b">
                          <td className="p-2"><Input value={student.index_no} onChange={(e) => updateStudent(index, "index_no", e.target.value)} placeholder="STU00001" className="w-28" data-testid={`student-index-${index}`} /></td>
                          <td className="p-2"><Input value={student.first_name} onChange={(e) => updateStudent(index, "first_name", e.target.value)} placeholder="First" className="w-24" /></td>
                          <td className="p-2"><Input value={student.last_name} onChange={(e) => updateStudent(index, "last_name", e.target.value)} placeholder="Last" className="w-24" /></td>
                          <td className="p-2"><Input value={student.email} onChange={(e) => updateStudent(index, "email", e.target.value)} placeholder="email@school.lk" className="w-40" /></td>
                          <td className="p-2"><Input value={student.phone} onChange={(e) => updateStudent(index, "phone", e.target.value)} placeholder="+94" className="w-32" /></td>
                          <td className="p-2">
                            <Select value={student.grade} onValueChange={(v) => updateStudent(index, "grade", v)}>
                              <SelectTrigger className="w-28"><SelectValue placeholder="Grade" /></SelectTrigger>
                              <SelectContent>{GRADES.map(g => <SelectItem key={g} value={g}>{g}</SelectItem>)}</SelectContent>
                            </Select>
                          </td>
                          <td className="p-2">
                            <Select value={student.section} onValueChange={(v) => updateStudent(index, "section", v)}>
                              <SelectTrigger className="w-20"><SelectValue placeholder="Sec" /></SelectTrigger>
                              <SelectContent>{SECTIONS.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent>
                            </Select>
                          </td>
                          <td className="p-2">
                            <Button variant="ghost" size="icon" onClick={() => removeStudentRow(index)} disabled={students.length === 1}>
                              <Trash2 className="w-4 h-4 text-red-500" />
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="flex justify-between">
                  <Button variant="outline" onClick={addStudentRow} data-testid="add-student-row-btn">
                    <Plus className="w-4 h-4 mr-2" /> Add Row
                  </Button>
                  <Button onClick={handleImportStudents} disabled={loading} className="bg-sky-500 hover:bg-sky-600" data-testid="import-students-btn">
                    {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Upload className="w-4 h-4 mr-2" />}
                    Import {students.filter(s => s.index_no).length} Students
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="teachers" className="mt-6">
            <Card className="border-0 shadow-sm">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-lg">Import Teachers</CardTitle>
                <Button variant="outline" onClick={() => fileInputRef.current?.click()} data-testid="upload-teacher-file-btn">
                  <Upload className="w-4 h-4 mr-2" /> Upload Excel/CSV
                </Button>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2 font-medium">First Name</th>
                        <th className="text-left p-2 font-medium">Last Name</th>
                        <th className="text-left p-2 font-medium">Email</th>
                        <th className="text-left p-2 font-medium">Phone</th>
                        <th className="text-left p-2 font-medium">Subject</th>
                        <th className="p-2"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {teachers.map((teacher, index) => (
                        <tr key={index} className="border-b">
                          <td className="p-2"><Input value={teacher.first_name} onChange={(e) => updateTeacher(index, "first_name", e.target.value)} placeholder="First" className="w-32" /></td>
                          <td className="p-2"><Input value={teacher.last_name} onChange={(e) => updateTeacher(index, "last_name", e.target.value)} placeholder="Last" className="w-32" /></td>
                          <td className="p-2"><Input value={teacher.email} onChange={(e) => updateTeacher(index, "email", e.target.value)} placeholder="email@school.lk" className="w-48" /></td>
                          <td className="p-2"><Input value={teacher.phone} onChange={(e) => updateTeacher(index, "phone", e.target.value)} placeholder="+94" className="w-32" /></td>
                          <td className="p-2">
                            <Select value={teacher.subject} onValueChange={(v) => updateTeacher(index, "subject", v)}>
                              <SelectTrigger className="w-32"><SelectValue placeholder="Subject" /></SelectTrigger>
                              <SelectContent>{SUBJECTS.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent>
                            </Select>
                          </td>
                          <td className="p-2">
                            <Button variant="ghost" size="icon" onClick={() => removeTeacherRow(index)} disabled={teachers.length === 1}>
                              <Trash2 className="w-4 h-4 text-red-500" />
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="flex justify-between">
                  <Button variant="outline" onClick={addTeacherRow} data-testid="add-teacher-row-btn">
                    <Plus className="w-4 h-4 mr-2" /> Add Row
                  </Button>
                  <Button onClick={handleImportTeachers} disabled={loading} className="bg-sky-500 hover:bg-sky-600" data-testid="import-teachers-btn">
                    {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Upload className="w-4 h-4 mr-2" />}
                    Import {teachers.filter(t => t.first_name).length} Teachers
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
