import type { Metadata } from "next";
import Link from "next/link";
import { CurrentPlan } from "@/features/plans/CurrentPlan";

export const metadata: Metadata = { title: "Plan" };

export default function PlanPage() {
  return (
    <>
      <div className="flex items-baseline justify-between">
        <h1 className="text-3xl font-black uppercase">Planul meu</h1>
        <Link href="/plan/istoric" className="text-accent-text text-sm font-semibold underline">
          Istoric
        </Link>
      </div>
      <CurrentPlan />
    </>
  );
}
