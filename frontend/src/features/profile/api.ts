import { api, json } from "@/lib/api";

export type Sex = "male" | "female";
export type ActivityLevel = "sedentary" | "light" | "moderate" | "active" | "very_active";
export type Goal = "lose" | "maintain" | "gain";
export type Experience = "beginner" | "intermediate" | "advanced";
export type ScreeningStatus = "passed" | "refer";

export type ProfileInput = {
  display_name: string;
  sex: Sex;
  birth_date: string;
  height_cm: number;
  weight_kg: number;
  activity_level: ActivityLevel;
  goal: Goal;
  training_days: number;
  experience: Experience;
  equipment: "gym";
};

export type Profile = ProfileInput & {
  age: number;
  screening_status: ScreeningStatus | null;
  screening_at: string | null;
};

export type ScreeningAnswers = {
  pregnant_or_breastfeeding?: boolean; // asked only for female sex
  diagnosed_medical_condition: boolean;
  eating_disorder_history: boolean;
  current_injury: boolean;
};

export const saveProfile = (data: ProfileInput) => api<Profile>("/profile", { method: "PUT", ...json(data) });

export const submitScreening = (answers: ScreeningAnswers) =>
  api<{ status: ScreeningStatus }>("/profile/screening", { method: "POST", ...json(answers) });
