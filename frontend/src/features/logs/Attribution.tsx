/** Credit required by the licence of external food data (Open Food Facts: ODbL). */
export function Attribution({ text }: { text: string | null }) {
  if (!text) return null;
  const isOff = text.startsWith("Open Food Facts");
  return (
    <span className="text-muted text-xs">
      Sursa:{" "}
      {isOff ? (
        <a href="https://world.openfoodfacts.org" target="_blank" rel="noreferrer" className="underline">
          {text}
        </a>
      ) : (
        text
      )}
    </span>
  );
}
