import type { Metadata } from "next";
import { ConsentForm } from "@/features/auth/ConsentForm";

export const metadata: Metadata = { title: "Consimțământ" };

export default function ConsentPage() {
  return (
    <>
      <h1 className="text-3xl font-black uppercase">Consimțământ</h1>
      <ConsentForm />
    </>
  );
}
