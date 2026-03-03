import { useState } from "react";
import axios from "axios";
import { API } from "../App";
import { DashboardLayout } from "./DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Label } from "../components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { toast } from "sonner";
import { Download, FileText, FileSpreadsheet, Loader2 } from "lucide-react";

const GRADES = ["", "Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11"];
const SECTIONS = ["", "A", "B", "C", "D"];

export default function ReportsPage() {
  const [grade, setGrade] = useState("");
  const [section, setSection] = useState("");
  const [loading, setLoading] = useState({ pdf: false, excel: false });

  const handleExportPDF = async () => {
    setLoading(prev => ({ ...prev, pdf: true }));
    try {
      const params = new URLSearchParams();
      if (grade) params.append("grade", grade);
      if (section) params.append("section", section);
      
      const response = await axios.get(`${API}/export/students/pdf?${params}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'students_report.pdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success("PDF exported successfully");
    } catch (error) { toast.error("Failed to export PDF"); }
    finally { setLoading(prev => ({ ...prev, pdf: false })); }
  };

  const handleExportExcel = async () => {
    setLoading(prev => ({ ...prev, excel: true }));
    try {
      const params = new URLSearchParams();
      if (grade) params.append("grade", grade);
      if (section) params.append("section", section);
      
      const response = await axios.get(`${API}/export/students/excel?${params}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'students_report.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success("Excel exported successfully");
    } catch (error) { toast.error("Failed to export Excel"); }
    finally { setLoading(prev => ({ ...prev, excel: false })); }
  };

  return (
    <DashboardLayout title="Reports">
      <div className="space-y-6 animate-fade-in" data-testid="reports-page">
        <Card className="border-0 shadow-sm">
          <CardHeader><CardTitle className="text-lg">Export Student Reports</CardTitle></CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label>Filter by Grade (Optional)</Label>
                <Select value={grade || "all"} onValueChange={(v) => setGrade(v === "all" ? "" : v)}>
                  <SelectTrigger data-testid="select-grade"><SelectValue placeholder="All Grades" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Grades</SelectItem>
                    {GRADES.slice(1).map(g => <SelectItem key={g} value={g}>{g}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Filter by Section (Optional)</Label>
                <Select value={section || "all"} onValueChange={(v) => setSection(v === "all" ? "" : v)}>
                  <SelectTrigger data-testid="select-section"><SelectValue placeholder="All Sections" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Sections</SelectItem>
                    {SECTIONS.slice(1).map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div className="flex flex-wrap gap-4">
              <Button onClick={handleExportPDF} disabled={loading.pdf} className="bg-red-500 hover:bg-red-600" data-testid="export-pdf-btn">
                {loading.pdf ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <FileText className="w-4 h-4 mr-2" />}
                Export as PDF
              </Button>
              <Button onClick={handleExportExcel} disabled={loading.excel} className="bg-green-500 hover:bg-green-600" data-testid="export-excel-btn">
                {loading.excel ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <FileSpreadsheet className="w-4 h-4 mr-2" />}
                Export as Excel
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="border-0 shadow-sm card-hover cursor-pointer" onClick={handleExportPDF}>
            <CardContent className="p-8 flex flex-col items-center text-center">
              <div className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center mb-4">
                <FileText className="w-8 h-8 text-red-500" />
              </div>
              <h3 className="font-semibold text-lg mb-2">PDF Report</h3>
              <p className="text-sm text-slate-500">Download a formatted PDF report of all students with their details</p>
            </CardContent>
          </Card>
          
          <Card className="border-0 shadow-sm card-hover cursor-pointer" onClick={handleExportExcel}>
            <CardContent className="p-8 flex flex-col items-center text-center">
              <div className="w-16 h-16 rounded-full bg-green-50 flex items-center justify-center mb-4">
                <FileSpreadsheet className="w-8 h-8 text-green-500" />
              </div>
              <h3 className="font-semibold text-lg mb-2">Excel Report</h3>
              <p className="text-sm text-slate-500">Download an Excel spreadsheet with student data for analysis</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
