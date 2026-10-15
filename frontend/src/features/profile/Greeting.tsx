"use client";

import { formatDay, todayLocal } from "@/lib/dates";
import { useProfile } from "./ProfileGate";

export function Greeting() {
  const { profile } = useProfile();
  return (
    <header>
      <p className="text-muted text-sm font-semibold capitalize">{formatDay(todayLocal())}</p>
      <h1 className="text-4xl font-black uppercase">
        Salut, <span className="text-gradient">{profile.display_name}</span>
      </h1>
    </header>
  );
}
