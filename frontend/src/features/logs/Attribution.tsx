const OFF_URL = "https://world.openfoodfacts.org";
const ODBL_URL = "https://opendatacommons.org/licenses/odbl/1-0/";

/** Open Food Facts credit, linking both the source and the licence (ODbL 1.0, section 4.3). */
export function OffNotice({ prefix = "Sursa:" }: { prefix?: string }) {
  return (
    <>
      {prefix}{" "}
      <a href={OFF_URL} target="_blank" rel="noreferrer" className="underline">
        Open Food Facts
      </a>
      , date disponibile sub licența{" "}
      <a href={ODBL_URL} target="_blank" rel="noreferrer" className="underline">
        ODbL
      </a>
    </>
  );
}

/** Credit required by the licence of external food data, shown wherever such data is shown. */
export function Attribution({ text }: { text: string | null }) {
  if (!text) return null;
  return (
    <span className="text-muted text-xs">
      {text.startsWith("Open Food Facts") ? <OffNotice /> : `Sursa: ${text}`}
    </span>
  );
}
