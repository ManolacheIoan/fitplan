"use client";

import { usePathname, useRouter } from "next/navigation";
import { createContext, useContext, useEffect, type ReactNode } from "react";
import { ErrorState, Loading } from "@/components/ui/States";
import { ApiError } from "@/lib/api";
import { useApi } from "@/lib/use-api";
import type { Me } from "./api";

const MeContext = createContext<{ me: Me; reload: () => void } | null>(null);

function useMeContext() {
  const ctx = useContext(MeContext);
  if (!ctx) throw new Error("useMe must be used inside <AuthGuard>");
  return ctx;
}

export const useMe = (): Me => useMeContext().me;
export const useReloadMe = (): (() => void) => useMeContext().reload;

/**
 * Redirects to login or to the consent page. This is a UX convenience only:
 * the API rejects every unauthorized request on its own.
 */
export function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { data: me, error, reload } = useApi<Me>("/auth/me");
  const unauthenticated = error instanceof ApiError && error.status === 401;
  const needsConsent = !!me?.consent_required && pathname !== "/consimtamant";

  useEffect(() => {
    if (unauthenticated) router.replace("/autentificare");
    else if (needsConsent) router.replace("/consimtamant");
  }, [unauthenticated, needsConsent, router]);

  if (error && !unauthenticated) return <ErrorState error={error} onRetry={reload} />;
  if (!me || needsConsent) return <Loading />;
  return <MeContext.Provider value={{ me, reload }}>{children}</MeContext.Provider>;
}
