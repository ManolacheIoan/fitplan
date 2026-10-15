export const DISCLAIMER =
  "Informațiile sunt orientative și nu înlocuiesc sfatul unui medic sau al unui specialist acreditat. Consultă un medic înainte de a schimba dieta sau antrenamentul.";

export function Disclaimer({ className = "" }: { className?: string }) {
  return (
    <p className={`border-warning/40 bg-warning/10 text-fg rounded-xl border p-3 text-sm ${className}`}>
      <strong className="text-warning">Important: </strong>
      {DISCLAIMER}
    </p>
  );
}
