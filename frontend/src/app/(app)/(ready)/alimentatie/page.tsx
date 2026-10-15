import type { Metadata } from "next";
import { FoodLog } from "@/features/logs/FoodLog";

export const metadata: Metadata = { title: "Alimentație" };

export default function FoodPage() {
  return (
    <>
      <h1 className="text-3xl font-black uppercase">Alimentație</h1>
      <FoodLog />
    </>
  );
}
