"use client";

import { useRef, useState, type FormEvent } from "react";
import { Button } from "@/components/ui/Button";
import { ChoiceGroup, TextField } from "@/components/ui/Field";
import { errorMessage } from "@/lib/errors";
import { nf1 } from "@/lib/dates";
import { useApi } from "@/lib/use-api";
import { addMeal, createFood, searchExternalFoods, searchFoods, type Food, type RecentFood } from "./api";
import { Attribution } from "./Attribution";
import { MEAL_TYPES, mealTypeForNow, type MealType } from "./meals";

const SEARCH_DELAY_MS = 300;

function ManualFoodForm({
  initialName,
  onCreated,
}: {
  initialName: string;
  onCreated: (food: Food) => void;
}) {
  const [error, setError] = useState<string>();
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const num = (key: string) => Number(form.get(key));
    setPending(true);
    setError(undefined);
    try {
      onCreated(
        await createFood({
          name: String(form.get("name")),
          kcal_100g: num("kcal"),
          protein_100g: num("protein"),
          carbs_100g: num("carbs"),
          fat_100g: num("fat"),
        }),
      );
    } catch (err) {
      setError(errorMessage(err));
      setPending(false);
    }
  }

  const numberProps = { type: "number", inputMode: "decimal" as const, min: 0, step: 0.1, required: true };
  return (
    <form onSubmit={onSubmit} className="border-border flex flex-col gap-3 rounded-xl border p-4">
      <p className="font-bold">Aliment nou (valori la 100 g)</p>
      <TextField
        label="Denumire"
        name="name"
        required
        minLength={2}
        maxLength={120}
        defaultValue={initialName}
      />
      <div className="grid grid-cols-2 gap-3">
        <TextField label="Calorii (kcal)" name="kcal" max={900} {...numberProps} />
        <TextField label="Proteine (g)" name="protein" max={100} {...numberProps} />
        <TextField label="Carbohidrați (g)" name="carbs" max={100} {...numberProps} />
        <TextField label="Grăsimi (g)" name="fat" max={100} {...numberProps} />
      </div>
      <p className="text-muted text-xs">Alimentele adăugate manual sunt vizibile doar pentru tine.</p>
      {error && (
        <p role="alert" className="text-danger text-sm font-semibold">
          {error}
        </p>
      )}
      <Button type="submit" variant="secondary" loading={pending}>
        Salvează alimentul
      </Button>
    </form>
  );
}

function AddPortion({
  food,
  date,
  initialGrams = "100",
  onAdded,
}: {
  food: Food;
  date: string;
  initialGrams?: string;
  onAdded: () => void;
}) {
  const [error, setError] = useState<string>();
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setPending(true);
    try {
      await addMeal(food.id, date, Number(form.get("grams")), form.get("meal_type") as MealType);
      onAdded();
    } catch (err) {
      setError(errorMessage(err));
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="border-accent flex flex-col gap-2 rounded-xl border p-3">
      <p className="font-bold">{food.name}</p>
      <Attribution text={food.attribution} />
      <p className="text-muted text-sm">
        La 100 g: {nf1.format(Number(food.kcal_100g))} kcal · P {food.protein_100g} g · C {food.carbs_100g} g
        · G {food.fat_100g} g
      </p>
      <ChoiceGroup
        legend="Masa"
        name="meal_type"
        options={MEAL_TYPES}
        defaultValue={mealTypeForNow()}
        columns={2}
      />
      <div className="grid grid-cols-[1fr_auto] items-end gap-2">
        <TextField
          label="Cantitate (g)"
          name="grams"
          type="number"
          inputMode="decimal"
          min={1}
          max={5000}
          step={1}
          required
          defaultValue={initialGrams}
        />
        <Button type="submit" loading={pending}>
          Adaugă
        </Button>
      </div>
      {error && (
        <p role="alert" className="text-danger text-sm font-semibold">
          {error}
        </p>
      )}
    </form>
  );
}

function FoodResults({
  foods,
  label,
  onPick,
}: {
  foods: Food[];
  label: string;
  onPick: (food: Food) => void;
}) {
  return (
    <ul className="flex flex-col gap-2" aria-label={label}>
      {foods.map((food) => (
        <li key={food.id}>
          <button
            type="button"
            onClick={() => onPick(food)}
            className="bg-surface-2 flex min-h-12 w-full items-center justify-between gap-2 rounded-xl px-3 py-2 text-left"
          >
            <span className="font-semibold">
              {food.name}
              {food.is_own && <span className="text-muted ml-2 text-xs">(al tău)</span>}
            </span>
            <span className="text-muted shrink-0 text-sm">
              {nf1.format(Number(food.kcal_100g))} kcal/100 g
            </span>
          </button>
        </li>
      ))}
      {foods.length === 0 && <li className="text-muted text-sm">Niciun rezultat.</li>}
    </ul>
  );
}

