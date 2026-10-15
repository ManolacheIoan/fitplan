"use client";

import { useProfile } from "./ProfileGate";

export function Greeting() {
  const { profile } = useProfile();
  return <h1 className="text-3xl font-black uppercase">Salut, {profile.display_name}</h1>;
}
