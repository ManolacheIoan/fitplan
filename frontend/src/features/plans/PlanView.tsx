"use client";

import { useState } from "react";
import { Card } from "@/components/ui/Card";
import { swapPermanently, type Plan, type PlanExercise } from "./api";
import { EQUIPMENT_LABELS, MUSCLE_LABELS, TEMPLATE_LABELS, dateRo, reps } from "./labels";
import { SwapPanel } from "./SwapPanel";

export function ExerciseRow({ item, onChanged }: { item: PlanExercise; onChanged?: () => void }) {
  const { exercise } = item;
  const [swapping, setSwapping] = useState(false);
  return (
    <details className="group bg-surface-2 rounded-xl p-3">
      <summary className="flex min-h-10 cursor-pointer list-none items-center justify-between gap-3">
        <span className="font-bold">{exercise.name}</span>
        <span className="text-accent-text shrink-0 text-sm font-extrabold">
          {item.sets} × {reps(item.reps_min, item.reps_max)}
          {exercise.unit === "seconds" && " s"}
        </span>
      </summary>
      <div className="text-muted mt-2 flex flex-col gap-2 text-sm">
        <p>{exercise.description}</p>
        <p>
          Pauză {item.rest_seconds} s · {MUSCLE_LABELS[exercise.primary_muscle]} ·{" "}
          {EQUIPMENT_LABELS[exercise.equipment]}
        </p>
        {onChanged &&
          (swapping ? (
            <SwapPanel
              planExerciseId={item.id}
              onClose={() => setSwapping(false)}
              choices={[
                {
                  label: "Înlocuiește în plan",
                  run: async (replacement) => {
                    await swapPermanently(item.id, replacement.id);
                    setSwapping(false);
                    onChanged();
                  },
                },
              ]}
            />
          ) : (
            <button
              type="button"
              onClick={() => setSwapping(true)}
              className="text-accent-text min-h-11 self-start font-semibold"
            >
              Înlocuiește exercițiul
            </button>
          ))}
      </div>
    </details>
  );
}

/** `onChanged` enables replacing exercises (only for the active plan). */
export function PlanView({ plan, onChanged }: { plan: Plan; onChanged?: () => void }) {
  return (
    <div className="flex flex-col gap-4">
      <p className="text-muted">
        {TEMPLATE_LABELS[plan.template]} · {plan.days_per_week} antrenamente pe săptămână · generat la{" "}
        {dateRo(plan.created_at)}. Parcurge zilele în ordine, apoi reia de la prima.
      </p>
      {plan.days.map((day) => (
        <Card key={day.id} className="animate-fade-up">
          <h2 className="mb-3 text-xl font-black uppercase">
            <span className="text-accent-text">Ziua {day.position}</span> · {day.name}
          </h2>
          <ol className="flex flex-col gap-2">
            {day.exercises.map((item) => (
              <li key={item.id}>
                <ExerciseRow item={item} onChanged={onChanged} />
              </li>
            ))}
          </ol>
        </Card>
      ))}
    </div>
  );
}
