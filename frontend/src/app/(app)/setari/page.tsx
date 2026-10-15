import type { Metadata } from "next";
import Link from "next/link";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Card } from "@/components/ui/Card";
import { AccountSettings } from "@/features/auth/AccountSettings";

export const metadata: Metadata = { title: "Setări" };

const linkButton =
  "inline-flex min-h-12 items-center justify-center rounded-xl border border-border bg-surface-2 font-bold";

export default function SettingsPage() {
  return (
    <>
      <h1 className="text-3xl font-black uppercase">Setări</h1>
      <Card>
        <ThemeToggle />
      </Card>
      <Card className="flex flex-col gap-3">
        <h2 className="text-lg font-extrabold">Profil</h2>
        <Link href="/profil/chestionar" className={linkButton}>
          Editează profilul
        </Link>
        <Link href="/profil/screening" className={linkButton}>
          Refă screeningul de siguranță
        </Link>
      </Card>
      <AccountSettings />
      <Link href="/confidentialitate" className="text-muted text-sm underline">
        Politica de confidențialitate
      </Link>
    </>
  );
}
