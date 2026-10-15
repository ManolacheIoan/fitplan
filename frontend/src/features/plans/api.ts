import type { Experience, Goal } from "@/features/profile/api";

export type Exercise = {
  id: number;
  slug: string;
  name: string;
  description: string;
  pattern: string;
  primary_muscle: string;
  secondary_muscles: string[];
  equipment: string;
  difficulty: Experience;
  is_compound: boolean;
};

export type PlanExercise = {
  id: number;
  position: number;
  sets: number;
  reps_min: number;
  reps_max: number;
  rest_seconds: number;
  exercise: Exercise;
};

export type PlanDay = { id: number; position: number; name: string; exercises: PlanExercise[] };

export type PlanSummary = {
  id: number;
  template: "full_body" | "upper_lower" | "push_pull_legs";
  days_per_week: number;
  goal: Goal;
  experience: Experience;
  is_active: boolean;
  created_at: string;
};

export type Plan = PlanSummary & { days: PlanDay[] };

export type Page<T> = { items: T[]; next_offset: number | null };
