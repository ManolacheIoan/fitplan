import type { Metadata } from "next";
import Link from "next/link";
import { TodayWorkoutCard } from "@/features/logs/TodayWorkoutCard";
import { TargetsCard } from "@/features/nutrition/TargetsCard";
import { Greeting } from "@/features/profile/Greeting";

export const metadata: Metadata = { title: "Azi" };

export default function TodayPage() {
  return (
    <>
      <Greeting />
      <TodayWorkoutCard />
      <TargetsCard />
      <Link
        href="/antrenament/istoric"
        className="text-accent-text text-center text-sm font-semibold underline"
      >
        Istoric antrenamente
      </Link>
    </>
  );
}
