import { useId, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes } from "react";

type Common = { label: string; hint?: ReactNode; error?: string };

const control =
  "min-h-12 w-full rounded-xl border border-border bg-surface-2 px-4 text-base text-fg placeholder:text-muted aria-[invalid=true]:border-danger";

function Wrapper({ id, label, hint, error, children }: Common & { id: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-semibold">
        {label}
      </label>
      {children}
      {hint && (
        <p id={`${id}-hint`} className="text-muted text-sm">
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-error`} className="text-danger text-sm" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

function describedBy(id: string, { hint, error }: Common) {
  return [hint && `${id}-hint`, error && `${id}-error`].filter(Boolean).join(" ") || undefined;
}

export function TextField({ label, hint, error, ...rest }: Common & InputHTMLAttributes<HTMLInputElement>) {
  const id = useId();
  return (
    <Wrapper id={id} label={label} hint={hint} error={error}>
      <input
        id={id}
        className={control}
        aria-invalid={!!error}
        aria-describedby={describedBy(id, { label, hint, error })}
        {...rest}
      />
    </Wrapper>
  );
}

export function SelectField({
  label,
  hint,
  error,
  options,
  ...rest
}: Common & SelectHTMLAttributes<HTMLSelectElement> & { options: { value: string; label: string }[] }) {
  const id = useId();
  return (
    <Wrapper id={id} label={label} hint={hint} error={error}>
      <select
        id={id}
        className={control}
        aria-invalid={!!error}
        aria-describedby={describedBy(id, { label, hint, error })}
        {...rest}
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </Wrapper>
  );
}

export function Checkbox({ label, ...rest }: { label: ReactNode } & InputHTMLAttributes<HTMLInputElement>) {
  const id = useId();
  return (
    <div className="flex items-start gap-3">
      <input id={id} type="checkbox" className="mt-1 size-6 shrink-0 accent-[var(--accent)]" {...rest} />
      <label htmlFor={id} className="text-sm leading-relaxed">
        {label}
      </label>
    </div>
  );
}

/** Thumb-friendly radio group rendered as large tappable options. */
export function ChoiceGroup({
  legend,
  name,
  options,
  defaultValue,
  value,
  onValueChange,
  hint,
  columns = 2,
}: {
  legend: string;
  name: string;
  options: { value: string; label: string; description?: string }[];
  defaultValue?: string;
  /** Controlled mode: pass `value` and `onValueChange` together. */
  value?: string;
  onValueChange?: (value: string) => void;
  hint?: ReactNode;
  columns?: 1 | 2 | 3;
}) {
  const cols = { 1: "grid-cols-1", 2: "grid-cols-2", 3: "grid-cols-3" }[columns];
  return (
    <fieldset className="flex flex-col gap-1.5">
      <legend className="mb-1.5 text-sm font-semibold">{legend}</legend>
      <div className={`grid gap-2 ${cols}`}>
        {options.map((o) => (
          <label
            key={o.value}
            className="has-checked:border-accent has-checked:bg-accent has-checked:text-accent-fg has-focus-visible:outline-accent-text border-border bg-surface-2 flex min-h-12 cursor-pointer items-center justify-center rounded-xl border px-3 text-center text-sm font-bold has-focus-visible:outline-3 has-focus-visible:outline-offset-2"
          >
            <input
              type="radio"
              name={name}
              value={o.value}
              {...(value === undefined
                ? { defaultChecked: o.value === defaultValue }
                : { checked: o.value === value, onChange: () => onValueChange?.(o.value) })}
              required
              className="sr-only"
            />
            <span>
              <span className="block">{o.label}</span>
              {o.description && <span className="block text-xs font-medium opacity-80">{o.description}</span>}
            </span>
          </label>
        ))}
      </div>
      {hint && <p className="text-muted text-sm">{hint}</p>}
    </fieldset>
  );
}
