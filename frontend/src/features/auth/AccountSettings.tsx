"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { TextField } from "@/components/ui/Field";
import { errorMessage } from "@/lib/errors";
import { changePassword, deleteAccount, exportData, logout } from "./api";
import { useMe } from "./AuthGuard";

function useAction() {
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string }>();
  async function run(action: () => Promise<unknown>, success?: string) {
    setPending(true);
    setMessage(undefined);
    try {
      await action();
      if (success) setMessage({ ok: true, text: success });
    } catch (err) {
      setMessage({ ok: false, text: errorMessage(err) });
    } finally {
      setPending(false);
    }
  }
  const feedback = message && (
    <p
      role={message.ok ? "status" : "alert"}
      className={`text-sm font-semibold ${message.ok ? "text-accent-text" : "text-danger"}`}
    >
      {message.text}
    </p>
  );
  return { pending, run, feedback };
}

function PasswordCard() {
  const { pending, run, feedback } = useAction();
  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formEl = event.currentTarget;
    const form = new FormData(formEl);
    void run(async () => {
      await changePassword(String(form.get("current")), String(form.get("new")));
      formEl.reset();
    }, "Parola a fost schimbată. Celelalte sesiuni au fost închise.");
  }
  return (
    <Card>
      <h2 className="mb-4 text-lg font-extrabold">Schimbă parola</h2>
      <form onSubmit={onSubmit} className="flex flex-col gap-4">
        <TextField
          label="Parola actuală"
          name="current"
          type="password"
          autoComplete="current-password"
          required
        />
        <TextField
          label="Parola nouă"
          name="new"
          type="password"
          autoComplete="new-password"
          required
          minLength={10}
          maxLength={128}
          hint="Minimum 10 caractere."
        />
        {feedback}
        <Button type="submit" variant="secondary" loading={pending}>
          Salvează parola
        </Button>
      </form>
    </Card>
  );
}

function DataCard() {
  const router = useRouter();
  const { pending, run, feedback } = useAction();

  const download = () =>
    run(async () => {
      const data = await exportData();
      const url = URL.createObjectURL(
        new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }),
      );
      const link = Object.assign(document.createElement("a"), { href: url, download: "fitplan-date.json" });
      link.click();
      URL.revokeObjectURL(url);
    });

  function onDelete(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const password = String(new FormData(event.currentTarget).get("password"));
    if (!window.confirm("Ștergi definitiv contul și toate datele? Acțiunea nu poate fi anulată.")) return;
    void run(async () => {
      await deleteAccount(password);
      router.replace("/");
    });
  }

  return (
    <Card>
      <h2 className="mb-2 text-lg font-extrabold">Datele mele</h2>
      <p className="text-muted mb-4 text-sm">
        Poți descărca toate datele tale (JSON) sau poți șterge definitiv contul.
      </p>
      <Button variant="secondary" className="w-full" onClick={download} disabled={pending}>
        Exportă datele (JSON)
      </Button>
      <form onSubmit={onDelete} className="border-border mt-6 flex flex-col gap-4 border-t pt-6">
        <TextField
          label="Confirmă cu parola pentru ștergere"
          name="password"
          type="password"
          autoComplete="current-password"
          required
        />
        <Button type="submit" variant="danger" loading={pending}>
          Șterge contul definitiv
        </Button>
      </form>
      <div className="mt-3">{feedback}</div>
    </Card>
  );
}

export function AccountSettings() {
  const me = useMe();
  const router = useRouter();
  const { pending, run } = useAction();
  return (
    <div className="flex flex-col gap-4">
      <Card className="flex flex-col gap-3">
        <p className="text-muted text-sm">
          Conectat ca <span className="text-fg font-semibold">{me.email}</span>
        </p>
        <Button
          variant="secondary"
          loading={pending}
          onClick={() =>
            run(async () => {
              await logout();
              router.replace("/autentificare");
            })
          }
        >
          Deconectare
        </Button>
      </Card>
      <PasswordCard />
      <DataCard />
    </div>
  );
}
