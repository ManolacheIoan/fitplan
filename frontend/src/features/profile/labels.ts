import type { ActivityLevel, Experience, Goal, Program, Sex } from "./api";

export const SEX_LABELS: Record<Sex, string> = { male: "Masculin", female: "Feminin" };

export const ACTIVITY_LABELS: Record<ActivityLevel, string> = {
  sedentary: "Sedentar (birou, fără sport)",
  light: "Ușor activ (sport 1–3 zile/săpt.)",
  moderate: "Moderat activ (sport 3–5 zile/săpt.)",
  active: "Foarte activ (sport 6–7 zile/săpt.)",
  very_active: "Extrem de activ (muncă fizică + sport)",
};

export const GOAL_LABELS: Record<Goal, string> = {
  lose: "Slăbire",
  maintain: "Menținere",
  gain: "Masă musculară",
};

export const EXPERIENCE_LABELS: Record<Experience, string> = {
  beginner: "Începător",
  intermediate: "Intermediar",
  advanced: "Avansat",
};

export const options = <K extends string>(labels: Record<K, string>) =>
  (Object.entries(labels) as [K, string][]).map(([value, label]) => ({ value, label }));

/** Programs and the training days each supports (must match backend plans/constants.py). */
export const PROGRAMS: { value: Program; label: string; description: string; days: number[] }[] = [
  { value: "auto", label: "Automat", description: "Recomandat pentru zilele alese", days: [2, 3, 4, 5, 6] },
  { value: "full_body", label: "Full Body", description: "Tot corpul în fiecare zi", days: [2, 3] },
  {
    value: "upper_lower",
    label: "Upper / Lower",
    description: "Partea superioară / inferioară",
    days: [2, 4],
  },
  {
    value: "push_pull_legs",
    label: "Push / Pull / Legs",
    description: "Împingere, tracțiune, picioare",
    days: [3, 5, 6],
  },
  { value: "bro_split", label: "Bro Split", description: "O grupă musculară pe zi", days: [5] },
];
