import type { Metadata } from "next";
import Link from "next/link";
import { Card } from "@/components/ui/Card";

export const metadata: Metadata = { title: "Recomandare" };

// Deliberately generic: the page never names or hints at the answer that triggered it.
export default function RecommendationPage() {
  return (
    <>
      <h1 className="text-3xl font-black uppercase">Recomandare</h1>
      <Card className="flex flex-col gap-3">
        <p className="text-lg font-bold">
          Îți recomandăm să discuți mai întâi cu un medic sau cu un specialist acreditat.
        </p>
        <p className="text-muted">
          Pe baza răspunsurilor tale la screeningul de siguranță, FitPlan nu generează estimări de calorii sau
          macronutrienți, obiective de slăbire ori planuri de antrenament. Aceste calcule și planuri sunt
          generale și nu au fost validate pentru situația ta.
        </p>
        <p className="text-muted">
          Un medic (de exemplu medicul de familie), un dietetician autorizat sau un kinetoterapeut te poate
          ajuta să stabilești ce tip de alimentație și activitate fizică ți se potrivește.
        </p>
      </Card>
      <Card className="flex flex-col gap-3">
        <p className="text-muted">Dacă situația ta s-a schimbat, poți reface screeningul oricând.</p>
        <Link
          href="/profil/screening"
          className="border-border inline-flex min-h-12 items-center justify-center rounded-xl border font-bold"
        >
          Refă screeningul
        </Link>
        <Link href="/setari" className="text-muted text-center text-sm underline">
          Setări cont (export date, ștergere cont)
        </Link>
      </Card>
    </>
  );
}
