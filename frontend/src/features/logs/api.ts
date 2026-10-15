import { api, json } from "@/lib/api";
import type { Targets } from "@/features/nutrition/api";
import type { PlanDay, PlanExercise } from "@/features/plans/api";

export type SetLog = { id: number; exercise_id: number; set_number: number; weight_kg: string; reps: number };

export type Suggestion = {
  kind: "first_time" | "add_weight" | "add_reps" | "max_reached";
  weight_kg: string | null;
};

export type WorkoutExercise = {
  planned: PlanExercise;
  /** Replaced for this workout only; the plan is unchanged. */
  swapped_today: boolean;
  sets: SetLog[];
  last_sets: { weight_kg: string; reps: number }[];
  suggestion: Suggestion;
};

export type Workout = {
  id: number;
  day: { id: number; position: number; name: string };
  started_at: string;
  finished_at: string | null;
  exercises: WorkoutExercise[];
};

export type WorkoutSummary = {
  id: number;
  day_name: string;
  started_at: string;
  finished_at: string | null;
  sets_count: number;
  volume_kg: string;
};

export type Today = { open_session_id: number | null; next_day: PlanDay };

export type Food = {
  id: number;
  name: string;
  kcal_100g: string;
  protein_100g: string;
  carbs_100g: string;
  fat_100g: string;
  source: "seed" | "manual" | "external";
  is_own: boolean;
};

export type FoodInput = {
  name: string;
  kcal_100g: number;
  protein_100g: number;
  carbs_100g: number;
  fat_100g: number;
};

type Macros = { kcal: string; protein_g: string; carbs_g: string; fat_g: string };
export type Meal = Macros & { id: number; food: Food; eaten_on: string; grams: string };
export type DayMeals = { date: string; entries: Meal[]; totals: Macros; targets: Targets | null };

export const startWorkout = (plan_day_id: number) =>
  api<Workout>("/workouts", { method: "POST", ...json({ plan_day_id }) });
export const swapToday = (workoutId: number, plan_exercise_id: number, exercise_id: number) =>
  api<Workout>(`/workouts/${workoutId}/swaps`, {
    method: "POST",
    ...json({ plan_exercise_id, exercise_id }),
  });
export const finishWorkout = (id: number) => api<void>(`/workouts/${id}/finish`, { method: "POST" });
export const addSet = (workoutId: number, exercise_id: number, weight_kg: number, reps: number) =>
  api<SetLog & { is_record: boolean }>(`/workouts/${workoutId}/sets`, {
    method: "POST",
    ...json({ exercise_id, weight_kg, reps }),
  });
export const updateSet = (id: number, weight_kg: number, reps: number) =>
  api<SetLog>(`/sets/${id}`, { method: "PATCH", ...json({ weight_kg, reps }) });
export const deleteSet = (id: number) => api<void>(`/sets/${id}`, { method: "DELETE" });

export const searchFoods = (q: string) => api<Food[]>(`/foods?q=${encodeURIComponent(q)}`);
export const createFood = (data: FoodInput) => api<Food>("/foods", { method: "POST", ...json(data) });
export const addMeal = (food_id: number, eaten_on: string, grams: number) =>
  api<Meal>("/meals", { method: "POST", ...json({ food_id, eaten_on, grams }) });
export const updateMeal = (id: number, grams: number) =>
  api<Meal>(`/meals/${id}`, { method: "PATCH", ...json({ grams }) });
export const deleteMeal = (id: number) => api<void>(`/meals/${id}`, { method: "DELETE" });
