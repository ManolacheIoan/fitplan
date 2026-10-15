"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/Button";
import { Checkbox, TextField } from "@/components/ui/Field";
import { errorMessage } from "@/lib/errors";
import { login, register } from "./api";
import { ConsentText } from "./ConsentText";

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const [error, setError] = useState<string>();
  const [pending, setPending] = useState(false);
  const isRegister = mode === "register";

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const email = String(form.get("email"));
    const password = String(form.get("password"));
    setPending(true);
    setError(undefined);
    try {
      if (isRegister) await register(email, password, form.get("consent") === "on");
      else await login(email, password);
      router.replace("/azi");
    } catch (err) {
      setError(errorMessage(err));
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4" noValidate={false}>
      <TextField label="Email" name="email" type="email" autoComplete="email" required maxLength={254} />
      <TextField
        label="Parolă"
        name="password"
        type="password"
        autoComplete={isRegister ? "new-password" : "current-password"}
        required
        minLength={isRegister ? 10 : 1}
        maxLength={128}
        hint={isRegister ? "Minimum 10 caractere." : undefined}
      />
      {isRegister && <Checkbox name="consent" required label={<ConsentText />} />}
      {error && (
        <p role="alert" className="text-danger text-sm font-semibold">
          {error}
        </p>
      )}
      <Button type="submit" loading={pending}>
        {isRegister ? "Creează cont" : "Intră în cont"}
      </Button>
      <p className="text-muted text-center text-sm">
        {isRegister ? "Ai deja cont? " : "Nu ai cont? "}
        <Link
          href={isRegister ? "/autentificare" : "/inregistrare"}
          className="text-accent-text font-semibold underline"
        >
          {isRegister ? "Autentifică-te" : "Înregistrează-te"}
        </Link>
      </p>
    </form>
  );
}
