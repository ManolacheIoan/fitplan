"use client";

import Link from "next/link";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { EmptyState, ErrorState, Loading } from "@/components/ui/States";
import type { Page } from "@/features/plans/api";
import { formatDateTime, nf1 } from "@/lib/dates";
import { useApi } from "@/lib/use-api";
import type { WorkoutSummary } from "./api";

const PAGE_SIZE = 15;

function HistoryPage({ offset, onMore }: { offset: number; onMore: (next: number) => void }) {
  const { data, error, reload } = useApi<Page<WorkoutSummary>>(
    `/workouts?limit=${PAGE_SIZE}&offset=${offset}`,
  );
  if (error) return <ErrorState error={error} onRetry={reload} />;
  if (!data) return <Loading />;
  if (offset === 0 && data.items.length === 0)
    return (
      <EmptyState title="Niciun antrenament încă.">Începe primul antrenament din pagina Azi.</EmptyState>
    );
  return (
    <>
      {data.items.map((w) => (
        <li key={w.id}>
          <Link
            href={`/antrenament?id=${w.id}`}
            className="border-border bg-surface flex min-h-14 items-center justify-between gap-3 rounded-2xl border p-4"
          >
            <span>
              <span className="block font-bold">{w.day_name}</span>
              <span className="text-muted text-sm">
                {formatDateTime(w.started_at)} · {w.sets_count} serii · {nf1.format(Number(w.volume_kg))} kg
                volum
              </span>
            </span>
            {!w.finished_at && (
              <span className="bg-accent text-accent-fg rounded-full px-3 py-1 text-xs font-bold">
                În curs
              </span>
            )}
          </Link>
        </li>
      ))}
      {data.next_offset !== null && (
        <li>
          <Button variant="secondary" className="w-full" onClick={() => onMore(data.next_offset!)}>
            Încarcă mai multe
          </Button>
        </li>
      )}
    </>
  );
}

export function WorkoutHistory() {
  const [offsets, setOffsets] = useState([0]);
  return (
    <ul className="flex flex-col gap-3">
      {offsets.map((offset) => (
        <HistoryPage
          key={offset}
          offset={offset}
          onMore={(next) => setOffsets((list) => (list.includes(next) ? list : [...list, next]))}
        />
      ))}
    </ul>
  );
}
