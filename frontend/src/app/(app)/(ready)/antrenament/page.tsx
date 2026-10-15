import type { Metadata } from "next";
import { Suspense } from "react";
import { Loading } from "@/components/ui/States";
import { WorkoutLogger } from "@/features/logs/WorkoutLogger";

export const metadata: Metadata = { title: "Antrenament" };

export default function WorkoutPage() {
  return (
    <Suspense fallback={<Loading />}>
      <WorkoutLogger />
    </Suspense>
  );
}
