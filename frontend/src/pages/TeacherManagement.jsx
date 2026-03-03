import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import { DashboardLayout } from "./DashboardLayout";
import { Card, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "../components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Badge } from "../components/ui/badge";
import { toast } from "sonner";
import { Plus, Search, Edit, Trash2, ChevronLeft, ChevronRight, Loader2 } from "lucide-react";

const SUBJECTS = ["Maths", "Science", "English", "Tamil", "ICT"];

export default function TeacherManagement() {
  const [teachers, setTeachers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState("");
  const [subjectFilter, setSubjectFilter] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingTeacher, setEditingTeacher] = useState(null);
  const [formData, setFormData] = useState({
    first_name: "", last_name: "", email: "", phone: "+94", subject: ""
  });

  useEffect(() => { fetchTeachers(); }, [page, search, subjectFilter]);

  const fetchTeachers = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page, limit: 20 });
      if (search) params.append("search", search);
      if (subjectFilter) params.append("subject", subjectFilter);
      const response = await axios.get(`${API}/teachers?${params}`);
      setTeachers(response.data.teachers);
      setTotalPages(response.data.pages);
    } catch (error) { toast.error("Failed to fetch teachers"); }
    finally { setLoading(false); }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingTeacher) {
        await axios.put(`${API}/teachers/${editingTeacher.id}`, formData);
        toast.success("Teacher updated successfully");
      } else {
        await axios.post(`${API}/teachers`, formData);
        toast.success("Teacher created successfully");
      }
      setDialogOpen(false); resetForm(); fetchTeachers();
    } catch (error) { toast.error(error.response?.data?.detail || "Operation failed"); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure?")) return;
    try { await axios.delete(`${API}/teachers/${id}`); toast.success("Teacher deleted"); fetchTeachers(); }
    catch (error) { toast.error("Failed to delete teacher"); }
  };

  const handleEdit = (teacher) => {
    setEditingTeacher(teacher);
    setFormData({ first_name: teacher.first_name, last_name: teacher.last_name, email: teacher.email, phone: teacher.phone, subject: teacher.subject });
    setDialogOpen(true);
  };

  const resetForm = () => { setEditingTeacher(null); setFormData({ first_name: "", last_name: "", email: "", phone: "+94", subject: "" }); };

  return (
    <DashboardLayout title="Teacher Management">
      <div className="space-y-6 animate-fade-in" data-testid="teacher-management">
        <div className="flex flex-col md:flex-row gap-4 justify-between">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input placeholder="Search teachers..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-10 w-full sm:w-64" data-testid="search-teachers-input" />
            </div>
            <Select value={subjectFilter} onValueChange={(v) => setSubjectFilter(v === "all" ? "" : v)}>
              <SelectTrigger className="w-full sm:w-40" data-testid="subject-filter">
                <SelectValue placeholder="All Subjects" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Subjects</SelectItem>
                {SUBJECTS.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
            <DialogTrigger asChild>
              <Button className="bg-sky-500 hover:bg-sky-600" data-testid="add-teacher-btn"><Plus className="w-4 h-4 mr-2" /> Add Teacher</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>{editingTeacher ? "Edit Teacher" : "Add New Teacher"}</DialogTitle></DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div><Label>First Name</Label><Input value={formData.first_name} onChange={(e) => setFormData({...formData, first_name: e.target.value})} required data-testid="input-teacher-first-name" /></div>
                  <div><Label>Last Name</Label><Input value={formData.last_name} onChange={(e) => setFormData({...formData, last_name: e.target.value})} required data-testid="input-teacher-last-name" /></div>
                  <div><Label>Email</Label><Input type="email" value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} required data-testid="input-teacher-email" /></div>
                  <div><Label>Phone (+94)</Label><Input value={formData.phone} onChange={(e) => setFormData({...formData, phone: e.target.value})} required data-testid="input-teacher-phone" /></div>
                  <div className="col-span-2">
                    <Label>Subject</Label>
                    <Select value={formData.subject} onValueChange={(v) => setFormData({...formData, subject: v})}>
                      <SelectTrigger data-testid="select-teacher-subject"><SelectValue placeholder="Select subject" /></SelectTrigger>
                      <SelectContent>{SUBJECTS.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent>
                    </Select>
                  </div>
                </div>
                <DialogFooter><Button type="submit" className="bg-sky-500 hover:bg-sky-600" data-testid="submit-teacher-btn">{editingTeacher ? "Update" : "Create"}</Button></DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        <Card className="border-0 shadow-sm">
          <CardContent className="p-0">
            {loading ? <div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 animate-spin text-sky-500" /></div> : (
              <Table>
                <TableHeader><TableRow className="bg-slate-50">
                  <TableHead>Name</TableHead><TableHead>Email</TableHead><TableHead>Phone</TableHead><TableHead>Subject</TableHead><TableHead className="text-right">Actions</TableHead>
                </TableRow></TableHeader>
                <TableBody>
                  {teachers.map((teacher) => (
                    <TableRow key={teacher.id} className="hover:bg-slate-50" data-testid={`teacher-row-${teacher.id}`}>
                      <TableCell className="font-medium">{teacher.first_name} {teacher.last_name}</TableCell>
                      <TableCell className="text-slate-600">{teacher.email}</TableCell>
                      <TableCell className="text-slate-600">{teacher.phone}</TableCell>
                      <TableCell><Badge variant="secondary">{teacher.subject}</Badge></TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="icon" onClick={() => handleEdit(teacher)} data-testid={`edit-teacher-${teacher.id}`}><Edit className="w-4 h-4 text-slate-600" /></Button>
                        <Button variant="ghost" size="icon" onClick={() => handleDelete(teacher.id)} data-testid={`delete-teacher-${teacher.id}`}><Trash2 className="w-4 h-4 text-red-500" /></Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {teachers.length === 0 && <TableRow><TableCell colSpan={5} className="text-center py-8 text-slate-500">No teachers found</TableCell></TableRow>}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        <div className="flex items-center justify-between">
          <p className="text-sm text-slate-600">Page {page} of {totalPages}</p>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} data-testid="prev-page-btn"><ChevronLeft className="w-4 h-4" /></Button>
            <Button variant="outline" size="sm" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages} data-testid="next-page-btn"><ChevronRight className="w-4 h-4" /></Button>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
