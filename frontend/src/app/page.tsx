import Link from "next/link";
import type { ComponentType, SVGProps } from "react";
import { BoltIcon, ChartIcon, DumbbellIcon, ShieldIcon } from "@/components/Icons";
import { Logo } from "@/components/Logo";
import { Disclaimer } from "@/components/ui/Disclaimer";
import { GuestButton } from "@/features/auth/GuestButton";

const FEATURES: [ComponentType<SVGProps<SVGSVGElement>>, string, string][] = [
  [DumbbellIcon, "Plan de sală", "Full Body, Upper/Lower, PPL sau Bro Split, exact pe zilele tale."],
  [
    BoltIcon,
    "Estimări nutriționale",
    "Calorii și macronutrienți calculați prin formule standard, orientativ.",
  ],
  [ChartIcon, "Progres vizibil", "Antrenamente, alimentație și greutate, cu grafice clare."],
  [ShieldIcon, "Siguranță", "Screening inițial: dacă e cazul, te îndrumăm către un specialist."],
];

export default function Home() {
  return (
    <main className="stagger mx-auto flex w-full max-w-xl flex-1 flex-col gap-8 px-4 py-8">
      <Logo />
      <section className="hero-glow">
        <p className="text-accent-text mb-3 text-sm font-bold tracking-widest uppercase">
          Antrenor personal digital
        </p>
        <h1 className="text-[min(9.5vw,3.75rem)] leading-[0.95] font-black tracking-tight uppercase">
          <span className="whitespace-nowrap">Antrenează-te</span>{" "}
          <span className="text-gradient">cu un plan.</span>
        </h1>
        <p className="text-muted mt-4 text-lg">
          Pentru adulți care vor să slăbească, să își mențină greutatea sau să câștige masă musculară.
        </p>
        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <Link
            href="/inregistrare"
            className="bg-accent text-accent-fg inline-flex min-h-14 flex-1 items-center justify-center rounded-xl px-5 text-lg font-bold shadow-[0_8px_30px_-10px_var(--accent)] transition active:scale-[0.97]"
          >
            Începe gratuit
          </Link>
          <Link
            href="/autentificare"
            className="border-border inline-flex min-h-14 flex-1 items-center justify-center rounded-xl border px-5 font-bold transition active:scale-[0.97]"
          >
            Am deja cont
          </Link>
        </div>
        <div className="mt-3">
          <GuestButton />
        </div>
      </section>
      <ul className="stagger grid gap-3 sm:grid-cols-2">
        {FEATURES.map(([Icon, title, text]) => (
          <li key={title} className="border-border bg-surface flex gap-4 rounded-2xl border p-5">
            <span className="bg-accent/15 text-accent-text flex size-11 shrink-0 items-center justify-center rounded-xl">
              <Icon />
            </span>
            <span>
              <span className="block font-extrabold">{title}</span>
              <span className="text-muted text-sm">{text}</span>
            </span>
          </li>
        ))}
      </ul>
      <Disclaimer />
      <footer className="text-muted pb-4 text-sm">
        <Link href="/confidentialitate" className="underline">
          Politica de confidențialitate
        </Link>
      </footer>
    </main>
  );
}
