export type MealType = "breakfast" | "lunch" | "dinner" | "snack";

/** Display order and Romanian labels. */
export const MEAL_TYPES: { value: MealType; label: string }[] = [
  { value: "breakfast", label: "Mic dejun" },
  { value: "lunch", label: "Prânz" },
  { value: "dinner", label: "Cină" },
  { value: "snack", label: "Gustare" },
];

/** Category suggested from the local time of day (the user can change it). */
export function mealTypeForNow(now = new Date()): MealType {
  const hour = now.getHours();
  if (hour < 11) return "breakfast";
  if (hour < 15) return "lunch";
  if (hour >= 18 && hour < 22) return "dinner";
  return "snack";
}
