"use client";

import { useSearchParams } from "next/navigation";
import { ErrorState, Loading } from "@/components/ui/States";
import { useApi } from "@/lib/use-api";
import type { Plan } from "./api";
import { PlanView } from "./PlanView";

export function PlanDetails() {
  const id = Number(useSearchParams().get("id"));
  const { data, error, reload } = useApi<Plan>(Number.isInteger(id) && id > 0 ? `/plans/${id}` : null);
  if (error) return <ErrorState error={error} onRetry={reload} />;
  if (!data) return <Loading />;
  return <PlanView plan={data} />;
}
