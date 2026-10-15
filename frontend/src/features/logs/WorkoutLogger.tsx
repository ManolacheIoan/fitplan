"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ErrorState, Loading } from "@/components/ui/States";
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

function suggestionText({ suggestion, planned }: WorkoutExercise): string {
  const kg = suggestion.weight_kg ? nf1.format(Number(suggestion.weight_kg)) : "";
  switch (suggestion.kind) {
    case "first_time":
      return `Prima dată: alege o greutate cu care poți face ${planned.reps_max} repetări cu tehnică bună.`;
    case "add_weight":
      return `Data trecută ai atins ${planned.reps_max} repetări la toate seriile. Încearcă ${kg} kg.`;
    case "add_reps":
      return `Rămâi la ${kg} kg și încearcă o repetare în plus pe serie.`;
  }
}

const numberInput =
  "min-h-12 w-full rounded-xl border border-border bg-surface-2 px-3 text-center text-lg font-bold text-fg";

/** Weight + reps inputs, used both for adding and editing a set. */
function SetForm({
  initialWeight,
  initialReps,
  submitLabel,
  onSubmit,
  onCancel,
}: {
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
      <div className="grid grid-cols-[1fr_1fr_auto] items-end gap-2">
        <label className="text-muted flex flex-col gap-1 text-xs font-semibold">
          Greutate (kg)
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
        <label className="text-muted flex flex-col gap-1 text-xs font-semibold">
          Repetări
          <input
            name="reps"
            type="number"
            inputMode="numeric"
            min={1}
            max={100}
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

function SetRow({ set, onChange }: { set: SetLog; onChange: () => void }) {
  const [editing, setEditing] = useState(false);
  if (editing) {
    return (
      <li>
        <SetForm
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
        Seria {set.set_number}: {nf1.format(Number(set.weight_kg))} kg × {set.reps}
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
  const lastSet = sets.at(-1);
  const defaultWeight = lastSet?.weight_kg ?? item.suggestion.weight_kg ?? last.at(-1)?.weight_kg ?? "";
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
        {planned.sets} × {repRange(planned.reps_min, planned.reps_max)} repetări · pauză{" "}
        {planned.rest_seconds} s
      </p>
      {last.length > 0 && (
        <p className="text-muted text-sm">
          Data trecută: {last.map((s) => `${nf1.format(Number(s.weight_kg))}×${s.reps}`).join(", ")}
        </p>
      )}
      <p className="border-border rounded-xl border p-3 text-sm">{suggestionText(item)}</p>
      {sets.length > 0 && (
        <ol className="flex flex-col gap-2">
          {sets.map((s) => (
            <SetRow key={s.id} set={s} onChange={onChange} />
          ))}
        </ol>
      )}
      <SetForm
        key={sets.length}
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
