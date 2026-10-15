import Link from "next/link";
import { Disclaimer } from "@/components/ui/Disclaimer";
import { Logo } from "@/components/Logo";

const FEATURES = [
  ["Plan de sală", "Generat după zilele disponibile, obiectiv și experiență."],
  ["Estimări nutriționale", "Calorii și macronutrienți calculați prin formule standard, orientativ."],
  ["Jurnal", "Antrenamente, alimentație și greutate, cu grafice de progres."],
  ["Siguranță", "Screening inițial: dacă e cazul, te îndrumăm către un specialist."],
];

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-xl flex-1 flex-col gap-8 px-4 py-8">
      <Logo />
      <section className="animate-fade-up">
        <h1 className="text-4xl leading-none font-black tracking-tight uppercase sm:text-5xl">
          <span className="whitespace-nowrap">Antrenează-te</span>{" "}
          <span className="text-accent-text">cu un plan.</span>
        </h1>
        <p className="text-muted mt-4 text-lg">
          Antrenor personal digital pentru adulți care vor să slăbească, să își mențină greutatea sau să
          câștige masă musculară.
        </p>
        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <Link
            href="/inregistrare"
            className="bg-accent text-accent-fg inline-flex min-h-12 flex-1 items-center justify-center rounded-xl px-5 font-bold"
          >
            Începe gratuit
          </Link>
          <Link
            href="/autentificare"
            className="border-border inline-flex min-h-12 flex-1 items-center justify-center rounded-xl border px-5 font-bold"
          >
            Am deja cont
          </Link>
        </div>
      </section>
      <ul className="grid gap-3">
        {FEATURES.map(([title, text]) => (
          <li key={title} className="border-border bg-surface rounded-2xl border p-5">
            <p className="font-extrabold">{title}</p>
            <p className="text-muted text-sm">{text}</p>
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
