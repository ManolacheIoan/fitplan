"use client";

import { useState } from "react";
import { Card } from "@/components/ui/Card";
import { EmptyState, ErrorState, Loading } from "@/components/ui/States";
import { formatDay, nf1, todayLocal } from "@/lib/dates";
import { useApi } from "@/lib/use-api";
import { deleteMeal, updateMeal, type DayMeals, type Meal } from "./api";
import { FoodPicker } from "./FoodPicker";

function shiftDay(isoDate: string, days: number): string {
  const d = new Date(`${isoDate}T12:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

function Progress({
  label,
  value,
  target,
  unit,
}: {
  label: string;
  value: number;
  target?: number;
  unit: string;
}) {
  const pct = target ? Math.min(100, (value / target) * 100) : 0;
  return (
    <div>
      <div className="flex justify-between text-sm">
        <span className="font-semibold">{label}</span>
        <span className="text-muted">
          {nf1.format(value)}
          {target ? ` / ~${target}` : ""} {unit}
        </span>
      </div>
      {target !== undefined && (
        <div
          className="bg-surface-2 mt-1 h-3 overflow-hidden rounded-full"
          role="progressbar"
          aria-label={label}
          aria-valuemin={0}
          aria-valuemax={target}
          aria-valuenow={Math.round(value)}
        >
          <div className="bg-accent h-full rounded-full transition-[width]" style={{ width: `${pct}%` }} />
        </div>
      )}
    </div>
  );
}

function MealRow({ meal, onChange }: { meal: Meal; onChange: () => void }) {
  const [editing, setEditing] = useState(false);
  return (
    <li className="bg-surface-2 flex flex-col gap-2 rounded-xl p-3">
      <div className="flex items-center justify-between gap-2">
        <span>
          <span className="block font-semibold">{meal.food.name}</span>
          <span className="text-muted text-sm">
            {nf1.format(Number(meal.grams))} g · {nf1.format(Number(meal.kcal))} kcal
          </span>
        </span>
        <span className="flex shrink-0 gap-1">
          <button
            type="button"
            className="text-accent-text min-h-11 px-2 text-sm font-semibold"
            onClick={() => setEditing((v) => !v)}
          >
            Editează
          </button>
          <button
            type="button"
            className="text-danger min-h-11 px-2 text-sm font-semibold"
            onClick={async () => {
              await deleteMeal(meal.id);
              onChange();
            }}
          >
            Șterge
          </button>
        </span>
      </div>
      {editing && (
        <form
          className="flex gap-2"
          onSubmit={async (e) => {
            e.preventDefault();
            await updateMeal(meal.id, Number(new FormData(e.currentTarget).get("grams")));
            setEditing(false);
            onChange();
          }}
        >
          <label className="sr-only" htmlFor={`grams-${meal.id}`}>
            Cantitate (g)
          </label>
          <input
            id={`grams-${meal.id}`}
            name="grams"
            type="number"
            inputMode="decimal"
            min={1}
            max={5000}
            required
            defaultValue={meal.grams}
            className="border-border bg-surface min-h-12 flex-1 rounded-xl border px-3"
          />
          <button type="submit" className="bg-accent text-accent-fg min-h-12 rounded-xl px-4 font-bold">
            Salvează
          </button>
        </form>
      )}
    </li>
  );
}

export function FoodLog() {
  const [date, setDate] = useState(todayLocal);
  const { data, error, reload } = useApi<DayMeals>(`/meals?date=${date}`);
  const isToday = date === todayLocal();

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between gap-2">
        <button
          type="button"
          onClick={() => setDate((d) => shiftDay(d, -1))}
          className="border-border min-h-12 min-w-12 rounded-xl border font-bold"
          aria-label="Ziua anterioară"
        >
          ‹
        </button>
        <p className="text-center font-bold capitalize">{isToday ? "Azi" : formatDay(date)}</p>
        <button
          type="button"
          onClick={() => setDate((d) => shiftDay(d, 1))}
          disabled={isToday}
          className="border-border min-h-12 min-w-12 rounded-xl border font-bold disabled:opacity-40"
          aria-label="Ziua următoare"
        >
          ›
        </button>
      </div>

      {error ? (
        <ErrorState error={error} onRetry={reload} />
      ) : !data || data.date !== date ? (
        <Loading />
      ) : (
        <>
          <Card className="flex flex-col gap-3">
            <div className="flex items-baseline justify-between">
              <h2 className="text-lg font-extrabold">Total zi</h2>
              {data.targets && <span className="text-muted text-xs font-bold">Ținte aproximative</span>}
            </div>
            <Progress
              label="Calorii"
              value={Number(data.totals.kcal)}
              target={data.targets?.kcal}
              unit="kcal"
            />
            <Progress
              label="Proteine"
              value={Number(data.totals.protein_g)}
              target={data.targets?.protein_g}
              unit="g"
            />
            <Progress
              label="Carbohidrați"
              value={Number(data.totals.carbs_g)}
              target={data.targets?.carbs_g}
              unit="g"
            />
            <Progress
              label="Grăsimi"
              value={Number(data.totals.fat_g)}
              target={data.targets?.fat_g}
              unit="g"
            />
          </Card>
          <Card className="flex flex-col gap-3">
            <h2 className="text-lg font-extrabold">Mese</h2>
            {data.entries.length === 0 ? (
              <EmptyState title="Nimic înregistrat în această zi." />
            ) : (
              <ul className="flex flex-col gap-2">
                {data.entries.map((meal) => (
                  <MealRow key={meal.id} meal={meal} onChange={reload} />
                ))}
              </ul>
            )}
          </Card>
          <Card>
            <h2 className="mb-3 text-lg font-extrabold">Adaugă</h2>
            <FoodPicker date={date} onAdded={reload} />
          </Card>
        </>
      )}
    </div>
  );
}
