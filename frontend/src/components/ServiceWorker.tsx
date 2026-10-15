"use client";

import { useEffect } from "react";

/** Registers /sw.js in production builds (installable PWA, offline app shell). */
export function ServiceWorker() {
  useEffect(() => {
    if (process.env.NODE_ENV === "production" && "serviceWorker" in navigator) {
      navigator.serviceWorker.register("/sw.js").catch(() => {
        // Not critical: the app works without it.
      });
    }
  }, []);
  return null;
}
