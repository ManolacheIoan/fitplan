"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/Button";
import { Checkbox } from "@/components/ui/Field";
import { errorMessage } from "@/lib/errors";
import { continueAsGuest } from "./api";
import { ConsentText } from "./ConsentText";

// Must match GUEST_TTL_DAYS in backend/app/auth/service.py.
export const GUEST_DAYS = 7;

/** "Continue as guest": a temporary account without email or password. */
export function GuestButton() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string>();

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(undefined);
    try {
      await continueAsGuest();
      router.replace("/azi");
    } catch (err) {
      setError(errorMessage(err));
      setPending(false);
    }
  }

  if (!open) {
    return (
      <Button variant="ghost" className="w-full" onClick={() => setOpen(true)}>
        Continuă ca vizitator
      </Button>
    );
  }
  return (
    <form
      onSubmit={onSubmit}
      className="animate-fade-up border-border flex flex-col gap-3 rounded-2xl border p-4"
    >
      <p className="text-sm">
        <span className="font-bold">Fără email și parolă.</span>{" "}
        <span className="text-muted">
          Datele se șterg definitiv când ieși. Dacă nu ieși, contul expiră după {GUEST_DAYS} zile și e șters
          la curățarea automată următoare. Datele nu pot fi mutate într-un cont.
        </span>
      </p>
      <Checkbox name="consent" required label={<ConsentText />} />
      {error && (
        <p role="alert" className="text-danger text-sm font-semibold">
          {error}
        </p>
      )}
      <Button type="submit" variant="secondary" loading={pending}>
        Intră ca vizitator
      </Button>
    </form>
  );
}
