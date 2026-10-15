/** Today's date in the user's local time zone, as YYYY-MM-DD. */
export function todayLocal(): string {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60_000;
  return new Date(now.getTime() - offset).toISOString().slice(0, 10);
}

export const formatDay = (isoDate: string) =>
  new Date(`${isoDate}T12:00:00`).toLocaleDateString("ro-RO", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });

export const formatDateTime = (iso: string) =>
  new Date(iso).toLocaleString("ro-RO", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });

export const nf1 = new Intl.NumberFormat("ro-RO", { maximumFractionDigits: 1 });
