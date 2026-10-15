"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ComponentType, SVGProps } from "react";
import { ChartIcon, DumbbellIcon, ForkIcon, GearIcon, HomeIcon } from "./Icons";

const ITEMS: { href: string; label: string; Icon: ComponentType<SVGProps<SVGSVGElement>> }[] = [
  { href: "/azi", label: "Azi", Icon: HomeIcon },
  { href: "/plan", label: "Plan", Icon: DumbbellIcon },
  { href: "/alimentatie", label: "Mâncare", Icon: ForkIcon },
  { href: "/progres", label: "Progres", Icon: ChartIcon },
  { href: "/setari", label: "Setări", Icon: GearIcon },
];

export function AppNav() {
  const pathname = usePathname();
  return (
    <nav
      aria-label="Navigare principală"
      className="border-border bg-surface/90 fixed inset-x-0 bottom-0 z-40 border-t pb-[env(safe-area-inset-bottom)] backdrop-blur-md"
    >
      <ul className="mx-auto flex max-w-xl">
        {ITEMS.map(({ href, label, Icon }) => {
          const active = pathname.startsWith(href);
          return (
            <li key={href} className="flex-1">
              <Link
                href={href}
                aria-current={active ? "page" : undefined}
                className={`group flex min-h-16 flex-col items-center justify-center gap-1 text-xs font-bold transition-colors ${active ? "text-accent-text" : "text-muted hover:text-fg"}`}
              >
                <span
                  className={`flex h-8 w-14 items-center justify-center rounded-full transition-all duration-300 ${active ? "bg-accent/15 scale-100" : "scale-90 group-active:scale-95"}`}
                >
                  <Icon width={22} height={22} />
                </span>
                {label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
