"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { Button } from "@/components/ui/Button";
import { Checkbox } from "@/components/ui/Field";
import { errorMessage } from "@/lib/errors";
import { giveConsent } from "./api";
import { useMe, useReloadMe } from "./AuthGuard";
import { ConsentText } from "./ConsentText";

export function ConsentForm() {
  const router = useRouter();
  const me = useMe();
  const reloadMe = useReloadMe();
  const [error, setError] = useState<string>();
  const [pending, setPending] = useState(false);

  useEffect(() => {
    if (!me.consent_required) router.replace("/azi");
  }, [me.consent_required, router]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    try {
      await giveConsent();
      reloadMe();
    } catch (err) {
      setError(errorMessage(err));
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4">
      <p className="text-muted">
        Politica de confidențialitate a fost actualizată (versiunea {me.policy_version}). Fără acordul tău nu
        putem prelucra datele necesare aplicației.
      </p>
      <Checkbox name="consent" required label={<ConsentText />} />
      {error && (
        <p role="alert" className="text-danger text-sm font-semibold">
          {error}
        </p>
      )}
      <Button type="submit" loading={pending}>
        Continuă
      </Button>
    </form>
  );
}
