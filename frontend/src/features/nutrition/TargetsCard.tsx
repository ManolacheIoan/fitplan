"use client";

import { FlameIcon } from "@/components/Icons";
import { Card } from "@/components/ui/Card";
import { Ring } from "@/components/ui/Ring";
import { ErrorState, Loading } from "@/components/ui/States";
import { errorMessage } from "@/lib/errors";
import { ApiError } from "@/lib/api";
import { todayLocal } from "@/lib/dates";
import { useApi } from "@/lib/use-api";
import type { DayMeals } from "@/features/logs/api";
import type { TargetsResponse } from "./api";

const nf = new Intl.NumberFormat("ro-RO", { maximumFractionDigits: 2 });

export function TargetsCard() {
  const { data, error, loading, reload } = useApi<TargetsResponse>("/nutrition/targets");
  const today = useApi<DayMeals>(`/meals?date=${todayLocal()}`);
  if (loading && !data) return <Loading />;
  if (error) return <ErrorState error={error} onRetry={reload} />;
  if (!data) return null;

  if (data.status === "blocked") {
    return (
      <Card>
        <h2 className="mb-2 text-lg font-extrabold">Ținte nutriționale</h2>
        <p className="text-muted">{errorMessage(new ApiError(422, data.reason))}</p>
      </Card>
    );
  }

  const t = data.targets;
  const eaten = Number(today.data?.totals.kcal ?? 0);
  const weekly = Number(t.weekly_change_kg);
  return (
    <Card>
      <div className="flex items-baseline justify-between gap-2">
        <h2 className="text-lg font-extrabold">Ținte zilnice</h2>
        <span className="bg-surface-2 text-muted rounded-full px-3 py-1 text-xs font-bold">
          Estimare aproximativă
        </span>
      </div>
      <div className="mt-4 flex items-center gap-5">
        <Ring value={eaten / t.kcal}>
          <span className="text-2xl leading-none font-black">{Math.round(eaten)}</span>
          <span className="text-muted text-xs font-semibold">din ~{t.kcal} kcal</span>
        </Ring>
        <div className="flex flex-col gap-1">
          <p className="text-muted flex items-center gap-1 text-sm font-semibold">
            <FlameIcon width={16} height={16} className="text-accent-text" /> Ținta zilei
          </p>
          <p className="text-accent-text text-4xl font-black">
            ~{t.kcal}
            <span className="text-muted ml-1 text-base font-bold">kcal</span>
          </p>
          <p className="text-muted text-sm">
            {eaten > t.kcal ? "Ai depășit ținta de azi." : `Mai ai ~${Math.round(t.kcal - eaten)} kcal azi.`}
          </p>
        </div>
      </div>
      <dl className="mt-4 grid grid-cols-3 gap-2 text-center">
        {[
          ["Proteine", t.protein_g],
          ["Grăsimi", t.fat_g],
          ["Carbohidrați", t.carbs_g],
        ].map(([label, grams]) => (
          <div key={label} className="bg-surface-2 rounded-xl p-3">
            <dt className="text-muted text-xs">{label}</dt>
            <dd className="text-xl font-extrabold">~{grams} g</dd>
          </div>
        ))}
      </dl>
      <p className="text-muted mt-4 text-sm">
        Calculat cu formula Mifflin-St Jeor pentru {t.based_on_weight_kg} kg. Necesar estimat de menținere: ~
        {t.tdee_kcal} kcal.
        {weekly !== 0 &&
          ` Ritm estimat: ${weekly > 0 ? "+" : "−"}${nf.format(Math.abs(weekly))} kg/săptămână (aprox.).`}
      </p>
      {t.floor_applied && (
        <p className="text-warning mt-2 text-sm">
          Ținta a fost ridicată la pragul minim de calorii folosit de aplicație.
        </p>
      )}
    </Card>
  );
}
