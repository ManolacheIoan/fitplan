import { AppNav } from "@/components/AppNav";
import { Disclaimer } from "@/components/ui/Disclaimer";
import { WakeBanner } from "@/components/ui/WakeBanner";
import { AuthGuard } from "@/features/auth/AuthGuard";

export default function AppLayout({ children }: LayoutProps<"/">) {
  return (
    <>
      <WakeBanner />
      <main className="mx-auto flex w-full max-w-xl flex-1 flex-col gap-6 px-4 pt-6 pb-28">
        <AuthGuard>{children}</AuthGuard>
        <Disclaimer className="mt-auto" />
      </main>
      <AppNav />
    </>
  );
}
