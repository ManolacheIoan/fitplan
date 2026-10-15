import type { Metadata } from "next";
import { AuthForm } from "@/features/auth/AuthForm";
import { GuestButton } from "@/features/auth/GuestButton";

export const metadata: Metadata = { title: "Autentificare" };

export default function LoginPage() {
  return (
    <>
      <h1 className="text-3xl font-black uppercase">Autentificare</h1>
      <AuthForm mode="login" />
      <GuestButton />
    </>
  );
}
