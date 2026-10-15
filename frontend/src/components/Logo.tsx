import Link from "next/link";

export function Logo() {
  return (
    <Link href="/" className="text-2xl font-black tracking-tight uppercase italic">
      Fit<span className="text-accent-text">Plan</span>
    </Link>
  );
}
