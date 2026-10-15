import type { Metadata } from "next";
import { ProfileForm } from "@/features/profile/ProfileForm";

export const metadata: Metadata = { title: "Profil" };

export default function QuestionnairePage() {
  return (
    <>
      <h1 className="text-3xl font-black uppercase">Despre tine</h1>
      <ProfileForm />
    </>
  );
}
