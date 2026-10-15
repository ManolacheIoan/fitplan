import { api, json } from "@/lib/api";

export type WeightEntry = { id: number; logged_on: string; weight_kg: string };
export type WeightProgress = { entries: WeightEntry[]; weekly: { week_start: string; average_kg: string }[] };
export type VolumeProgress = { weekly: { week_start: string; volume_kg: string; sessions: number }[] };

export type PersonalRecord = {
  exercise_id: number;
  exercise_name: string;
  weight_kg: string;
  reps: number;
  achieved_on: string;
};

export const saveWeight = (logged_on: string, weight_kg: number) =>
  api<{ entry: WeightEntry; targets_updated: boolean }>("/weights", {
    method: "POST",
    ...json({ logged_on, weight_kg }),
  });

export const deleteWeight = (id: number) => api<void>(`/weights/${id}`, { method: "DELETE" });
