"use client";

import { useEffect, useState } from "react";
import { onWakingChange } from "@/lib/api";

/** Shown while a sleeping free-tier backend is starting up. */
export function WakeBanner() {
  const [waking, setWaking] = useState(false);
  useEffect(() => onWakingChange(setWaking), []);
  if (!waking) return null;
  return (
    <div
      role="status"
      className="bg-surface-2 fixed inset-x-0 top-0 z-50 px-4 py-3 text-center text-sm shadow-lg"
    >
      <span
        className="bg-accent mr-2 inline-block size-3 animate-pulse rounded-full align-middle"
        aria-hidden
      />
      Serverul pornește (poate dura până la un minut)…
    </div>
  );
}
