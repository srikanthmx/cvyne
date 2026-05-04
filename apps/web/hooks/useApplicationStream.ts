"use client";
import { useEffect, useState } from "react";
import { applicationsApi } from "@/lib/api";

export type StatusEvent = {
  application_id: string;
  status: "queued" | "processing" | "submitted" | "failed" | "requires_human";
  step: string;
  progress: number;
  code?: string;
  message?: string;
};

export function useApplicationStream(applicationId: string | null) {
  const [event, setEvent] = useState<StatusEvent | null>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!applicationId) return;
    const es = applicationsApi.streamStatus(applicationId);

    es.addEventListener("status_update", (e) => {
      try {
        setEvent(JSON.parse((e as MessageEvent).data));
      } catch (err) {}
    });
    
    es.addEventListener("error", (e) => {
      try {
        setEvent(JSON.parse((e as MessageEvent).data));
      } catch (err) {}
    });

    es.addEventListener("done", () => {
      setDone(true);
      es.close();
    });

    es.onerror = () => es.close();

    return () => es.close();
  }, [applicationId]);

  return { event, done };
}