/** Explicit (not as-you-type) search in Open Food Facts, which limits request rates. */
function ExternalSearch({ query, onPick }: { query: string; onPick: (food: Food) => void }) {
  const [foods, setFoods] = useState<Food[] | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string>();

  async function run() {
    setPending(true);
    setError(undefined);
    try {
      setFoods(await searchExternalFoods(query));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setPending(false);
    }
  }

  if (foods) {
    return (
      <div className="flex flex-col gap-2">
        <p className="text-sm font-semibold">Rezultate Open Food Facts</p>
        <FoodResults foods={foods} label="Rezultate Open Food Facts" onPick={onPick} />
        <p className="text-muted text-xs">
          Date de la{" "}
          <a href="https://world.openfoodfacts.org" target="_blank" rel="noreferrer" className="underline">
            Open Food Facts
          </a>{" "}
          (licență ODbL), introduse de voluntari: verifică valorile pe etichetă.
        </p>
      </div>
    );
  }
  return (
    <div className="flex flex-col gap-2">
      <Button variant="secondary" loading={pending} onClick={run}>
        Caută „{query}” în Open Food Facts
      </Button>
      {error && (
        <p role="alert" className="text-danger text-sm font-semibold">
          {error}
        </p>
      )}
    </div>
  );
}

export function FoodPicker({ date, onAdded }: { date: string; onAdded: () => void }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Food[] | null>(null);
  const [searchError, setSearchError] = useState<string>();
  const [selected, setSelected] = useState<{ food: Food; grams?: string } | null>(null);
  const recent = useApi<RecentFood[]>("/meals/recent");
  const [manual, setManual] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);

  function onQueryChange(value: string) {
    setQuery(value);
    setSelected(null);
    clearTimeout(timer.current);
    if (value.trim().length < 2) {
      setResults(null);
      return;
    }
    timer.current = setTimeout(() => {
      searchFoods(value.trim())
        .then((found) => {
          setResults(found);
          setSearchError(undefined);
        })
        .catch((err: unknown) => setSearchError(errorMessage(err)));
    }, SEARCH_DELAY_MS);
  }

  function reset() {
    setQuery("");
    setResults(null);
    setSelected(null);
    setManual(false);
    recent.reload();
    onAdded();
  }

  return (
    <div className="flex flex-col gap-3">
      <TextField
        label="Caută aliment"
        type="search"
        value={query}
        onChange={(e) => onQueryChange(e.target.value)}
        placeholder="ex. ovăz, banană"
        autoComplete="off"
      />
      {searchError && <p className="text-danger text-sm">{searchError}</p>}
      {!selected && !query && !manual && recent.data && recent.data.length > 0 && (
        <div>
          <p className="text-muted mb-2 text-sm font-semibold">Recente</p>
          <ul className="flex flex-wrap gap-2" aria-label="Alimente recente">
            {recent.data.map(({ food, grams }) => (
              <li key={food.id}>
                <button
                  type="button"
                  onClick={() => setSelected({ food, grams })}
                  className="border-border bg-surface-2 hover:border-accent min-h-11 rounded-full border px-4 text-sm font-semibold transition active:scale-[0.97]"
                >
                  {food.name} · {nf1.format(Number(grams))} g
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
      {selected ? (
        <AddPortion food={selected.food} initialGrams={selected.grams} date={date} onAdded={reset} />
      ) : (
        results && (
          <>
            <FoodResults foods={results} label="Rezultate căutare" onPick={(food) => setSelected({ food })} />
            {query.trim().length >= 3 && (
              <ExternalSearch
                key={query.trim()}
                query={query.trim()}
                onPick={(food) => setSelected({ food })}
              />
            )}
          </>
        )
      )}
      {!selected &&
        (manual ? (
          <ManualFoodForm
            initialName={query}
            onCreated={(food) => {
              setManual(false);
              setSelected({ food });
            }}
          />
        ) : (
          <Button variant="ghost" onClick={() => setManual(true)}>
            Nu găsești alimentul? Adaugă-l manual
          </Button>
        ))}
    </div>
  );
}
