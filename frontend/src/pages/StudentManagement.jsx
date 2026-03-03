import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import { DashboardLayout } from "./DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { 
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow 
} from "../components/ui/table";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter
} from "../components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from "../components/ui/select";
import { Badge } from "../components/ui/badge";
import { toast } from "sonner";
import { 
  Plus, Search, Edit, Trash2, ChevronLeft, ChevronRight,
  Download, Eye, Loader2
} from "lucide-react";

const GRADES = ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12", "Grade 13"];
const SECTIONS = ["A", "B", "C", "D"];

export default function StudentManagement() {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState("");
  const [gradeFilter, setGradeFilter] = useState("");
  const [sectionFilter, setSectionFilter] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingStudent, setEditingStudent] = useState(null);
  const [viewStudent, setViewStudent] = useState(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    index_no: "",
    first_name: "",
    last_name: "",
    email: "",
    phone: "+94",
    grade: "",
    section: ""
  });

  useEffect(() => {
    fetchStudents();
  }, [page, search, gradeFilter, sectionFilter]);

  const fetchStudents = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page, limit: 20 });
      if (search) params.append("search", search);
      if (gradeFilter) params.append("grade", gradeFilter);
      if (sectionFilter) params.append("section", sectionFilter);

      const response = await axios.get(`${API}/students?${params}`);
      setStudents(response.data.students);
      setTotalPages(response.data.pages);
    } catch (error) {
      toast.error("Failed to fetch students");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingStudent) {
        await axios.put(`${API}/students/${editingStudent.id}`, formData);
        toast.success("Student updated successfully");
      } else {
        await axios.post(`${API}/students`, formData);
        toast.success("Student created successfully");
      }
      setDialogOpen(false);
      resetForm();
      fetchStudents();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Operation failed");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this student?")) return;
    try {
      await axios.delete(`${API}/students/${id}`);
      toast.success("Student deleted successfully");
      fetchStudents();
    } catch (error) {
      toast.error("Failed to delete student");
    }
  };

  const handleEdit = (student) => {
    setEditingStudent(student);
    setFormData({
      index_no: student.index_no,
      first_name: student.first_name,
      last_name: student.last_name,
      email: student.email,
      phone: student.phone,
      grade: student.grade,
      section: student.section
    });
    setDialogOpen(true);
  };

  const handleView = async (studentId) => {
    try {
      const response = await axios.get(`${API}/students/${studentId}`);
      setViewStudent(response.data);
      setViewDialogOpen(true);
    } catch (error) {
      toast.error("Failed to fetch student details");
    }
  };

  const resetForm = () => {
    setEditingStudent(null);
    setFormData({
      index_no: "",
      first_name: "",
      last_name: "",
      email: "",
      phone: "+94",
      grade: "",
      section: ""
    });
  };

  const handleExportPDF = async () => {
    try {
      const params = new URLSearchParams();
      if (gradeFilter) params.append("grade", gradeFilter);
      if (sectionFilter) params.append("section", sectionFilter);
      
      const response = await axios.get(`${API}/export/students/pdf?${params}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'students_report.pdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success("PDF exported successfully");
    } catch (error) {
      toast.error("Failed to export PDF");
    }
  };

  const handleExportExcel = async () => {
    try {
      const params = new URLSearchParams();
      if (gradeFilter) params.append("grade", gradeFilter);
      if (sectionFilter) params.append("section", sectionFilter);
      
      const response = await axios.get(`${API}/export/students/excel?${params}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'students_report.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success("Excel exported successfully");
    } catch (error) {
      toast.error("Failed to export Excel");
    }
  };

  return (
    <DashboardLayout title="Student Management">
      <div className="space-y-6 animate-fade-in" data-testid="student-management">
        {/* Actions Bar */}
        <div className="flex flex-col md:flex-row gap-4 justify-between">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="Search by name or Index No..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10 w-full sm:w-64"
                data-testid="search-students-input"
              />
            </div>
            <Select value={gradeFilter} onValueChange={(v) => setGradeFilter(v === "all" ? "" : v)}>
              <SelectTrigger className="w-full sm:w-40" data-testid="grade-filter">
                <SelectValue placeholder="All Grades" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Grades</SelectItem>
                {GRADES.map(g => (
                  <SelectItem key={g} value={g}>{g}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={sectionFilter} onValueChange={(v) => setSectionFilter(v === "all" ? "" : v)}>
              <SelectTrigger className="w-full sm:w-32" data-testid="section-filter">
                <SelectValue placeholder="Section" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Sections</SelectItem>
                {SECTIONS.map(s => (
                  <SelectItem key={s} value={s}>{s}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleExportPDF} data-testid="export-pdf-btn">
              <Download className="w-4 h-4 mr-2" /> PDF
            </Button>
            <Button variant="outline" onClick={handleExportExcel} data-testid="export-excel-btn">
              <Download className="w-4 h-4 mr-2" /> Excel
            </Button>
            <Dialog open={dialogOpen} onOpenChange={(open) => {
              setDialogOpen(open);
              if (!open) resetForm();
            }}>
              <DialogTrigger asChild>
                <Button className="bg-sky-500 hover:bg-sky-600" data-testid="add-student-btn">
                  <Plus className="w-4 h-4 mr-2" /> Add Student
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-md">
                <DialogHeader>
                  <DialogTitle>{editingStudent ? "Edit Student" : "Add New Student"}</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Index No</Label>
                      <Input
                        value={formData.index_no}
                        onChange={(e) => setFormData({...formData, index_no: e.target.value})}
                        placeholder="STU00001"
                        required
                        disabled={!!editingStudent}
                        data-testid="input-index-no"
                      />
                    </div>
                    <div>
                      <Label>First Name</Label>
                      <Input
                        value={formData.first_name}
                        onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                        required
                        data-testid="input-first-name"
                      />
                    </div>
                    <div>
                      <Label>Last Name</Label>
                      <Input
                        value={formData.last_name}
                        onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                        required
                        data-testid="input-last-name"
                      />
                    </div>
                    <div>
                      <Label>Email</Label>
                      <Input
                        type="email"
                        value={formData.email}
                        onChange={(e) => setFormData({...formData, email: e.target.value})}
                        required
                        data-testid="input-email"
                      />
                    </div>
                    <div>
                      <Label>Phone (+94)</Label>
                      <Input
                        value={formData.phone}
                        onChange={(e) => setFormData({...formData, phone: e.target.value})}
                        placeholder="+94771234567"
                        required
                        data-testid="input-phone"
                      />
                    </div>
                    <div>
                      <Label>Grade</Label>
                      <Select 
                        value={formData.grade} 
                        onValueChange={(v) => setFormData({...formData, grade: v})}
                      >
                        <SelectTrigger data-testid="select-grade">
                          <SelectValue placeholder="Select grade" />
                        </SelectTrigger>
                        <SelectContent>
                          {GRADES.map(g => (
                            <SelectItem key={g} value={g}>{g}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Section</Label>
                      <Select 
                        value={formData.section} 
                        onValueChange={(v) => setFormData({...formData, section: v})}
                      >
                        <SelectTrigger data-testid="select-section">
                          <SelectValue placeholder="Select section" />
                        </SelectTrigger>
                        <SelectContent>
                          {SECTIONS.map(s => (
                            <SelectItem key={s} value={s}>{s}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button type="submit" className="bg-sky-500 hover:bg-sky-600" data-testid="submit-student-btn">
                      {editingStudent ? "Update" : "Create"} Student
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Students Table */}
        <Card className="border-0 shadow-sm">
          <CardContent className="p-0">
            {loading ? (
              <div className="flex items-center justify-center h-64">
                <Loader2 className="w-8 h-8 animate-spin text-sky-500" />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-slate-50">
                      <TableHead className="font-semibold">Index No</TableHead>
                      <TableHead className="font-semibold">Name</TableHead>
                      <TableHead className="font-semibold">Email</TableHead>
                      <TableHead className="font-semibold">Phone</TableHead>
                      <TableHead className="font-semibold">Grade</TableHead>
                      <TableHead className="font-semibold">Section</TableHead>
                      <TableHead className="font-semibold text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {students.map((student) => (
                      <TableRow key={student.id} className="hover:bg-slate-50" data-testid={`student-row-${student.id}`}>
                        <TableCell className="font-medium">{student.index_no}</TableCell>
                        <TableCell>{student.first_name} {student.last_name}</TableCell>
                        <TableCell className="text-slate-600">{student.email}</TableCell>
                        <TableCell className="text-slate-600">{student.phone}</TableCell>
                        <TableCell>{student.grade}</TableCell>
                        <TableCell>{student.section}</TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Button 
                              variant="ghost" 
                              size="icon"
                              onClick={() => handleView(student.id)}
                              data-testid={`view-student-${student.id}`}
                            >
                              <Eye className="w-4 h-4 text-slate-600" />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="icon"
                              onClick={() => handleEdit(student)}
                              data-testid={`edit-student-${student.id}`}
                            >
                              <Edit className="w-4 h-4 text-slate-600" />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="icon"
                              onClick={() => handleDelete(student.id)}
                              data-testid={`delete-student-${student.id}`}
                            >
                              <Trash2 className="w-4 h-4 text-red-500" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                    {students.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center py-8 text-slate-500">
                          No students found
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Pagination */}
        <div className="flex items-center justify-between">
          <p className="text-sm text-slate-600">
            Page {page} of {totalPages}
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              data-testid="prev-page-btn"
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              data-testid="next-page-btn"
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* View Student Dialog */}
        <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
          <DialogContent className="sm:max-w-2xl">
            <DialogHeader>
              <DialogTitle>Student Details</DialogTitle>
            </DialogHeader>
            {viewStudent && (
              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-slate-500">Index No</p>
                    <p className="font-medium">{viewStudent.index_no}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Name</p>
                    <p className="font-medium">{viewStudent.first_name} {viewStudent.last_name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Grade & Section</p>
                    <p className="font-medium">{viewStudent.grade} - {viewStudent.section}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Contact</p>
                    <p className="font-medium">{viewStudent.phone}</p>
                  </div>
                </div>

                {/* Marks Table */}
                <div>
                  <h4 className="font-semibold mb-3">Term Marks</h4>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Subject</TableHead>
                        <TableHead>Term 1</TableHead>
                        <TableHead>Term 2</TableHead>
                        <TableHead>Term 3</TableHead>
                        <TableHead>Predicted</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {['Maths', 'Science', 'English', 'Tamil', 'ICT'].map(subject => {
                        const marks = viewStudent.marks?.filter(m => m.subject === subject) || [];
                        const prediction = viewStudent.predictions?.find(p => p.subject === subject);
                        const term1 = marks.find(m => m.term === 1)?.marks || '-';
                        const term2 = marks.find(m => m.term === 2)?.marks || '-';
                        const term3 = marks.find(m => m.term === 3)?.marks || '-';
                        
                        return (
                          <TableRow key={subject}>
                            <TableCell>{subject}</TableCell>
                            <TableCell>{term1}</TableCell>
                            <TableCell>{term2}</TableCell>
                            <TableCell>{term3}</TableCell>
                            <TableCell>{prediction?.predicted_term3 || '-'}</TableCell>
                            <TableCell>
                              {prediction?.is_at_risk ? (
                                <Badge className="at-risk-badge">At Risk</Badge>
                              ) : prediction ? (
                                <Badge className="on-track-badge">On Track</Badge>
                              ) : '-'}
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
