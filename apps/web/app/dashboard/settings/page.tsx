"use client";
import { useState, useEffect } from "react";
import { useSettingsStore, Provider, Theme } from "@/hooks/useSettingsStore";
import { useSaveApiKey } from "@/hooks/useSettingsApi";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Save, KeyRound, Palette, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

const THEMES: { id: Theme; name: string; previewClass: string }[] = [
  { id: "ats", name: "ATS Friendly", previewClass: "bg-white border-muted-foreground/30 text-black rounded-none shadow-none" },
  { id: "modern", name: "Modern", previewClass: "bg-background border-primary/20 text-foreground rounded-lg shadow-sm" },
  { id: "creative", name: "Creative", previewClass: "bg-gradient-to-br from-indigo-500/10 via-purple-500/10 to-pink-500/10 border-purple-500/30 rounded-2xl shadow-md" },
  { id: "portfolio", name: "Portfolio", previewClass: "bg-zinc-950 border-zinc-800 text-zinc-100 rounded-xl shadow-xl dark" },
];

export default function SettingsPage() {
  const { provider, defaultTheme, setProvider, setDefaultTheme } = useSettingsStore();
  const saveKeyMutation = useSaveApiKey();
  const [apiKey, setApiKey] = useState("");
  const [isClient, setIsClient] = useState(false);

  // Fix hydration mismatch for zustand store
  useEffect(() => {
    setIsClient(true);
  }, []);

  const handleSaveKey = () => {
    if (!apiKey.trim()) return;
    saveKeyMutation.mutate({ provider, api_key: apiKey.trim() }, {
      onSuccess: () => setApiKey("") // Clear field on success for security
    });
  };

  if (!isClient) return null;

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight mb-2">Settings</h1>
        <p className="text-muted-foreground">Configure your AI providers and default generation preferences.</p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2 mb-1">
            <KeyRound className="w-5 h-5 text-primary" />
            <CardTitle>LLM Provider & API Keys</CardTitle>
          </div>
          <CardDescription>
            Choose your preferred LLM for resume personalization and JD extraction. Your keys are encrypted at rest.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <Label>Active Provider</Label>
              <Select value={provider} onValueChange={(val) => setProvider(val as Provider)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a provider" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="anthropic">Anthropic (Claude 3.5 Sonnet)</SelectItem>
                  <SelectItem value="openai">OpenAI (GPT-4o)</SelectItem>
                  <SelectItem value="gemini">Google Gemini</SelectItem>
                  <SelectItem value="ollama">Ollama (Local / Open-Source)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-3">
              <Label>Save New API Key</Label>
              <div className="flex gap-2">
                <Input
                  type="password"
                  placeholder={`Enter ${provider} API Key...`}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="font-mono text-sm"
                />
                <Button onClick={handleSaveKey} disabled={!apiKey.trim() || saveKeyMutation.isPending}>
                  {saveKeyMutation.isPending ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                  Save
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Saving a new key will overwrite the existing key for {provider}.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2 mb-1">
            <Palette className="w-5 h-5 text-primary" />
            <CardTitle>Default CV Theme</CardTitle>
          </div>
          <CardDescription>
            Select the visual style that open-design will use by default when generating PDFs.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            {THEMES.map((theme) => {
              const isSelected = defaultTheme === theme.id;
              return (
                <button
                  key={theme.id}
                  onClick={() => setDefaultTheme(theme.id)}
                  className={cn(
                    "relative flex flex-col items-center text-left transition-all rounded-xl border-2 p-1 overflow-hidden",
                    isSelected ? "border-primary ring-2 ring-primary/20" : "border-transparent hover:border-border"
                  )}
                >
                  <div className={cn("w-full h-32 mb-3 border p-3 flex flex-col gap-2 overflow-hidden", theme.previewClass)}>
                    <div className="w-1/2 h-3 bg-current/20 rounded" />
                    <div className="w-3/4 h-2 bg-current/10 rounded mt-2" />
                    <div className="w-2/3 h-2 bg-current/10 rounded" />
                    <div className="w-full h-2 bg-current/10 rounded" />
                  </div>
                  <div className="w-full px-2 pb-2">
                    <p className="font-semibold text-sm">{theme.name}</p>
                  </div>
                  {isSelected && (
                    <div className="absolute top-3 right-3 bg-primary text-primary-foreground rounded-full p-1 shadow-sm">
                      <Save className="w-3 h-3" />
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
