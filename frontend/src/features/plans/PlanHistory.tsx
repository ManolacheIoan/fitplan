"use client";

import Link from "next/link";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { EmptyState, ErrorState, Loading } from "@/components/ui/States";
import { useApi } from "@/lib/use-api";
import type { Page, PlanSummary } from "./api";
import { TEMPLATE_LABELS, dateRo } from "./labels";
import { GOAL_LABELS } from "@/features/profile/labels";

const PAGE_SIZE = 10;

function HistoryPage({ offset, onMore }: { offset: number; onMore: (next: number) => void }) {
  const { data, error, reload } = useApi<Page<PlanSummary>>(`/plans?limit=${PAGE_SIZE}&offset=${offset}`);
  if (error) return <ErrorState error={error} onRetry={reload} />;
  if (!data) return <Loading />;
  if (offset === 0 && data.items.length === 0) return <EmptyState title="Nu există planuri încă." />;
  return (
    <>
      {data.items.map((plan) => (
        <li key={plan.id}>
          <Link
            href={`/plan/detalii?id=${plan.id}`}
            className="border-border bg-surface flex min-h-14 items-center justify-between gap-3 rounded-2xl border p-4"
          >
            <span>
              <span className="block font-bold">{TEMPLATE_LABELS[plan.template]}</span>
              <span className="text-muted text-sm">
                {dateRo(plan.created_at)} · {plan.days_per_week} zile · {GOAL_LABELS[plan.goal]}
              </span>
            </span>
            {plan.is_active && (
              <span className="bg-accent text-accent-fg rounded-full px-3 py-1 text-xs font-bold">Activ</span>
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

export function PlanHistory() {
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
