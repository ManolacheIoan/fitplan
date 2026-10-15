"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ErrorState, Loading } from "@/components/ui/States";
import type { Exercise } from "@/features/plans/api";
import { reps as repRange } from "@/features/plans/labels";
import { formatDateTime, nf1 } from "@/lib/dates";
import { errorMessage } from "@/lib/errors";
import { useApi } from "@/lib/use-api";
import {
  addSet,
  deleteSet,
  finishWorkout,
  updateSet,
  type SetLog,
  type Workout,
  type WorkoutExercise,
} from "./api";

/** How a set is measured: held for time, or reps with an external / extra load. */
type Measure = { timed: boolean; bodyweight: boolean };

const measureOf = (exercise: Exercise): Measure => ({
  timed: exercise.unit === "seconds",
  bodyweight: exercise.equipment === "bodyweight",
});

function setText(weightKg: string | number, reps: number, m: Measure): string {
  if (m.timed) return `${reps} s`;
  const kg = Number(weightKg);
  if (m.bodyweight) return kg > 0 ? `${reps} rep. +${nf1.format(kg)} kg` : `${reps} rep.`;
  return `${nf1.format(kg)} kg × ${reps}`;
}

function suggestionText({ suggestion, planned }: WorkoutExercise): string {
  const m = measureOf(planned.exercise);
  const kg = suggestion.weight_kg ? nf1.format(Number(suggestion.weight_kg)) : "";
  const top = m.timed ? `${planned.reps_max} de secunde` : `${planned.reps_max} repetări`;
  switch (suggestion.kind) {
    case "first_time":
      if (m.timed) return `Prima dată: menține poziția cât poți cu tehnică bună, până la ${top}.`;
      if (m.bodyweight) return `Prima dată: fă câte repetări poți cu tehnică bună, până la ${top}.`;
      return `Prima dată: alege o greutate cu care poți face ${top} cu tehnică bună.`;
    case "add_weight":
      return `Data trecută ai atins ${top} la toate seriile. Încearcă ${kg} kg.`;
    case "add_reps":
      if (m.timed) return "Încearcă să menții poziția câteva secunde în plus pe serie.";
      return m.bodyweight || Number(suggestion.weight_kg) === 0
        ? "Încearcă o repetare în plus pe serie."
        : `Rămâi la ${kg} kg și încearcă o repetare în plus pe serie.`;
    case "max_reached":
      return m.timed
        ? `Ai atins ${top}. Poți trece la o variantă mai grea (de ex. cu un picior ridicat).`
        : `Ai atins ${top} la toate seriile. Poți adăuga greutate (centură/vestă) sau o variantă mai grea.`;
  }
}

const numberInput =
  "min-h-12 w-full rounded-xl border border-border bg-surface-2 px-3 text-center text-lg font-bold text-fg";

/** Weight + reps inputs, used both for adding and editing a set. */
function SetForm({
  measure,
  initialWeight,
  initialReps,
  submitLabel,
  onSubmit,
  onCancel,
}: {
  measure: Measure;
  initialWeight: string;
  initialReps: string;
  submitLabel: string;
  onSubmit: (weight: number, reps: number) => Promise<void>;
  onCancel?: () => void;
}) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string>();

  async function handle(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setPending(true);
    setError(undefined);
    try {
      await onSubmit(Number(form.get("weight")), Number(form.get("reps")));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={handle} className="flex flex-col gap-2">
      <div
        className={`grid items-end gap-2 ${measure.timed ? "grid-cols-[1fr_auto]" : "grid-cols-[1fr_1fr_auto]"}`}
      >
        {measure.timed ? (
          <input type="hidden" name="weight" value="0" />
        ) : (
          <label className="text-muted flex flex-col gap-1 text-xs font-semibold">
            {measure.bodyweight ? "Greutate extra (kg)" : "Greutate (kg)"}
            <input
              name="weight"
              type="number"
              inputMode="decimal"
              min={0}
              max={500}
              step={0.25}
              required
              defaultValue={initialWeight}
              className={numberInput}
            />
          </label>
        )}
        <label className="text-muted flex flex-col gap-1 text-xs font-semibold">
          {measure.timed ? "Secunde" : "Repetări"}
          <input
            name="reps"
            type="number"
            inputMode="numeric"
            min={1}
            max={300}
            step={1}
            required
            defaultValue={initialReps}
            className={numberInput}
          />
        </label>
        <Button type="submit" loading={pending} className="px-4">
          {submitLabel}
        </Button>
      </div>
      {onCancel && (
        <Button type="button" variant="ghost" onClick={onCancel}>
          Renunță
        </Button>
      )}
      {error && (
        <p role="alert" className="text-danger text-sm font-semibold">
          {error}
        </p>
      )}
    </form>
  );
}

