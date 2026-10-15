import type { Metadata } from "next";
import { Progress } from "@/features/progress/Progress";

export const metadata: Metadata = { title: "Progres" };

export default function ProgressPage() {
  return (
    <>
      <h1 className="text-3xl font-black uppercase">Progres</h1>
      <Progress />
    </>
  );
}
