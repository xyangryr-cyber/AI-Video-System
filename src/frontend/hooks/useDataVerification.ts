import { useState, useCallback } from "react";
import type { DataPoint, TrustLevel, VerificationStatus } from "../types/dataVerification";

export function useDataVerification(initialDataPoints: DataPoint[]) {
  const [dataPoints, setDataPoints] = useState<DataPoint[]>(initialDataPoints);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const stats = {
    total: dataPoints.length,
    verified: dataPoints.filter((d) => d.verification_status === "verified").length,
    pending: dataPoints.filter((d) => d.verification_status === "pending").length,
    failed: dataPoints.filter((d) => d.verification_status === "failed").length,
    stale: dataPoints.filter((d) => d.verification_status === "stale").length,
  };

  const toggleExpand = useCallback((id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  }, []);

  const updatePoint = useCallback((id: string, updates: Partial<DataPoint>) => {
    setDataPoints((prev) =>
      prev.map((dp) => (dp.id === id ? { ...dp, ...updates } : dp)),
    );
  }, []);

  const manualConfirm = useCallback(
    (id: string) => {
      updatePoint(id, {
        trust_level: "user_verified" as TrustLevel,
        verification_status: "verified" as VerificationStatus,
        verified_at: new Date().toISOString(),
      });
    },
    [updatePoint],
  );

  const triggerVerify = useCallback(
    async (_id: string) => {
      // Calls POST /api/projects/{_id}/subtask with type=verify (handled by parent)
    },
    [],
  );

  return { dataPoints, stats, expandedId, toggleExpand, manualConfirm, triggerVerify };
}
