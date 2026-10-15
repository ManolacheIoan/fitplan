"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { EmptyState, ErrorState, Loading } from "@/components/ui/States";
import { errorMessage } from "@/lib/errors";
import { useApi } from "@/lib/use-api";
import type { Exercise } from "./api";
import { EQUIPMENT_LABELS } from "./labels";

export type SwapChoice = { label: string; run: (exercise: Exercise) => Promise<void> };

/** Lists exercises that can replace a planned one; each choice is a button per exercise. */
export function SwapPanel({
  planExerciseId,
  choices,
  onClose,
}: {
  planExerciseId: number;
  choices: SwapChoice[];
  onClose: () => void;
}) {
  const { data, error, reload } = useApi<Exercise[]>(`/plans/exercises/${planExerciseId}/alternatives`);
  const [pending, setPending] = useState<string>();
  const [actionError, setActionError] = useState<string>();

  async function choose(choice: SwapChoice, exercise: Exercise) {
    setPending(`${choice.label}-${exercise.id}`);
    setActionError(undefined);
    try {
      await choice.run(exercise);
    } catch (err) {
      setActionError(errorMessage(err));
      setPending(undefined);
    }
  }

  return (
    <div className="animate-fade-up border-border flex flex-col gap-3 rounded-xl border p-3">
      <div className="flex items-center justify-between">
        <p className="text-sm font-bold">Înlocuiește cu</p>
        <button type="button" onClick={onClose} className="text-muted min-h-11 px-2 text-sm font-semibold">
          Închide
        </button>
      </div>
      {error ? (
        <ErrorState error={error} onRetry={reload} />
      ) : !data ? (
        <Loading />
      ) : data.length === 0 ? (
        <EmptyState title="Nu există alternative pentru nivelul tău." />
      ) : (
        <ul className="flex flex-col gap-2">
          {data.map((exercise) => (
            <li key={exercise.id} className="bg-surface-2 flex flex-col gap-2 rounded-xl p-3">
              <span>
                <span className="block font-bold">{exercise.name}</span>
                <span className="text-muted text-xs">{EQUIPMENT_LABELS[exercise.equipment]}</span>
              </span>
              <span className="flex gap-2">
                {choices.map((choice) => (
                  <Button
                    key={choice.label}
                    variant="secondary"
                    className="min-h-11 flex-1 px-3 text-sm"
                    loading={pending === `${choice.label}-${exercise.id}`}
                    disabled={pending !== undefined}
                    onClick={() => choose(choice, exercise)}
                  >
                    {choice.label}
                  </Button>
                ))}
              </span>
            </li>
          ))}
        </ul>
      )}
      {actionError && (
        <p role="alert" className="text-danger text-sm font-semibold">
          {actionError}
        </p>
      )}
    </div>
  );
}
