import type { Metadata } from "next";
import { Suspense } from "react";
import { Loading } from "@/components/ui/States";
import { PlanDetails } from "@/features/plans/PlanDetails";

export const metadata: Metadata = { title: "Detalii plan" };

export default function PlanDetailsPage() {
  return (
    <>
      <h1 className="text-3xl font-black uppercase">Detalii plan</h1>
      <Suspense fallback={<Loading />}>
        <PlanDetails />
      </Suspense>
    </>
  );
}
