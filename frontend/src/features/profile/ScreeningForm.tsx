"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/Button";
import { ChoiceGroup } from "@/components/ui/Field";
import { ErrorState, Loading } from "@/components/ui/States";
import { errorMessage } from "@/lib/errors";
import { useApi } from "@/lib/use-api";
import { submitScreening, type Profile, type ScreeningAnswers } from "./api";

// Wording to be reviewed by a qualified professional together with the thresholds.
const QUESTIONS: { key: keyof ScreeningAnswers; text: string; femaleOnly?: boolean }[] = [
  { key: "pregnant_or_breastfeeding", text: "Ești însărcinată sau alăptezi?", femaleOnly: true },
  { key: "diagnosed_medical_condition", text: "Ai vreo afecțiune medicală diagnosticată?" },
  { key: "eating_disorder_history", text: "Ai avut vreodată o tulburare de alimentație?" },
  { key: "current_injury", text: "Ai în prezent o accidentare sau o durere care îți limitează mișcarea?" },
];

const YES_NO = [
  { value: "yes", label: "Da" },
  { value: "no", label: "Nu" },
];

export function ScreeningForm() {
  const profile = useApi<Profile>("/profile");
  if (profile.error) return <ErrorState error={profile.error} onRetry={profile.reload} />;
  if (!profile.data) return <Loading />;
  const questions = QUESTIONS.filter((q) => !q.femaleOnly || profile.data!.sex === "female");
  return <Form questions={questions} />;
}

function Form({ questions }: { questions: typeof QUESTIONS }) {
  const router = useRouter();
  const [error, setError] = useState<string>();
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const answers = Object.fromEntries(
      QUESTIONS.map(({ key }) => [key, form.get(key) === "yes"]),
    ) as ScreeningAnswers;
    setPending(true);
    try {
      const { status } = await submitScreening(answers);
      router.replace(status === "passed" ? "/azi" : "/recomandare");
    } catch (err) {
      setError(errorMessage(err));
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-5">
      <p className="text-muted">
        Câteva întrebări de siguranță. Răspunsurile nu sunt salvate: păstrăm doar rezultatul general.
      </p>
      {questions.map(({ key, text }) => (
        <ChoiceGroup key={key} legend={text} name={key} options={YES_NO} />
      ))}
      {error && (
        <p role="alert" className="text-danger font-semibold">
          {error}
        </p>
      )}
      <Button type="submit" loading={pending}>
        Trimite
      </Button>
    </form>
  );
}
