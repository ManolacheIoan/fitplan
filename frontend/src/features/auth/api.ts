import { api, json } from "@/lib/api";

export type Me = {
  email: string | null;
  is_guest: boolean;
  created_at: string;
  consent_required: boolean;
  policy_version: string;
};

export const register = (email: string, password: string, consent: boolean) =>
  api<Me>("/auth/register", { method: "POST", ...json({ email, password, consent }) });

export const login = (email: string, password: string) =>
  api<Me>("/auth/login", { method: "POST", ...json({ email, password }) });

export const continueAsGuest = () => api<Me>("/auth/guest", { method: "POST", ...json({ consent: true }) });

export const logout = () => api<void>("/auth/logout", { method: "POST" });

export const giveConsent = () => api<void>("/auth/consent", { method: "POST", ...json({ accepted: true }) });

export const changePassword = (current_password: string, new_password: string) =>
  api<void>("/auth/password", { method: "POST", ...json({ current_password, new_password }) });

export const exportData = () => api<unknown>("/account/export");

export const deleteAccount = (password?: string) =>
  api<void>("/account", { method: "DELETE", ...json({ password }) });
