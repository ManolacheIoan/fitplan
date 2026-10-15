import type { HTMLAttributes } from "react";

export function Card({ className = "", ...rest }: HTMLAttributes<HTMLDivElement>) {
  return <div className={`border-border bg-surface rounded-2xl border p-5 ${className}`} {...rest} />;
}
