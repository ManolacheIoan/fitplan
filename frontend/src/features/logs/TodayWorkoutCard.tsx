"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { DumbbellIcon } from "@/components/Icons";
import { Card } from "@/components/ui/Card";
import { ErrorState, Loading } from "@/components/ui/States";
import { errorMessage } from "@/lib/errors";
import { useApi } from "@/lib/use-api";
import { startWorkout, type Today } from "./api";

export function TodayWorkoutCard() {
  const router = useRouter();
  const { data, error, reload } = useApi<Today>("/workouts/today");
  const [pending, setPending] = useState(false);
  const [actionError, setActionError] = useState<string>();

  if (error) return <ErrorState error={error} onRetry={reload} />;
  if (!data) return <Loading />;

  async function start(dayId: number) {
    setPending(true);
    try {
      const workout = await startWorkout(dayId);
      router.push(`/antrenament?id=${workout.id}`);
    } catch (err) {
      setActionError(errorMessage(err));
      setPending(false);
    }
  }

  const { next_day: day, open_session_id: openId } = data;
  return (
    <Card className="hero-glow border-accent/40 flex flex-col gap-3 overflow-hidden">
      <p className="text-accent-text flex items-center gap-2 text-sm font-bold tracking-wide uppercase">
        <DumbbellIcon width={18} height={18} /> Antrenamentul de azi
      </p>
      <h2 className="text-2xl font-black uppercase">
        <span className="text-accent-text">Ziua {day.position}</span> · {day.name}
      </h2>
      <p className="text-muted">{day.exercises.map((e) => e.exercise.name).join(" · ")}</p>
      {actionError && (
        <p role="alert" className="text-danger font-semibold">
          {actionError}
        </p>
      )}
      {openId ? (
        <Button onClick={() => router.push(`/antrenament?id=${openId}`)}>Continuă antrenamentul</Button>
      ) : (
        <Button loading={pending} onClick={() => start(day.id)}>
          Începe antrenamentul
        </Button>
      )}
    </Card>
  );
}
