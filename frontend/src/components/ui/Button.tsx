import type { ButtonHTMLAttributes } from "react";

const VARIANTS = {
  primary: "bg-accent text-accent-fg shadow-[0_6px_24px_-8px_var(--accent)] hover:brightness-105",
  secondary: "border border-border bg-surface-2 text-fg hover:border-muted",
  danger: "border border-danger text-danger hover:bg-danger/10",
  ghost: "text-fg hover:bg-surface-2",
} as const;

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: keyof typeof VARIANTS;
  loading?: boolean;
};

export function Button({ variant = "primary", loading, className = "", children, disabled, ...rest }: Props) {
  return (
    <button
      className={`inline-flex min-h-12 items-center justify-center gap-2 rounded-xl px-5 font-bold transition duration-150 active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-50 disabled:active:scale-100 ${VARIANTS[variant]} ${className}`}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...rest}
    >
      {loading && (
        <span
          className="size-4 animate-spin rounded-full border-2 border-current border-t-transparent"
          aria-hidden
        />
      )}
      {children}
    </button>
  );
}
