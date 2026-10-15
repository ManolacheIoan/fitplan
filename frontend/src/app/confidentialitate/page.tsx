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
      "Cont obișnuit: adresa de email și parola (stocată doar sub formă de hash).",
      "Cont de vizitator: nu cere email sau parolă; în rest folosește aceleași date ca un cont obișnuit (profil, jurnale).",
      "Profil: nume afișat, sex biologic (doar pentru formula metabolică), data nașterii, înălțime, greutate, nivel de activitate, obiectiv, zile de antrenament, experiență, tipul de program.",
      "Screening de siguranță: NU stocăm răspunsurile individuale. Păstrăm doar rezultatul (fără restricții / necesită sfatul unui specialist) și data.",
      "Jurnale: antrenamente (exerciții, greutăți, repetări, exerciții înlocuite), alimente consumate pe categorii de masă, greutatea corporală, alimente adăugate manual.",
      "Consimțământul: versiunea politicii acceptate și momentul acceptării.",
      "Sesiunea de autentificare: un identificator aleator într-un cookie; pe server păstrăm doar o amprentă (hash) a lui și data expirării.",
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
    "Cât timp păstrăm datele",
    [
      "Cont obișnuit: până când îți ștergi contul. Ștergerea este imediată și definitivă și include toate datele de mai sus.",
      "Sesiunea de autentificare expiră după 14 zile sau la deconectare.",
      "Cont de vizitator: când apeși „Ieși și șterge datele”, contul și toate datele lui sunt șterse imediat. Dacă nu ieși, sesiunea expiră după 7 zile de la creare, iar contul și datele sunt șterse la următoarea curățare automată, care rulează zilnic (de regulă în aproximativ o zi de la expirare).",
      "Textul unei căutări în Open Food Facts este ținut cel mult 24 de ore în memoria serverului, fără legătură cu contul tău, ca să nu trimitem aceeași căutare de mai multe ori.",
    ],
  ],
  [
    "Cui trimitem date (terți)",
    [
      "Open Food Facts (asociație non-profit, Franța; vezi politica lor de confidențialitate pe world.openfoodfacts.org/privacy): doar când apeși „Caută în Open Food Facts”. Trimitem textul căutat (de ex. „iaurt”). Cererea pleacă de pe serverul aplicației, deci Open Food Facts vede adresa IP a serverului și numele aplicației, nu adresa ta IP. Nu trimitem email, nume, identificatorul contului sau date de sănătate.",
      "Produsele găsite (denumire, valori nutriționale, cod de bare) sunt salvate în baza aplicației pentru căutări viitoare; ele nu conțin date despre tine.",
      "Furnizori de găzduire care prelucrează datele în numele nostru: Neon (baza de date) și Render (serverul aplicației), ambele în regiunea UE (Frankfurt), și Netlify (servește interfața web și redirecționează cererile către server). [DE COMPLETAT după verificarea juridică: contractele de prelucrare și eventualele transferuri în afara UE.]",
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
