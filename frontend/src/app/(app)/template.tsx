// Re-mounted on every navigation, so each page enters with a short animation
// (disabled by prefers-reduced-motion in globals.css).
export default function AppTemplate({ children }: { children: React.ReactNode }) {
  return <div className="stagger flex flex-col gap-6">{children}</div>;
}
