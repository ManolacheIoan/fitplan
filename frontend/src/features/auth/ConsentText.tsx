import Link from "next/link";

/** Wording of the explicit consent for processing health-related data. */
export function ConsentText() {
  return (
    <>
      Sunt de acord ca FitPlan să prelucreze datele mele legate de sănătate (de ex. greutate, înălțime,
      vârstă, rezultatul screeningului de siguranță) pentru a-mi genera estimări și planuri, conform{" "}
      <Link href="/confidentialitate" className="text-accent-text font-semibold underline">
        Politicii de confidențialitate
      </Link>
      . Pot retrage acordul oricând ștergându-mi contul.
    </>
  );
}
