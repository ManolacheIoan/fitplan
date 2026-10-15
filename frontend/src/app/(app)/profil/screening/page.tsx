import type { Metadata } from "next";
import { ScreeningForm } from "@/features/profile/ScreeningForm";

export const metadata: Metadata = { title: "Screening de siguranță" };

export default function ScreeningPage() {
  return (
    <>
      <h1 className="text-3xl font-black uppercase">Siguranță</h1>
      <ScreeningForm />
    </>
  );
}
