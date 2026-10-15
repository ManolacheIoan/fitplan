import { Card } from "@/components/ui/Card";
import type { Plan, PlanExercise } from "./api";
import { EQUIPMENT_LABELS, MUSCLE_LABELS, TEMPLATE_LABELS, dateRo, reps } from "./labels";

export function ExerciseRow({ item }: { item: PlanExercise }) {
  const { exercise } = item;
  return (
    <details className="group bg-surface-2 rounded-xl p-3">
      <summary className="flex min-h-10 cursor-pointer list-none items-center justify-between gap-3">
        <span className="font-bold">{exercise.name}</span>
        <span className="text-accent-text shrink-0 text-sm font-extrabold">
          {item.sets} × {reps(item.reps_min, item.reps_max)}
        </span>
      </summary>
      <div className="text-muted mt-2 flex flex-col gap-2 text-sm">
        <p>{exercise.description}</p>
        <p>
          Pauză {item.rest_seconds} s · {MUSCLE_LABELS[exercise.primary_muscle]} ·{" "}
          {EQUIPMENT_LABELS[exercise.equipment]}
        </p>
      </div>
    </details>
  );
}

export function PlanView({ plan }: { plan: Plan }) {
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
                <ExerciseRow item={item} />
              </li>
            ))}
          </ol>
        </Card>
      ))}
    </div>
  );
}
