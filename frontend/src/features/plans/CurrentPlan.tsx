"use client";

import { ErrorState, Loading } from "@/components/ui/States";
import { useApi } from "@/lib/use-api";
import type { Plan } from "./api";
import { PlanView } from "./PlanView";

export function CurrentPlan() {
  const { data, error, reload } = useApi<Plan>("/plans/current");
  if (error) return <ErrorState error={error} onRetry={reload} />;
  if (!data) return <Loading />;
  return <PlanView plan={data} onChanged={reload} />;
}
