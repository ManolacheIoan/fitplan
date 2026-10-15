"use client";

import { Card } from "@/components/ui/Card";
import { EmptyState, ErrorState, Loading } from "@/components/ui/States";
import { nf1 } from "@/lib/dates";
import { useApi } from "@/lib/use-api";
import type { PersonalRecord } from "./api";

const shortDate = (iso: string) =>
  new Date(iso).toLocaleDateString("ro-RO", { day: "numeric", month: "short", year: "numeric" });

/** Heaviest weight lifted per exercise. */
export function Records() {
  const { data, error, reload } = useApi<PersonalRecord[]>("/progress/records");
  return (
    <Card>
      <h2 className="mb-1 text-lg font-extrabold">Recorduri personale</h2>
      <p className="text-muted mb-3 text-sm">Cea mai mare greutate ridicată la fiecare exercițiu.</p>
      {error ? (
        <ErrorState error={error} onRetry={reload} />
      ) : !data ? (
        <Loading />
      ) : data.length === 0 ? (
        <EmptyState title="Niciun record încă.">Apar după primele serii cu greutate.</EmptyState>
      ) : (
        <ul className="flex flex-col gap-2">
          {data.map((r) => (
            <li
              key={r.exercise_id}
              className="bg-surface-2 flex items-center justify-between gap-3 rounded-xl p-3"
            >
              <span>
                <span className="block font-bold">{r.exercise_name}</span>
                <span className="text-muted text-xs">{shortDate(r.achieved_on)}</span>
              </span>
              <span className="text-accent-text shrink-0 text-lg font-black">
                {nf1.format(Number(r.weight_kg))} kg
                <span className="text-muted ml-1 text-sm font-bold">× {r.reps}</span>
              </span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