function SetRow({ set, measure, onChange }: { set: SetLog; measure: Measure; onChange: () => void }) {
  const [editing, setEditing] = useState(false);
  if (editing) {
    return (
      <li>
        <SetForm
          measure={measure}
          initialWeight={set.weight_kg}
          initialReps={String(set.reps)}
          submitLabel="Salvează"
          onCancel={() => setEditing(false)}
          onSubmit={async (weight, reps) => {
            await updateSet(set.id, weight, reps);
            setEditing(false);
            onChange();
          }}
        />
      </li>
    );
  }
  return (
    <li className="bg-surface-2 flex min-h-12 items-center justify-between gap-2 rounded-xl px-3">
      <span className="font-bold">
        Seria {set.set_number}: {setText(set.weight_kg, set.reps, measure)}
      </span>
      <span className="flex gap-1">
        <button
          type="button"
          onClick={() => setEditing(true)}
          className="text-accent-text min-h-11 rounded-lg px-3 text-sm font-semibold"
          aria-label={`Editează seria ${set.set_number}`}
        >
          Editează
        </button>
        <button
          type="button"
          onClick={async () => {
            await deleteSet(set.id);
            onChange();
          }}
          className="text-danger min-h-11 rounded-lg px-3 text-sm font-semibold"
          aria-label={`Șterge seria ${set.set_number}`}
        >
          Șterge
        </button>
      </span>
    </li>
  );
}

function ExerciseCard({
  workoutId,
  item,
  onChange,
}: {
  workoutId: number;
  item: WorkoutExercise;
  onChange: () => void;
}) {
  const { planned, sets, last_sets: last } = item;
  const measure = measureOf(planned.exercise);
  const lastSet = sets.at(-1);
  const defaultWeight =
    lastSet?.weight_kg ??
    item.suggestion.weight_kg ??
    last.at(-1)?.weight_kg ??
    (measure.bodyweight ? "0" : "");
  const defaultReps = String(lastSet?.reps ?? planned.reps_min);
  const done = sets.length >= planned.sets;

  return (
    <Card className="flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <h2 className="text-lg font-extrabold">{planned.exercise.name}</h2>
        <span
          className={`shrink-0 rounded-full px-3 py-1 text-xs font-bold ${done ? "bg-accent text-accent-fg" : "bg-surface-2 text-muted"}`}
        >
          {sets.length}/{planned.sets} serii
        </span>
      </div>
      <p className="text-muted text-sm">
        {planned.sets} × {repRange(planned.reps_min, planned.reps_max)}{" "}
        {measure.timed ? "secunde" : "repetări"} · pauză {planned.rest_seconds} s
      </p>
      {last.length > 0 && (
        <p className="text-muted text-sm">
          Data trecută: {last.map((s) => setText(s.weight_kg, s.reps, measure)).join(", ")}
        </p>
      )}
      <p className="border-border rounded-xl border p-3 text-sm">{suggestionText(item)}</p>
      {sets.length > 0 && (
        <ol className="flex flex-col gap-2">
          {sets.map((s) => (
            <SetRow key={s.id} set={s} measure={measure} onChange={onChange} />
          ))}
        </ol>
      )}
      <SetForm
        key={sets.length}
        measure={measure}
        initialWeight={defaultWeight}
        initialReps={defaultReps}
        submitLabel="+ Serie"
        onSubmit={async (weight, reps) => {
          await addSet(workoutId, planned.exercise.id, weight, reps);
          onChange();
        }}
      />
    </Card>
  );
}

export function WorkoutLogger() {
  const router = useRouter();
  const id = Number(useSearchParams().get("id"));
  const { data, error, reload } = useApi<Workout>(Number.isInteger(id) && id > 0 ? `/workouts/${id}` : null);
  const [finishing, setFinishing] = useState(false);

  if (error) return <ErrorState error={error} onRetry={reload} />;
  if (!data) return <Loading />;

  async function finish() {
    setFinishing(true);
    try {
      await finishWorkout(data!.id);
      router.push("/antrenament/istoric");
    } finally {
      setFinishing(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-3xl font-black uppercase">
          <span className="text-accent-text">Ziua {data.day.position}</span> · {data.day.name}
        </h1>
        <p className="text-muted text-sm">
          Început {formatDateTime(data.started_at)}
          {data.finished_at && ` · terminat ${formatDateTime(data.finished_at)}`}
        </p>
      </div>
      {data.exercises.map((item) => (
        <ExerciseCard key={item.planned.id} workoutId={data.id} item={item} onChange={reload} />
      ))}
      {!data.finished_at && (
        <Button loading={finishing} onClick={finish}>
          Termină antrenamentul
        </Button>
      )}
    </div>
  );
}
