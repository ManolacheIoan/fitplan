import type { Metadata } from "next";
import { AuthForm } from "@/features/auth/AuthForm";

export const metadata: Metadata = { title: "Înregistrare" };

export default function RegisterPage() {
  return (
    <>
      <h1 className="text-3xl font-black uppercase">Cont nou</h1>
      <p className="text-muted">Aplicația este destinată exclusiv adulților (18+).</p>
      <AuthForm mode="register" />
    </>
  );
}
