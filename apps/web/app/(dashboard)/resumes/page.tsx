"use client";
import { useState } from "react";
import { ResumeUploader } from "@/components/resume/ResumeUploader";
import { ResumeEditor } from "@/components/resume/ResumeEditor";
import { useResumes } from "@/hooks/useResumes";
import { Button } from "@/components/ui/button";
import { Plus, FileText, CheckCircle2 } from "lucide-react";
import { ResumeFormData } from "@/components/resume/schema";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";

export default function ResumesPage() {
  const [editingData, setEditingData] = useState<Partial<ResumeFormData> | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  
  const { data: resumesResponse, isLoading } = useResumes();
  // resumesApi.list() typically returns an array directly, but let's assume it returns { items: ... } or an array
  const resumes = Array.isArray(resumesResponse) ? resumesResponse : (resumesResponse as any)?.data || [];

  const handleStartScratch = () => {
    setEditingData({});
    setIsEditing(true);
  };

  const handleParsed = (data: ResumeFormData) => {
    setEditingData(data);
    setIsEditing(true);
  };

  const handleSuccess = () => {
    setIsEditing(false);
    setEditingData(null);
  };

  if (isEditing) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-2">Resume Profile</h1>
          <p className="text-muted-foreground">Review and edit your parsed resume details.</p>
        </div>
        <ResumeEditor initialData={editingData || {}} onSuccess={handleSuccess} />
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-2 bg-gradient-to-br from-foreground to-foreground/70 bg-clip-text text-transparent">Your Resumes</h1>
          <p className="text-muted-foreground">Manage your base resumes to personalize for applications.</p>
        </div>
        {resumes.length > 0 && (
          <Button onClick={handleStartScratch}>
            <Plus className="w-4 h-4 mr-2" />
            Build from scratch
          </Button>
        )}
      </div>

      {resumes.length === 0 && !isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <ResumeUploader onParsed={handleParsed} />
          <Card className="flex flex-col items-center justify-center text-center p-6 border-dashed bg-muted/10">
            <div className="p-4 bg-muted rounded-full mb-4">
              <FileText className="w-8 h-8 text-muted-foreground" />
            </div>
            <h3 className="font-semibold mb-2">No resume? No problem</h3>
            <p className="text-sm text-muted-foreground mb-6 max-w-xs">
              Manually fill in your experience, skills, and education to create a base profile.
            </p>
            <Button variant="outline" onClick={handleStartScratch}>
              Build from scratch
            </Button>
          </Card>
        </div>
      )}

      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Skeleton className="h-32 rounded-xl" />
          <Skeleton className="h-32 rounded-xl" />
        </div>
      )}

      {resumes.length > 0 && !isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
          {resumes.map((resume: any) => (
            <Card key={resume.id} className="hover:shadow-md transition-shadow cursor-pointer group">
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-2.5 bg-primary/10 rounded-lg text-primary">
                    <FileText className="w-6 h-6" />
                  </div>
                  {resume.is_base && (
                    <Badge variant="secondary" className="bg-primary/10 text-primary border-0 font-medium">
                      <CheckCircle2 className="w-3 h-3 mr-1" /> Base Profile
                    </Badge>
                  )}
                </div>
                <h3 className="font-semibold text-lg line-clamp-1">{resume.name}</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  Updated {new Date(resume.created_at).toLocaleDateString()}
                </p>
              </CardContent>
            </Card>
          ))}
          <div 
            onClick={handleStartScratch}
            className="flex flex-col items-center justify-center p-6 border-2 border-dashed rounded-xl cursor-pointer hover:bg-muted/50 transition-colors text-muted-foreground hover:text-foreground"
          >
            <Plus className="w-8 h-8 mb-2 opacity-50" />
            <span className="font-medium">Create New</span>
          </div>
        </div>
      )}
    </div>
  );
}
