"use client";
import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { UploadCloud, Loader2 } from "lucide-react";
import { useParseResume } from "@/hooks/useResumes";
import { ResumeFormData } from "./schema";

export function ResumeUploader({ onParsed }: { onParsed: (data: ResumeFormData) => void }) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const parseMutation = useParseResume();
  const [isDragging, setIsDragging] = useState(false);

  const handleFile = (file: File) => {
    parseMutation.mutate(file, {
      onSuccess: (data) => onParsed(data as unknown as ResumeFormData),
    });
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Upload Resume</CardTitle>
        <CardDescription>Upload a PDF or DOCX file to automatically extract your experience.</CardDescription>
      </CardHeader>
      <CardContent>
        <div
          className={`border-2 border-dashed rounded-xl p-10 text-center transition-all ${
            isDragging ? "border-primary bg-primary/5 scale-[0.99]" : "border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/50"
          }`}
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setIsDragging(false);
            const file = e.dataTransfer.files[0];
            if (file) handleFile(file);
          }}
        >
          <div className="flex flex-col items-center justify-center gap-4">
            <div className="p-4 bg-primary/10 rounded-full text-primary">
              {parseMutation.isPending ? <Loader2 className="w-8 h-8 animate-spin" /> : <UploadCloud className="w-8 h-8" />}
            </div>
            <div>
              <p className="text-sm font-medium">Drag & drop your resume here</p>
              <p className="text-xs text-muted-foreground mt-1">Supports PDF, DOCX up to 10MB</p>
            </div>
            <input
              type="file"
              className="hidden"
              ref={fileInputRef}
              accept=".pdf,.docx,.txt"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleFile(file);
              }}
            />
            <Button
              variant="secondary"
              onClick={() => fileInputRef.current?.click()}
              disabled={parseMutation.isPending}
            >
              {parseMutation.isPending ? "Parsing Document..." : "Browse Files"}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
