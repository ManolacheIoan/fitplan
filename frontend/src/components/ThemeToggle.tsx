"use client";

import { useSyncExternalStore } from "react";

type Theme = "dark" | "light";

const listeners = new Set<() => void>();
const subscribe = (listener: () => void) => {
  listeners.add(listener);
  return () => listeners.delete(listener);
};
const getTheme = (): Theme => (document.documentElement.dataset.theme === "light" ? "light" : "dark");

function applyTheme(theme: Theme) {
  const root = document.documentElement;
  if (theme === "light") root.dataset.theme = "light";
  else delete root.dataset.theme;
  try {
    localStorage.setItem("theme", theme);
  } catch {
    // storage unavailable (private mode): the choice lasts for this page view only
  }
  listeners.forEach((listener) => listener());
}

export function ThemeToggle() {
  const theme = useSyncExternalStore(subscribe, getTheme, () => "dark" as Theme);
  return (
    <fieldset className="flex gap-2">
      <legend className="mb-2 text-sm font-semibold">Temă</legend>
      {(["dark", "light"] as const).map((value) => (
        <button
          key={value}
          type="button"
          aria-pressed={theme === value}
          onClick={() => applyTheme(value)}
          className="aria-pressed:border-accent aria-pressed:bg-accent aria-pressed:text-accent-fg border-border min-h-12 flex-1 rounded-xl border font-bold"
        >
          {value === "dark" ? "Întunecată" : "Luminoasă"}
        </button>
      ))}
    </fieldset>
  );
}
