import type { Metadata } from "next";
import { WorkoutHistory } from "@/features/logs/WorkoutHistory";

export const metadata: Metadata = { title: "Istoric antrenamente" };

export default function WorkoutHistoryPage() {
  return (
    <>
      <h1 className="text-3xl font-black uppercase">Istoric antrenamente</h1>
      <WorkoutHistory />
    </>
  );
}
