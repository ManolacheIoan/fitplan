import type { Metadata } from "next";
import { Disclaimer } from "@/components/ui/Disclaimer";
import { Logo } from "@/components/Logo";
import { POLICY_VERSION } from "@/lib/policy";

export const metadata: Metadata = { title: "Politica de confidențialitate" };

// Describes what the application actually does. Operator identity, contact details and the
// legal review are placeholders the project owner must complete before public use.
const SECTIONS: [string, string[]][] = [
  [
    "Cine prelucrează datele",
    [
      "Operator: [DE COMPLETAT: nume / denumire, adresă]. Contact pentru protecția datelor: [DE COMPLETAT: email].",
    ],
  ],
  [
    "Ce date colectăm",
    [
      "Cont: adresa de email și parola (stocată doar sub formă de hash).",
      "Profil: nume afișat, sex biologic (doar pentru formula metabolică), data nașterii, înălțime, greutate, nivel de activitate, obiectiv, zile de antrenament, experiență.",
      "Screening de siguranță: NU stocăm răspunsurile individuale. Păstrăm doar rezultatul (fără restricții / necesită sfatul unui specialist) și data.",
      "Jurnale: antrenamente (exerciții, greutăți, repetări), alimente consumate și greutatea corporală.",
      "Consimțământul: versiunea politicii acceptate și momentul acceptării.",
    ],
  ],
  [
    "De ce și pe ce bază",
    [
      "Datele sunt folosite exclusiv pentru a-ți genera estimări nutriționale, planul de antrenament și graficele de progres.",
      "Datele legate de sănătate sunt prelucrate doar pe baza consimțământului tău explicit, pe care îl poți retrage oricând ștergându-ți contul.",
    ],
  ],
  [
    "Ce NU facem",
    [
      "Nu folosim trackere, analytics sau publicitate de la terți.",
      "Nu vindem și nu partajăm datele tale în scop comercial.",
      "Nu scriem datele de sănătate în jurnalele (logs) serverului.",
    ],
  ],
  [
    "Unde sunt stocate",
    [
      "Baza de date și serverul aplicației rulează în regiunea UE (Frankfurt). Interfața web este servită printr-o rețea de distribuție (CDN), prin care trec și cererile către server.",
    ],
  ],
  [
    "Drepturile tale",
    [
      "Poți descărca oricând toate datele tale (export JSON) din Setări.",
      "Poți șterge definitiv contul din Setări; toate datele asociate sunt șterse imediat.",
      "Pentru alte solicitări (rectificare, informații, plângeri) folosește adresa de contact de mai sus. Ai dreptul să depui o plângere la autoritatea de supraveghere (ANSPDCP).",
    ],
  ],
];

export default function PrivacyPage() {
  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-6 px-4 py-8">
      <Logo />
      <h1 className="text-3xl font-black uppercase">Politica de confidențialitate</h1>
      <p className="text-muted text-sm">Versiunea {POLICY_VERSION}</p>
      {SECTIONS.map(([title, items]) => (
        <section key={title}>
          <h2 className="mb-2 text-xl font-extrabold">{title}</h2>
          <ul className="text-muted list-disc space-y-1 pl-5">
            {items.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
      ))}
      <Disclaimer />
    </main>
  );
}
