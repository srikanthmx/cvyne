"use client";
import { useForm, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { resumeSchema, type ResumeFormData } from "./schema";
import { useCreateResume } from "@/hooks/useResumes";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Trash2, Plus, Save, Loader2 } from "lucide-react";

interface ResumeEditorProps {
  initialData?: Partial<ResumeFormData>;
  onSuccess?: () => void;
}

export function ResumeEditor({ initialData, onSuccess }: ResumeEditorProps) {
  const form = useForm<ResumeFormData>({
    resolver: zodResolver(resumeSchema),
    defaultValues: {
      name: initialData?.name || "",
      email: initialData?.email || "",
      phone: initialData?.phone || "",
      location: initialData?.location || "",
      summary: initialData?.summary || "",
      experience: initialData?.experience || [],
      education: initialData?.education || [],
      skills: initialData?.skills || [],
    },
  });

  const { fields: expFields, append: appendExp, remove: removeExp } = useFieldArray({
    control: form.control,
    name: "experience",
  });

  const createMutation = useCreateResume();

  const onSubmit = form.handleSubmit((data) => {
    // Save to API
    createMutation.mutate(
      {
        name: data.name || "Untitled Resume",
        data: data as any,
        is_base: true,
      },
      {
        onSuccess: () => onSuccess?.(),
      }
    );
  });

  return (
    <Form {...form}>
      <form onSubmit={onSubmit} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Personal Details</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField control={form.control} name="name" render={({ field }: { field: any }) => (
              <FormItem><FormLabel>Full Name</FormLabel><FormControl><Input placeholder="John Doe" {...field} /></FormControl><FormMessage /></FormItem>
            )} />
            <FormField control={form.control} name="email" render={({ field }: { field: any }) => (
              <FormItem><FormLabel>Email</FormLabel><FormControl><Input placeholder="john@example.com" {...field} /></FormControl><FormMessage /></FormItem>
            )} />
            <FormField control={form.control} name="phone" render={({ field }: { field: any }) => (
              <FormItem><FormLabel>Phone</FormLabel><FormControl><Input placeholder="+1 234 567 890" {...field} value={field.value || ""} /></FormControl><FormMessage /></FormItem>
            )} />
            <FormField control={form.control} name="location" render={({ field }: { field: any }) => (
              <FormItem><FormLabel>Location</FormLabel><FormControl><Input placeholder="City, Country" {...field} value={field.value || ""} /></FormControl><FormMessage /></FormItem>
            )} />
            <FormField control={form.control} name="summary" render={({ field }: { field: any }) => (
              <FormItem className="md:col-span-2"><FormLabel>Professional Summary</FormLabel><FormControl><Textarea placeholder="A brief summary of your expertise..." className="h-24" {...field} value={field.value || ""} /></FormControl><FormMessage /></FormItem>
            )} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Experience</CardTitle>
            <Button type="button" variant="outline" size="sm" onClick={() => appendExp({ company: "", role: "", start: "", end: "", bullets: [] })}>
              <Plus className="w-4 h-4 mr-2" /> Add Role
            </Button>
          </CardHeader>
          <CardContent className="space-y-6">
            {expFields.map((field, index) => (
              <div key={field.id} className="p-4 border rounded-lg bg-muted/20 relative group">
                <Button type="button" variant="ghost" size="icon" className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity text-destructive" onClick={() => removeExp(index)}>
                  <Trash2 className="w-4 h-4" />
                </Button>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <FormField control={form.control} name={`experience.${index}.company`} render={({ field }: { field: any }) => (
                    <FormItem><FormLabel>Company</FormLabel><FormControl><Input placeholder="Acme Corp" {...field} /></FormControl><FormMessage /></FormItem>
                  )} />
                  <FormField control={form.control} name={`experience.${index}.role`} render={({ field }: { field: any }) => (
                    <FormItem><FormLabel>Role</FormLabel><FormControl><Input placeholder="Software Engineer" {...field} /></FormControl><FormMessage /></FormItem>
                  )} />
                  <FormField control={form.control} name={`experience.${index}.start`} render={({ field }: { field: any }) => (
                    <FormItem><FormLabel>Start Date</FormLabel><FormControl><Input placeholder="Jan 2020" {...field} /></FormControl><FormMessage /></FormItem>
                  )} />
                  <FormField control={form.control} name={`experience.${index}.end`} render={({ field }: { field: any }) => (
                    <FormItem><FormLabel>End Date</FormLabel><FormControl><Input placeholder="Present" {...field} value={field.value || ""} /></FormControl><FormMessage /></FormItem>
                  )} />
                </div>
                <FormField control={form.control} name={`experience.${index}.bullets`} render={({ field }: { field: any }) => (
                  <FormItem>
                    <FormLabel>Achievements (one per line)</FormLabel>
                    <FormControl>
                      <Textarea 
                        className="h-32" 
                        placeholder="• Built a scalable backend..." 
                        value={field.value?.join('\n') || ""} 
                        onChange={(e) => field.onChange(e.target.value.split('\n').filter(s => s.trim()))} 
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
              </div>
            ))}
            {expFields.length === 0 && <p className="text-sm text-muted-foreground text-center py-4">No experience added yet.</p>}
          </CardContent>
        </Card>

        <div className="flex justify-end gap-4">
          <Button type="button" variant="ghost" onClick={() => onSuccess?.()}>Cancel</Button>
          <Button type="submit" disabled={createMutation.isPending}>
            {createMutation.isPending ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
            Save Resume Profile
          </Button>
        </div>
      </form>
    </Form>
  );
}
