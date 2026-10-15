import type { ReactNode } from "react";
import { errorMessage } from "@/lib/errors";
import { Button } from "./Button";

export function Loading({ label = "Se încarcă…" }: { label?: string }) {
  return (
    <div role="status" className="flex flex-col gap-3 py-6" aria-label={label}>
      <div className="bg-surface-2 h-24 animate-pulse rounded-2xl" />
      <div className="bg-surface-2 h-24 animate-pulse rounded-2xl" />
      <span className="sr-only">{label}</span>
    </div>
  );
}

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="border-border rounded-2xl border border-dashed p-6 text-center">
      <p className="font-bold">{title}</p>
      {children && <div className="text-muted mt-2 text-sm">{children}</div>}
    </div>
  );
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  return (
    <div role="alert" className="border-danger/50 rounded-2xl border p-5">
      <p className="text-danger font-semibold">{errorMessage(error)}</p>
      {onRetry && (
        <Button variant="secondary" className="mt-3" onClick={onRetry}>
          Reîncearcă
        </Button>
      )}
    </div>
  );
}
