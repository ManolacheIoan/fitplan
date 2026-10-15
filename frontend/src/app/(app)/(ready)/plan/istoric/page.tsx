import type { Metadata } from "next";
import { PlanHistory } from "@/features/plans/PlanHistory";

export const metadata: Metadata = { title: "Istoric planuri" };

export default function PlanHistoryPage() {
  return (
    <>
      <h1 className="text-3xl font-black uppercase">Istoric planuri</h1>
      <p className="text-muted">Un plan nou se generează când schimbi zilele, obiectivul sau experiența.</p>
      <PlanHistory />
    </>
  );
}
