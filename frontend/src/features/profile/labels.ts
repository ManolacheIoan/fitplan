import type { ActivityLevel, Experience, Goal, Sex } from "./api";

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
