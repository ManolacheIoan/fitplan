import { ProfileGate } from "@/features/profile/ProfileGate";

export default function ReadyLayout({ children }: LayoutProps<"/">) {
  return <ProfileGate>{children}</ProfileGate>;
}
