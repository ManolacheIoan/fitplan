"use client";

import { useRouter } from "next/navigation";
import { createContext, useContext, useEffect, type ReactNode } from "react";
import { ErrorState, Loading } from "@/components/ui/States";
import { ApiError } from "@/lib/api";
import { useApi } from "@/lib/use-api";
import type { Profile } from "./api";

const ProfileContext = createContext<{ profile: Profile; reload: () => void } | null>(null);

export function useProfile() {
  const ctx = useContext(ProfileContext);
  if (!ctx) throw new Error("useProfile must be used inside <ProfileGate>");
  return ctx;
}

function redirectFor(profile: Profile | undefined, error: unknown): string | null {
  if (error instanceof ApiError && error.status === 404) return "/profil/chestionar";
  if (!profile) return null;
  if (profile.screening_status === null) return "/profil/screening";
  if (profile.screening_status === "refer") return "/recomandare";
  return null;
}

/** Sends the user through onboarding first. UX only: the API enforces the same rules. */
export function ProfileGate({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { data: profile, error, reload } = useApi<Profile>("/profile");
  const target = redirectFor(profile, error);

  useEffect(() => {
    if (target) router.replace(target);
  }, [target, router]);

  if (error && !target) return <ErrorState error={error} onRetry={reload} />;
  if (!profile || target) return <Loading />;
  return <ProfileContext.Provider value={{ profile, reload }}>{children}</ProfileContext.Provider>;
}
