"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/Button";
import { ChoiceGroup, SelectField, TextField } from "@/components/ui/Field";
import { ErrorState, Loading } from "@/components/ui/States";
import { ApiError } from "@/lib/api";
import { errorMessage } from "@/lib/errors";
import { useApi } from "@/lib/use-api";
import { saveProfile, type Profile, type ProfileInput } from "./api";
import { ACTIVITY_LABELS, EXPERIENCE_LABELS, GOAL_LABELS, SEX_LABELS, options } from "./labels";

function latestAdultBirthDate(): string {
  const d = new Date();
  d.setFullYear(d.getFullYear() - 18);
  return d.toISOString().slice(0, 10);
}

function readForm(form: FormData): ProfileInput {
  const text = (key: string) => String(form.get(key) ?? "");
  return {
    display_name: text("display_name"),
    sex: text("sex") as ProfileInput["sex"],
    birth_date: text("birth_date"),
    height_cm: Number(text("height_cm")),
    weight_kg: Number(text("weight_kg")),
    activity_level: text("activity_level") as ProfileInput["activity_level"],
    goal: text("goal") as ProfileInput["goal"],
    training_days: Number(text("training_days")),
    experience: text("experience") as ProfileInput["experience"],
    equipment: "gym",
  };
}

export function ProfileForm() {
  const existing = useApi<Profile>("/profile");
  const isNew = existing.error instanceof ApiError && existing.error.status === 404;
  if (existing.loading) return <Loading />;
  if (existing.error && !isNew) return <ErrorState error={existing.error} onRetry={existing.reload} />;
  return <Form initial={existing.data} />;
}

function Form({ initial }: { initial?: Profile }) {
  const router = useRouter();
  const [error, setError] = useState<string>();
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(undefined);
    try {
      const saved = await saveProfile(readForm(new FormData(event.currentTarget)));
      router.push(saved.screening_status === null ? "/profil/screening" : "/azi");
    } catch (err) {
      setError(errorMessage(err));
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-5">
      <TextField
        label="Nume"
        name="display_name"
        required
        maxLength={50}
        defaultValue={initial?.display_name}
        autoComplete="given-name"
      />
      <ChoiceGroup
        legend="Sex biologic (pentru formula de calcul)"
        name="sex"
        options={options(SEX_LABELS)}
        defaultValue={initial?.sex}
        hint="Folosit doar în formula metabolică. Rezultatul este o estimare aproximativă."
      />
      <TextField
        label="Data nașterii"
        name="birth_date"
        type="date"
        required
        max={latestAdultBirthDate()}
        defaultValue={initial?.birth_date}
        hint="Aplicația este destinată exclusiv adulților (18+)."
      />
      <div className="grid grid-cols-2 gap-3">
        <TextField
          label="Înălțime (cm)"
          name="height_cm"
          type="number"
          inputMode="decimal"
          min={120}
          max={230}
          step={0.1}
          required
          defaultValue={initial?.height_cm}
        />
        <TextField
          label="Greutate (kg)"
          name="weight_kg"
          type="number"
          inputMode="decimal"
          min={30}
          max={300}
          step={0.1}
          required
          defaultValue={initial?.weight_kg}
        />
      </div>
      <SelectField
        label="Nivel de activitate"
        name="activity_level"
        options={options(ACTIVITY_LABELS)}
        defaultValue={initial?.activity_level ?? "moderate"}
      />
      <ChoiceGroup
        legend="Obiectiv"
        name="goal"
        options={options(GOAL_LABELS)}
        defaultValue={initial?.goal}
        columns={3}
      />
      <ChoiceGroup
        legend="Zile de antrenament pe săptămână"
        name="training_days"
        options={[2, 3, 4, 5, 6].map((n) => ({ value: String(n), label: String(n) }))}
        defaultValue={initial ? String(initial.training_days) : undefined}
        columns={3}
      />
      <ChoiceGroup
        legend="Experiență"
        name="experience"
        options={options(EXPERIENCE_LABELS)}
        defaultValue={initial?.experience}
        columns={3}
      />
      <p className="text-muted text-sm">Echipament: sală de fitness.</p>
      {error && (
        <p role="alert" className="text-danger font-semibold">
          {error}
        </p>
      )}
      <Button type="submit" loading={pending}>
        {initial ? "Salvează profilul" : "Continuă"}
      </Button>
    </form>
  );
}
