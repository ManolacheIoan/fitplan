"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const ITEMS = [
  { href: "/azi", label: "Azi" },
  { href: "/plan", label: "Plan" },
  { href: "/alimentatie", label: "Mâncare" },
  { href: "/progres", label: "Progres" },
  { href: "/setari", label: "Setări" },
];

export function AppNav() {
  const pathname = usePathname();
  return (
    <nav
      aria-label="Navigare principală"
      className="border-border bg-surface/95 fixed inset-x-0 bottom-0 z-40 border-t pb-[env(safe-area-inset-bottom)] backdrop-blur"
    >
      <ul className="mx-auto flex max-w-xl">
        {ITEMS.map(({ href, label }) => {
          const active = pathname.startsWith(href);
          return (
            <li key={href} className="flex-1">
              <Link
                href={href}
                aria-current={active ? "page" : undefined}
                className={`flex min-h-14 items-center justify-center text-sm font-bold ${active ? "text-accent-text" : "text-muted"}`}
              >
                {label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
