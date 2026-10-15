export type Targets = {
  bmr_kcal: number;
  tdee_kcal: number;
  kcal: number;
  protein_g: number;
  fat_g: number;
  carbs_g: number;
  weekly_change_kg: string;
  floor_applied: boolean;
  based_on_weight_kg: string;
  computed_at: string;
};

export type TargetsResponse =
  { status: "ok"; targets: Targets; reason: null } | { status: "blocked"; reason: string; targets: null };
