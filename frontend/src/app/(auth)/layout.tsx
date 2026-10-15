import { Logo } from "@/components/Logo";
import { WakeBanner } from "@/components/ui/WakeBanner";

export default function AuthLayout({ children }: LayoutProps<"/">) {
  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col gap-6 px-4 py-8">
      <WakeBanner />
      <Logo />
      {children}
    </main>
  );
}
