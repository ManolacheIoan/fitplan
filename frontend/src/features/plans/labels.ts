import type { PlanSummary } from "./api";

export const TEMPLATE_LABELS: Record<PlanSummary["template"], string> = {
  full_body: "Full Body",
  upper_lower: "Upper / Lower",
  push_pull_legs: "Push / Pull / Legs",
  bro_split: "Bro Split",
};

export const MUSCLE_LABELS: Record<string, string> = {
  chest: "piept",
  back: "spate",
  shoulders: "umeri",
  biceps: "biceps",
  triceps: "triceps",
  quads: "cvadriceps",
  hamstrings: "femurali",
  glutes: "fesieri",
  calves: "gambe",
  core: "abdomen",
};

export const EQUIPMENT_LABELS: Record<string, string> = {
  barbell: "bară",
  dumbbell: "gantere",
  machine: "aparat",
  cable: "cablu",
  bodyweight: "greutatea corpului",
};

export const reps = (min: number, max: number) => (min === max ? `${min}` : `${min}–${max}`);

export const dateRo = (iso: string) =>
  new Date(iso).toLocaleDateString("ro-RO", { day: "numeric", month: "long", year: "numeric" });
